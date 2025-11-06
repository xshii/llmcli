/**
 * JSON-RPC Client - 与 Python 后端通信
 */
import * as cp from 'child_process';
import * as vscode from 'vscode';

export interface RPCRequest {
    jsonrpc: string;
    id: number;
    method: string;
    params: any;
}

export interface RPCResponse {
    jsonrpc: string;
    id: number;
    result?: any;
    error?: {
        code: number;
        message: string;
    };
}

export interface ChatMessage {
    role: string;
    content: string;
}

export interface FileContext {
    path: string;
    content: string;
}

export class RPCClient {
    private process: cp.ChildProcess | null = null;
    private requestId = 0;
    private pendingRequests = new Map<number, {
        resolve: (value: any) => void;
        reject: (reason: any) => void;
    }>();
    private outputChannel: vscode.OutputChannel;
    private isInitialized = false;

    constructor(private context: vscode.ExtensionContext) {
        this.outputChannel = vscode.window.createOutputChannel('AICode');
    }

    /**
     * 启动 RPC server
     */
    async start(): Promise<void> {
        const config = vscode.workspace.getConfiguration('aicode');
        const pythonPath = config.get<string>('pythonPath', 'python');
        const serverPath = config.get<string>('serverPath', '');

        // 构建命令
        const args = ['-m', 'aicode.cli.main', 'server', '--mode', 'stdio'];

        this.outputChannel.appendLine(`Starting RPC server: ${pythonPath} ${args.join(' ')}`);

        try {
            this.process = cp.spawn(pythonPath, args, {
                cwd: serverPath || undefined,
                stdio: ['pipe', 'pipe', 'pipe']
            });

            // 处理 stdout（响应）
            this.process.stdout?.on('data', (data: Buffer) => {
                const lines = data.toString().split('\n').filter(line => line.trim());
                for (const line of lines) {
                    try {
                        const response: RPCResponse = JSON.parse(line);
                        this.handleResponse(response);
                    } catch (e) {
                        this.outputChannel.appendLine(`Failed to parse response: ${line}`);
                    }
                }
            });

            // 处理 stderr（日志）
            this.process.stderr?.on('data', (data: Buffer) => {
                this.outputChannel.appendLine(`[Server] ${data.toString()}`);
            });

            // 处理退出
            this.process.on('exit', (code) => {
                this.outputChannel.appendLine(`Server exited with code ${code}`);
                this.process = null;
                this.isInitialized = false;
            });

            // 初始化服务器
            await this.initialize();
            this.isInitialized = true;
            this.outputChannel.appendLine('RPC server started successfully');

        } catch (error) {
            this.outputChannel.appendLine(`Failed to start server: ${error}`);
            throw error;
        }
    }

    /**
     * 停止 RPC server
     */
    stop(): void {
        if (this.process) {
            this.process.kill();
            this.process = null;
            this.isInitialized = false;
            this.outputChannel.appendLine('RPC server stopped');
        }
    }

    /**
     * 发送 RPC 请求
     */
    private async sendRequest(method: string, params: any = {}): Promise<any> {
        if (!this.process || !this.process.stdin) {
            throw new Error('RPC server not running');
        }

        const id = ++this.requestId;
        const request: RPCRequest = {
            jsonrpc: '2.0',
            id,
            method,
            params
        };

        return new Promise((resolve, reject) => {
            this.pendingRequests.set(id, { resolve, reject });

            const requestLine = JSON.stringify(request) + '\n';
            this.process!.stdin!.write(requestLine);

            // 超时处理
            setTimeout(() => {
                if (this.pendingRequests.has(id)) {
                    this.pendingRequests.delete(id);
                    reject(new Error(`Request timeout: ${method}`));
                }
            }, 30000); // 30 秒超时
        });
    }

    /**
     * 处理响应
     */
    private handleResponse(response: RPCResponse): void {
        const pending = this.pendingRequests.get(response.id);
        if (!pending) {
            return;
        }

        this.pendingRequests.delete(response.id);

        if (response.error) {
            pending.reject(new Error(response.error.message));
        } else {
            pending.resolve(response.result);
        }
    }

    /**
     * 初始化服务器
     */
    async initialize(model?: string): Promise<any> {
        return this.sendRequest('initialize', { model });
    }

    /**
     * 发送聊天消息
     */
    async chat(message: string, context?: FileContext[], temperature?: number): Promise<any> {
        return this.sendRequest('chat', {
            message,
            context,
            temperature
        });
    }

    /**
     * 获取可用模型列表
     */
    async getModels(): Promise<any> {
        return this.sendRequest('getModels', {});
    }

    /**
     * 切换模型
     */
    async setModel(model: string): Promise<any> {
        return this.sendRequest('setModel', { model });
    }

    /**
     * 获取配置
     */
    async getConfig(key?: string): Promise<any> {
        return this.sendRequest('getConfig', { key });
    }

    /**
     * 设置配置
     */
    async setConfig(key: string, value: any): Promise<any> {
        return this.sendRequest('setConfig', { key, value });
    }

    /**
     * 清除对话历史
     */
    async clearHistory(): Promise<any> {
        return this.sendRequest('clearHistory', {});
    }

    /**
     * 获取对话历史
     */
    async getHistory(): Promise<any> {
        return this.sendRequest('getHistory', {});
    }

    /**
     * 关闭服务器
     */
    async shutdown(): Promise<any> {
        const result = await this.sendRequest('shutdown', {});
        this.stop();
        return result;
    }
}
