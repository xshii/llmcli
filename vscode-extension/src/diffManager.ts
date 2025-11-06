/**
 * Diff Manager - 管理代码差异视图和应用
 */
import * as vscode from 'vscode';
import * as path from 'path';

export interface CodeEdit {
    file_path: string;
    original_content?: string;
    new_content: string;
    description: string;
    edit_type: string;  // modify, create, delete
}

export class DiffManager {
    private pendingEdits: Map<number, CodeEdit> = new Map();
    private editCounter = 0;

    constructor(private context: vscode.ExtensionContext) {}

    /**
     * 显示代码编辑列表
     */
    async showEdits(edits: CodeEdit[]): Promise<void> {
        if (edits.length === 0) {
            vscode.window.showInformationMessage('No code changes proposed');
            return;
        }

        // 保存待处理的编辑
        this.pendingEdits.clear();
        edits.forEach((edit, index) => {
            this.pendingEdits.set(index + 1, edit);
        });

        // 显示编辑列表
        const items = edits.map((edit, index) => ({
            label: `${index + 1}. ${edit.file_path}`,
            description: edit.description || edit.edit_type,
            detail: `Type: ${edit.edit_type}`,
            index: index + 1,
            edit
        }));

        // 添加额外选项
        items.push(
            {
                label: 'Apply All',
                description: 'Apply all changes',
                detail: `Apply ${edits.length} change(s)`,
                index: -1,
                edit: null as any
            },
            {
                label: 'Skip',
                description: 'Do not apply any changes',
                detail: '',
                index: 0,
                edit: null as any
            }
        );

        const selected = await vscode.window.showQuickPick(items, {
            placeHolder: 'Select code change to review or apply'
        });

        if (!selected) {
            return;
        }

        if (selected.index === 0) {
            // Skip
            vscode.window.showInformationMessage('Skipped all changes');
            return;
        }

        if (selected.index === -1) {
            // Apply all
            await this.applyAllEdits();
        } else {
            // Review single edit
            await this.reviewEdit(selected.index);
        }
    }

    /**
     * 审查单个编辑
     */
    private async reviewEdit(editIndex: number): Promise<void> {
        const edit = this.pendingEdits.get(editIndex);
        if (!edit) {
            vscode.window.showErrorMessage('Edit not found');
            return;
        }

        // 获取工作区根路径
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            vscode.window.showErrorMessage('No workspace folder open');
            return;
        }

        const filePath = path.join(workspaceFolder.uri.fsPath, edit.file_path);
        const fileUri = vscode.Uri.file(filePath);

        // 读取原始文件内容（如果存在）
        let originalContent = '';
        try {
            const fileData = await vscode.workspace.fs.readFile(fileUri);
            originalContent = Buffer.from(fileData).toString('utf8');
        } catch (e) {
            // 文件不存在，可能是新建文件
            if (edit.edit_type !== 'create') {
                vscode.window.showWarningMessage(`File not found: ${edit.file_path}`);
            }
        }

        // 创建临时文件用于diff
        const tempUri = vscode.Uri.parse(`aicode-temp:${edit.file_path}`);

        // 注册临时文件内容provider
        const provider = new class implements vscode.TextDocumentContentProvider {
            provideTextDocumentContent(uri: vscode.Uri): string {
                return edit.new_content;
            }
        }();

        this.context.subscriptions.push(
            vscode.workspace.registerTextDocumentContentProvider('aicode-temp', provider)
        );

        // 打开 diff 视图
        const title = `${edit.file_path} (Proposed Change)`;

        try {
            await vscode.commands.executeCommand(
                'vscode.diff',
                fileUri,  // 原始文件
                tempUri,  // 新内容
                title
            );

            // 询问是否应用
            const action = await vscode.window.showInformationMessage(
                `Apply this change to ${edit.file_path}?`,
                'Apply',
                'Skip',
                'View Others'
            );

            if (action === 'Apply') {
                await this.applyEdit(edit);
            } else if (action === 'View Others') {
                // 移除当前编辑并显示其余编辑
                this.pendingEdits.delete(editIndex);
                const remainingEdits = Array.from(this.pendingEdits.values());
                if (remainingEdits.length > 0) {
                    await this.showEdits(remainingEdits);
                }
            }
        } catch (error: any) {
            vscode.window.showErrorMessage(`Failed to show diff: ${error.message}`);
        }
    }

    /**
     * 应用单个编辑
     */
    private async applyEdit(edit: CodeEdit): Promise<boolean> {
        try {
            const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
            if (!workspaceFolder) {
                throw new Error('No workspace folder open');
            }

            const filePath = path.join(workspaceFolder.uri.fsPath, edit.file_path);
            const fileUri = vscode.Uri.file(filePath);

            // 写入新内容
            const content = Buffer.from(edit.new_content, 'utf8');
            await vscode.workspace.fs.writeFile(fileUri, content);

            vscode.window.showInformationMessage(`✓ Applied: ${edit.file_path}`);
            return true;

        } catch (error: any) {
            vscode.window.showErrorMessage(`Failed to apply edit: ${error.message}`);
            return false;
        }
    }

    /**
     * 应用所有编辑
     */
    private async applyAllEdits(): Promise<void> {
        const edits = Array.from(this.pendingEdits.values());
        let successCount = 0;
        let failCount = 0;

        for (const edit of edits) {
            const success = await this.applyEdit(edit);
            if (success) {
                successCount++;
            } else {
                failCount++;
            }
        }

        vscode.window.showInformationMessage(
            `Applied ${successCount} change(s)${failCount > 0 ? `, ${failCount} failed` : ''}`
        );

        this.pendingEdits.clear();
    }

    /**
     * 处理数字输入（来自聊天）
     */
    async handleNumberInput(input: string): Promise<boolean> {
        // 检查是否是数字
        const num = parseInt(input.trim());
        if (isNaN(num)) {
            return false;
        }

        // 检查是否在范围内
        if (!this.pendingEdits.has(num)) {
            vscode.window.showWarningMessage(`No pending edit #${num}`);
            return true; // 表示已处理
        }

        // 审查该编辑
        await this.reviewEdit(num);
        return true;
    }

    /**
     * 处理 "all" 输入
     */
    async handleAllInput(input: string): Promise<boolean> {
        if (input.trim().toLowerCase() !== 'all') {
            return false;
        }

        if (this.pendingEdits.size === 0) {
            vscode.window.showWarningMessage('No pending edits');
            return true;
        }

        await this.applyAllEdits();
        return true;
    }

    /**
     * 获取待处理编辑数量
     */
    getPendingCount(): number {
        return this.pendingEdits.size;
    }

    /**
     * 清除待处理编辑
     */
    clearPendingEdits(): void {
        this.pendingEdits.clear();
    }
}
