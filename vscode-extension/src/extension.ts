/**
 * AICode VSCode Extension
 */
import * as vscode from 'vscode';
import { RPCClient } from './rpcClient';
import { ChatPanel } from './chatPanel';
import { DiffManager } from './diffManager';

let rpcClient: RPCClient;
let chatPanel: ChatPanel;
let diffManager: DiffManager;

/**
 * 扩展激活时调用
 */
export async function activate(context: vscode.ExtensionContext) {
    console.log('AICode extension is now active');

    // 创建管理器
    rpcClient = new RPCClient(context);
    diffManager = new DiffManager(context);
    chatPanel = new ChatPanel(context, rpcClient, diffManager);

    // 启动 RPC server
    try {
        await rpcClient.start();
        vscode.window.showInformationMessage('AICode is ready!');
    } catch (error: any) {
        vscode.window.showErrorMessage(`Failed to start AICode: ${error.message}`);
        return;
    }

    // 注册命令: 打开聊天
    context.subscriptions.push(
        vscode.commands.registerCommand('aicode.openChat', async () => {
            await chatPanel.show();
        })
    );

    // 注册命令: 清除历史
    context.subscriptions.push(
        vscode.commands.registerCommand('aicode.clearHistory', async () => {
            try {
                await rpcClient.clearHistory();
                vscode.window.showInformationMessage('Chat history cleared');
            } catch (error: any) {
                vscode.window.showErrorMessage(`Failed to clear history: ${error.message}`);
            }
        })
    );

    // 注册命令: 选择模型
    context.subscriptions.push(
        vscode.commands.registerCommand('aicode.selectModel', async () => {
            try {
                const response = await rpcClient.getModels();
                if (!response.success) {
                    throw new Error(response.error);
                }

                const models = response.models;
                const items = models.map((m: any) => ({
                    label: m.name,
                    description: `${m.provider} | Score: ${m.code_score || 'N/A'}`,
                    detail: `Max tokens: ${m.max_input_tokens} / ${m.max_output_tokens}`
                }));

                const selected = await vscode.window.showQuickPick(items, {
                    placeHolder: 'Select a model'
                });

                if (selected) {
                    await rpcClient.setModel(selected.label);
                    vscode.window.showInformationMessage(`Model changed to: ${selected.label}`);
                }
            } catch (error: any) {
                vscode.window.showErrorMessage(`Failed to select model: ${error.message}`);
            }
        })
    );

    // 注册命令: 发送选中的代码到聊天
    context.subscriptions.push(
        vscode.commands.registerCommand('aicode.sendToChat', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showWarningMessage('No active editor');
                return;
            }

            const selection = editor.selection;
            const text = editor.document.getText(selection);

            if (!text) {
                vscode.window.showWarningMessage('No text selected');
                return;
            }

            await chatPanel.sendSelection(text);
        })
    );

    // 状态栏按钮
    const statusBarItem = vscode.window.createStatusBarItem(
        vscode.StatusBarAlignment.Right,
        100
    );
    statusBarItem.text = '$(comment-discussion) AICode';
    statusBarItem.command = 'aicode.openChat';
    statusBarItem.tooltip = 'Open AICode Chat';
    statusBarItem.show();
    context.subscriptions.push(statusBarItem);
}

/**
 * 扩展停用时调用
 */
export function deactivate() {
    if (rpcClient) {
        rpcClient.stop();
    }
}
