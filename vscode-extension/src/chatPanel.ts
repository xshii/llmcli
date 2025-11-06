/**
 * Chat Panel - Webview UI for chat interface
 */
import * as vscode from 'vscode';
import { RPCClient, FileContext } from './rpcClient';
import { DiffManager, CodeEdit } from './diffManager';

export class ChatPanel {
    private panel: vscode.WebviewPanel | undefined;
    private disposables: vscode.Disposable[] = [];

    constructor(
        private context: vscode.ExtensionContext,
        private rpcClient: RPCClient,
        private diffManager: DiffManager
    ) {}

    /**
     * 显示聊天面板
     */
    async show(): Promise<void> {
        if (this.panel) {
            this.panel.reveal();
            return;
        }

        this.panel = vscode.window.createWebviewPanel(
            'aicodeChat',
            'AICode Chat',
            vscode.ViewColumn.Beside,
            {
                enableScripts: true,
                retainContextWhenHidden: true,
                localResourceRoots: [this.context.extensionUri]
            }
        );

        this.panel.webview.html = this.getHtmlContent();

        // 处理来自 webview 的消息
        this.panel.webview.onDidReceiveMessage(
            async (message) => {
                await this.handleMessage(message);
            },
            null,
            this.disposables
        );

        // 面板关闭时清理
        this.panel.onDidDispose(
            () => {
                this.panel = undefined;
                this.disposables.forEach(d => d.dispose());
                this.disposables = [];
            },
            null,
            this.disposables
        );

        // 加载历史消息
        await this.loadHistory();
    }

    /**
     * 处理来自 webview 的消息
     */
    private async handleMessage(message: any): Promise<void> {
        switch (message.type) {
            case 'sendMessage':
                await this.sendMessage(message.text);
                break;

            case 'clearHistory':
                await this.clearHistory();
                break;

            case 'selectModel':
                await this.selectModel();
                break;

            case 'ready':
                // Webview 加载完成
                await this.loadHistory();
                break;
        }
    }

    /**
     * 发送消息到 AI
     */
    private async sendMessage(text: string): Promise<void> {
        if (!this.panel) {
            return;
        }

        try {
            // 显示用户消息
            this.panel.webview.postMessage({
                type: 'addMessage',
                message: {
                    role: 'user',
                    content: text
                }
            });

            // 获取文件上下文
            const context = await this.getFileContext();

            // 显示加载状态
            this.panel.webview.postMessage({
                type: 'setLoading',
                loading: true
            });

            // 发送到后端
            const response = await this.rpcClient.chat(text, context);

            if (response.success) {
                // 显示 AI 响应
                this.panel.webview.postMessage({
                    type: 'addMessage',
                    message: {
                        role: 'assistant',
                        content: response.response
                    }
                });

                // 显示 token 和成本信息
                if (response.tokens || response.cost) {
                    this.panel.webview.postMessage({
                        type: 'showInfo',
                        info: `Tokens: ${response.tokens} | Cost: $${response.cost?.toFixed(6) || '0.000000'}`
                    });
                }

                // 如果有代码编辑建议，显示差异视图
                if (response.edits && response.edits.length > 0) {
                    vscode.window.showInformationMessage(
                        `${response.edits.length} code change(s) proposed`,
                        'Review Changes'
                    ).then(action => {
                        if (action === 'Review Changes') {
                            this.diffManager.showEdits(response.edits);
                        }
                    });

                    // 在聊天中显示编辑摘要
                    if (response.edits_summary) {
                        this.panel.webview.postMessage({
                            type: 'addMessage',
                            message: {
                                role: 'system',
                                content: response.edits_summary
                            }
                        });
                    }
                }
            } else {
                throw new Error(response.error || 'Unknown error');
            }

        } catch (error: any) {
            vscode.window.showErrorMessage(`Chat error: ${error.message}`);
            this.panel.webview.postMessage({
                type: 'addMessage',
                message: {
                    role: 'error',
                    content: `Error: ${error.message}`
                }
            });
        } finally {
            // 取消加载状态
            this.panel.webview.postMessage({
                type: 'setLoading',
                loading: false
            });
        }
    }

    /**
     * 获取文件上下文
     */
    private async getFileContext(): Promise<FileContext[]> {
        const config = vscode.workspace.getConfiguration('aicode');
        const autoSendContext = config.get<boolean>('autoSendContext', true);

        if (!autoSendContext) {
            return [];
        }

        const context: FileContext[] = [];
        const maxFiles = config.get<number>('maxContextFiles', 3);

        // 获取当前活动编辑器
        const editor = vscode.window.activeTextEditor;
        if (editor) {
            const document = editor.document;
            context.push({
                path: vscode.workspace.asRelativePath(document.uri),
                content: document.getText()
            });
        }

        // TODO: 可以添加更多文件（如最近打开的文件）

        return context.slice(0, maxFiles);
    }

    /**
     * 加载对话历史
     */
    private async loadHistory(): Promise<void> {
        if (!this.panel) {
            return;
        }

        try {
            const response = await this.rpcClient.getHistory();
            if (response.success && response.messages) {
                this.panel.webview.postMessage({
                    type: 'loadHistory',
                    messages: response.messages
                });
            }
        } catch (error: any) {
            console.error('Failed to load history:', error);
        }
    }

    /**
     * 清除对话历史
     */
    private async clearHistory(): Promise<void> {
        try {
            await this.rpcClient.clearHistory();
            if (this.panel) {
                this.panel.webview.postMessage({
                    type: 'clearMessages'
                });
            }
            vscode.window.showInformationMessage('Chat history cleared');
        } catch (error: any) {
            vscode.window.showErrorMessage(`Failed to clear history: ${error.message}`);
        }
    }

    /**
     * 选择模型
     */
    private async selectModel(): Promise<void> {
        try {
            const response = await this.rpcClient.getModels();
            if (!response.success) {
                throw new Error(response.error);
            }

            const models = response.models;
            const items = models.map((m: any) => ({
                label: m.name,
                description: `${m.provider} | Score: ${m.code_score || 'N/A'}`
            }));

            const selected = await vscode.window.showQuickPick(items, {
                placeHolder: 'Select a model'
            });

            if (selected) {
                await this.rpcClient.setModel(selected.label);
                vscode.window.showInformationMessage(`Model changed to: ${selected.label}`);
            }
        } catch (error: any) {
            vscode.window.showErrorMessage(`Failed to select model: ${error.message}`);
        }
    }

    /**
     * 发送选中的代码到聊天
     */
    async sendSelection(text: string): Promise<void> {
        await this.show();
        if (this.panel) {
            this.panel.webview.postMessage({
                type: 'setInput',
                text: `Explain this code:\n\`\`\`\n${text}\n\`\`\``
            });
        }
    }

    /**
     * 生成 HTML 内容
     */
    private getHtmlContent(): string {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AICode Chat</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: var(--vscode-font-family);
            font-size: var(--vscode-font-size);
            color: var(--vscode-foreground);
            background-color: var(--vscode-editor-background);
            height: 100vh;
            display: flex;
            flex-direction: column;
        }

        #header {
            padding: 10px;
            border-bottom: 1px solid var(--vscode-panel-border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        #header h2 {
            font-size: 14px;
            font-weight: 600;
        }

        #header-buttons {
            display: flex;
            gap: 8px;
        }

        button {
            background-color: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            padding: 6px 12px;
            cursor: pointer;
            font-size: 12px;
            border-radius: 2px;
        }

        button:hover {
            background-color: var(--vscode-button-hoverBackground);
        }

        #messages {
            flex: 1;
            overflow-y: auto;
            padding: 16px;
        }

        .message {
            margin-bottom: 16px;
            padding: 12px;
            border-radius: 4px;
        }

        .message.user {
            background-color: var(--vscode-input-background);
            border-left: 3px solid var(--vscode-button-background);
        }

        .message.assistant {
            background-color: var(--vscode-editor-inactiveSelectionBackground);
            border-left: 3px solid var(--vscode-focusBorder);
        }

        .message.error {
            background-color: var(--vscode-inputValidation-errorBackground);
            border-left: 3px solid var(--vscode-inputValidation-errorBorder);
        }

        .message-role {
            font-weight: 600;
            font-size: 11px;
            text-transform: uppercase;
            margin-bottom: 6px;
            opacity: 0.8;
        }

        .message-content {
            line-height: 1.6;
            white-space: pre-wrap;
        }

        .message-content code {
            background-color: var(--vscode-textCodeBlock-background);
            padding: 2px 4px;
            border-radius: 2px;
            font-family: var(--vscode-editor-font-family);
        }

        #info {
            padding: 8px 16px;
            font-size: 11px;
            color: var(--vscode-descriptionForeground);
            border-top: 1px solid var(--vscode-panel-border);
        }

        #input-container {
            padding: 12px;
            border-top: 1px solid var(--vscode-panel-border);
            display: flex;
            gap: 8px;
        }

        #input {
            flex: 1;
            background-color: var(--vscode-input-background);
            color: var(--vscode-input-foreground);
            border: 1px solid var(--vscode-input-border);
            padding: 8px;
            font-family: var(--vscode-font-family);
            font-size: var(--vscode-font-size);
            resize: vertical;
            min-height: 60px;
        }

        #input:focus {
            outline: 1px solid var(--vscode-focusBorder);
        }

        #send-btn {
            align-self: flex-end;
        }

        .loading {
            display: none;
            padding: 12px;
            text-align: center;
            color: var(--vscode-descriptionForeground);
        }

        .loading.active {
            display: block;
        }
    </style>
</head>
<body>
    <div id="header">
        <h2>AICode Chat</h2>
        <div id="header-buttons">
            <button id="model-btn">Model</button>
            <button id="clear-btn">Clear</button>
        </div>
    </div>

    <div id="messages"></div>

    <div class="loading" id="loading">
        <span>Thinking...</span>
    </div>

    <div id="info"></div>

    <div id="input-container">
        <textarea id="input" placeholder="Type your message..."></textarea>
        <button id="send-btn">Send</button>
    </div>

    <script>
        const vscode = acquireVsCodeApi();
        const messagesDiv = document.getElementById('messages');
        const inputTextarea = document.getElementById('input');
        const sendBtn = document.getElementById('send-btn');
        const clearBtn = document.getElementById('clear-btn');
        const modelBtn = document.getElementById('model-btn');
        const loadingDiv = document.getElementById('loading');
        const infoDiv = document.getElementById('info');

        // 发送消息
        function sendMessage() {
            const text = inputTextarea.value.trim();
            if (!text) return;

            vscode.postMessage({
                type: 'sendMessage',
                text: text
            });

            inputTextarea.value = '';
        }

        // 添加消息到界面
        function addMessage(role, content) {
            const messageDiv = document.createElement('div');
            messageDiv.className = \`message \${role}\`;

            const roleDiv = document.createElement('div');
            roleDiv.className = 'message-role';
            roleDiv.textContent = role;

            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            contentDiv.textContent = content;

            messageDiv.appendChild(roleDiv);
            messageDiv.appendChild(contentDiv);

            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        // 事件监听
        sendBtn.addEventListener('click', sendMessage);

        inputTextarea.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                e.preventDefault();
                sendMessage();
            }
        });

        clearBtn.addEventListener('click', () => {
            vscode.postMessage({ type: 'clearHistory' });
        });

        modelBtn.addEventListener('click', () => {
            vscode.postMessage({ type: 'selectModel' });
        });

        // 接收来自扩展的消息
        window.addEventListener('message', (event) => {
            const message = event.data;

            switch (message.type) {
                case 'addMessage':
                    addMessage(message.message.role, message.message.content);
                    break;

                case 'clearMessages':
                    messagesDiv.innerHTML = '';
                    infoDiv.textContent = '';
                    break;

                case 'loadHistory':
                    messagesDiv.innerHTML = '';
                    message.messages.forEach(msg => {
                        addMessage(msg.role, msg.content);
                    });
                    break;

                case 'setLoading':
                    if (message.loading) {
                        loadingDiv.classList.add('active');
                    } else {
                        loadingDiv.classList.remove('active');
                    }
                    break;

                case 'showInfo':
                    infoDiv.textContent = message.info;
                    break;

                case 'setInput':
                    inputTextarea.value = message.text;
                    break;
            }
        });

        // 通知扩展 webview 已准备好
        vscode.postMessage({ type: 'ready' });
    </script>
</body>
</html>`;
    }
}
