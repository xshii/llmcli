"""
数据模型定义
"""
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
from aicode.config.constants import MIN_SCORE, MAX_SCORE, TOKEN_BUFFER_RATIO


# SQLite 表结构
CREATE_MODELS_TABLE = """
CREATE TABLE IF NOT EXISTS models (
    name TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    api_key TEXT,
    api_url TEXT,
    max_input_tokens INTEGER,
    max_output_tokens INTEGER,
    context_window INTEGER,
    code_score REAL,
    reasoning_score REAL,
    speed_score REAL,
    cost_per_1k_input REAL,
    cost_per_1k_output REAL,
    specialties TEXT,
    notes TEXT,
    vscode_friendly INTEGER DEFAULT 1,
    supports_function_calling INTEGER DEFAULT 0,
    supports_xml_format INTEGER DEFAULT 0,
    supports_json_mode INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


@dataclass
class ModelSchema:
    """模型数据类"""
    name: str
    provider: str
    api_key: Optional[str] = None
    api_url: Optional[str] = None
    max_input_tokens: Optional[int] = None
    max_output_tokens: Optional[int] = None
    context_window: Optional[int] = None
    code_score: Optional[float] = None
    reasoning_score: Optional[float] = None
    speed_score: Optional[float] = None
    cost_per_1k_input: Optional[float] = None
    cost_per_1k_output: Optional[float] = None
    specialties: Optional[List[str]] = None
    notes: Optional[str] = None
    vscode_friendly: bool = True  # 是否能很好地遵循代码编辑格式要求
    supports_function_calling: bool = False  # 是否支持 Function Calling
    supports_xml_format: bool = False  # 是否支持 XML 格式（Prompt Engineering）
    supports_json_mode: bool = False  # 是否支持 JSON Mode

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于数据库存储）"""
        data = asdict(self)
        # 将列表转为逗号分隔的字符串
        if self.specialties:
            data['specialties'] = ','.join(self.specialties)
        else:
            data['specialties'] = None
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelSchema':
        """从字典创建实例（从数据库读取）"""
        data = data.copy()
        # 将逗号分隔的字符串转为列表
        if data.get('specialties') and isinstance(data['specialties'], str):
            data['specialties'] = [s.strip() for s in data['specialties'].split(',') if s.strip()]
        return cls(**data)

    def get_context_limit(self) -> Optional[int]:
        """
        获取有效的上下文限制
        优先级：context_window > max_input_tokens
        返回安全值（乘以缓冲比例）
        """
        limit = None
        if self.context_window is not None:
            limit = self.context_window
        elif self.max_input_tokens is not None:
            limit = self.max_input_tokens

        if limit is not None:
            return int(limit * TOKEN_BUFFER_RATIO)
        return None

    def validate_scores(self) -> bool:
        """验证评分是否在有效范围内"""
        scores = [self.code_score, self.reasoning_score, self.speed_score]
        for score in scores:
            if score is not None:
                if not (MIN_SCORE <= score <= MAX_SCORE):
                    return False
        return True


def row_to_model(row: Any) -> ModelSchema:
    """
    将数据库行转换为 ModelSchema
    支持 dict 或 sqlite3.Row 对象
    """
    if hasattr(row, 'keys'):
        # sqlite3.Row 对象或字典
        data = dict(row)
    else:
        # 元组形式
        raise ValueError("Unsupported row type")

    # 移除时间戳字段（不在 ModelSchema 中）
    data.pop('created_at', None)
    data.pop('updated_at', None)

    return ModelSchema.from_dict(data)


def import_model_from_preconfig(config: Dict[str, Any]) -> ModelSchema:
    """
    从预配置字典导入模型
    自动填充默认值
    """
    # 必需字段
    name = config.get('name')
    provider = config.get('provider')

    if not name or not provider:
        raise ValueError("name and provider are required")

    # 创建模型实例
    return ModelSchema(
        name=name,
        provider=provider,
        api_key=config.get('api_key'),
        api_url=config.get('api_url'),
        max_input_tokens=config.get('max_input_tokens'),
        max_output_tokens=config.get('max_output_tokens'),
        context_window=config.get('context_window'),
        code_score=config.get('code_score'),
        reasoning_score=config.get('reasoning_score'),
        speed_score=config.get('speed_score'),
        cost_per_1k_input=config.get('cost_per_1k_input'),
        cost_per_1k_output=config.get('cost_per_1k_output'),
        specialties=config.get('specialties'),
        notes=config.get('notes')
    )
