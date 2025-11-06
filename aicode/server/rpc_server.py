"""
JSON-RPC Server - VSCode 扩展通信后端

使用 stdio 进行 JSON-RPC 通信，遵循 LSP 协议风格
"""
import json
import sys
from typing import Dict, Any, Optional, Callable
from aicode.config.config_manager import ConfigManager
from aicode.database.db_manager import DatabaseManager
from aicode.llm.client import LLMClient
from aicode.llm.session import SessionManager
from aicode.llm.code_edit import CodeEditParser, create_inline_edit_prompt
from aicode.config.constants import DEFAULT_DB_PATH
from aicode.llm.exceptions import ModelNotFoundError, APIError, ConfigError
from aicode.utils.logger import get_logger

logger = get_logger(__name__)


class RPCServer:
    """JSON-RPC Server"""

    def __init__(self):
        """初始化 RPC Server"""
        self.config_manager = ConfigManager()
        self.db_manager = DatabaseManager(DEFAULT_DB_PATH)
        self.session_manager = SessionManager()

        self.current_session = None
        self.current_model = None
        self.client = None

        # RPC 方法注册表
        self.methods: Dict[str, Callable] = {
            'initialize': self.initialize,
            'chat': self.chat,
            'getModels': self.get_models,
            'setModel': self.set_model,
            'getConfig': self.get_config,
            'setConfig': self.set_config,
            'clearHistory': self.clear_history,
            'getHistory': self.get_history,
            'applyEdit': self.apply_edit,
            'shutdown': self.shutdown,
        }

        logger.info("RPC Server initialized")

    def initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        初始化服务器

        Args:
            params: 初始化参数

        Returns:
            Dict: 服务器能力信息
        """
        try:
            # 加载配置
            if self.config_manager.config_exists():
                self.config_manager.load()

            # 加载默认模型
            model_name = params.get('model') or self.config_manager.get('global.default_model')
            if model_name:
                self._setup_model(model_name)

            logger.info("Server initialized successfully")
            return {
                'success': True,
                'capabilities': {
                    'chat': True,
                    'models': True,
                    'config': True,
                    'history': True,
                }
            }
        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            return {'success': False, 'error': str(e)}

    def _setup_model(self, model_name: str) -> bool:
        """设置当前模型"""
        try:
            self.current_model = self.db_manager.get_model(model_name)

            # 获取 API 配置
            api_key = self.config_manager.get('global.api_key') or self.current_model.api_key
            api_url = self.config_manager.get('global.api_url') or self.current_model.api_url

            if not api_key:
                raise ConfigError("API key not configured")

            # 创建客户端
            self.client = LLMClient(self.current_model, api_key=api_key, api_url=api_url)

            # 创建新会话
            self.current_session = self.session_manager.create_session(model_name)

            logger.info(f"Model set to: {model_name}")
            return True

        except ModelNotFoundError as e:
            logger.error(f"Model not found: {e}")
            raise
        except ConfigError as e:
            logger.error(f"Config error: {e}")
            raise

    def chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送聊天消息

        Args:
            params: {
                'message': str,  # 用户消息
                'context': Optional[List[str]],  # 文件上下文
                'temperature': Optional[float],  # 温度参数
            }

        Returns:
            Dict: 响应结果
        """
        try:
            if not self.client or not self.current_model:
                return {'success': False, 'error': 'No model selected'}

            message = params.get('message')
            if not message:
                return {'success': False, 'error': 'Message is required'}

            context = params.get('context', [])
            temperature = params.get('temperature', 0.7)

            # 构建消息
            user_message = message
            if context:
                context_text = '\n\n'.join([
                    f"File: {ctx['path']}\n```\n{ctx['content']}\n```"
                    for ctx in context
                ])
                user_message = f"{context_text}\n\n{message}"

            # 添加到会话
            self.current_session.add_message('user', user_message)

            # 构建消息列表（包含系统提示）
            messages = self.current_session.get_messages_for_api()

            # 如果是第一条消息，添加系统提示
            if len(messages) == 1:
                system_prompt = create_inline_edit_prompt()
                messages.insert(0, {
                    'role': 'system',
                    'content': system_prompt
                })

            # 发送请求
            response = self.client.chat(messages, temperature=temperature)

            # 解析代码编辑建议
            edits = CodeEditParser.parse(response)

            # 保存响应
            self.current_session.add_message('assistant', response)
            self.session_manager.save_session(self.current_session)

            # 计算 token 和成本
            token_count = self.client.count_message_tokens(messages)
            cost = self.client.estimate_cost(messages)

            logger.info(f"Chat response generated, tokens: {token_count}, edits: {len(edits)}")

            result = {
                'success': True,
                'response': response,
                'tokens': token_count,
                'cost': cost,
                'session_id': self.current_session.session_id
            }

            # 如果有代码编辑，添加到返回结果
            if edits:
                result['edits'] = [edit.to_dict() for edit in edits]
                result['edits_summary'] = CodeEditParser.format_edits_for_display(edits)

            return result

        except APIError as e:
            logger.error(f"API error: {e}")
            return {'success': False, 'error': f'API error: {str(e)}'}
        except Exception as e:
            logger.exception("Chat error")
            return {'success': False, 'error': str(e)}

    def get_models(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """获取可用模型列表"""
        try:
            models = self.db_manager.list_models()
            return {
                'success': True,
                'models': [
                    {
                        'name': m.name,
                        'provider': m.provider,
                        'code_score': m.code_score,
                        'max_input_tokens': m.max_input_tokens,
                        'max_output_tokens': m.max_output_tokens,
                    }
                    for m in models
                ]
            }
        except Exception as e:
            logger.error(f"Failed to get models: {e}")
            return {'success': False, 'error': str(e)}

    def set_model(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """切换模型"""
        try:
            model_name = params.get('model')
            if not model_name:
                return {'success': False, 'error': 'Model name is required'}

            self._setup_model(model_name)
            return {
                'success': True,
                'model': model_name,
                'session_id': self.current_session.session_id
            }
        except ModelNotFoundError:
            return {'success': False, 'error': f"Model '{model_name}' not found"}
        except Exception as e:
            logger.error(f"Failed to set model: {e}")
            return {'success': False, 'error': str(e)}

    def get_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """获取配置"""
        try:
            key = params.get('key')
            if key:
                value = self.config_manager.get(key)
                return {'success': True, 'value': value}
            else:
                # 返回所有配置
                return {'success': True, 'config': self.config_manager.config}
        except Exception as e:
            logger.error(f"Failed to get config: {e}")
            return {'success': False, 'error': str(e)}

    def set_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """设置配置"""
        try:
            key = params.get('key')
            value = params.get('value')

            if not key:
                return {'success': False, 'error': 'Key is required'}

            self.config_manager.set(key, value)
            self.config_manager.save()

            return {'success': True}
        except Exception as e:
            logger.error(f"Failed to set config: {e}")
            return {'success': False, 'error': str(e)}

    def clear_history(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """清除对话历史"""
        try:
            if self.current_session:
                self.current_session.messages.clear()
                self.session_manager.save_session(self.current_session)

            return {'success': True}
        except Exception as e:
            logger.error(f"Failed to clear history: {e}")
            return {'success': False, 'error': str(e)}

    def get_history(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """获取对话历史"""
        try:
            if not self.current_session:
                return {'success': True, 'messages': []}

            return {
                'success': True,
                'messages': self.current_session.messages,
                'session_id': self.current_session.session_id
            }
        except Exception as e:
            logger.error(f"Failed to get history: {e}")
            return {'success': False, 'error': str(e)}

    def apply_edit(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        应用代码编辑（由 VSCode 端调用，此方法仅验证）

        Args:
            params: {
                'file_path': str,  # 文件路径
                'new_content': str,  # 新内容
                'edit_type': str,  # modify/create/delete
            }

        Returns:
            Dict: 应用结果
        """
        try:
            file_path = params.get('file_path')
            new_content = params.get('new_content', '')
            edit_type = params.get('edit_type', 'modify')

            if not file_path:
                return {'success': False, 'error': 'file_path is required'}

            # 注意：实际的文件写入由 VSCode 扩展完成
            # 这里只返回验证结果
            logger.info(f"Edit validated for {file_path} ({edit_type})")

            return {
                'success': True,
                'file_path': file_path,
                'edit_type': edit_type
            }

        except Exception as e:
            logger.error(f"Failed to apply edit: {e}")
            return {'success': False, 'error': str(e)}

    def shutdown(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """关闭服务器"""
        logger.info("Server shutting down")
        return {'success': True}

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理 JSON-RPC 请求

        Args:
            request: JSON-RPC 请求

        Returns:
            Dict: JSON-RPC 响应
        """
        method = request.get('method')
        params = request.get('params', {})
        request_id = request.get('id')

        if method not in self.methods:
            return {
                'jsonrpc': '2.0',
                'id': request_id,
                'error': {
                    'code': -32601,
                    'message': f'Method not found: {method}'
                }
            }

        try:
            result = self.methods[method](params)
            return {
                'jsonrpc': '2.0',
                'id': request_id,
                'result': result
            }
        except Exception as e:
            logger.exception(f"Error handling method {method}")
            return {
                'jsonrpc': '2.0',
                'id': request_id,
                'error': {
                    'code': -32603,
                    'message': str(e)
                }
            }

    def run(self):
        """运行服务器（stdio 模式）"""
        logger.info("RPC Server starting in stdio mode")

        try:
            while True:
                # 读取请求（一行一个 JSON）
                line = sys.stdin.readline()
                if not line:
                    break

                try:
                    request = json.loads(line)
                    logger.debug(f"Received request: {request.get('method')}")

                    response = self.handle_request(request)

                    # 发送响应
                    sys.stdout.write(json.dumps(response) + '\n')
                    sys.stdout.flush()

                    logger.debug(f"Sent response for: {request.get('method')}")

                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON: {e}")
                    error_response = {
                        'jsonrpc': '2.0',
                        'id': None,
                        'error': {
                            'code': -32700,
                            'message': 'Parse error'
                        }
                    }
                    sys.stdout.write(json.dumps(error_response) + '\n')
                    sys.stdout.flush()

        except KeyboardInterrupt:
            logger.info("Server interrupted")
        except Exception as e:
            logger.exception("Server error")
        finally:
            logger.info("Server stopped")


def main():
    """启动 RPC Server"""
    server = RPCServer()
    server.run()


if __name__ == '__main__':
    main()
