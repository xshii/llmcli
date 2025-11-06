# AICode VSCode Extension

AI-powered coding assistant for VSCode, powered by the AICode Python CLI.

## Features

- **Interactive Chat**: Chat with AI models directly in VSCode
- **Automatic Context**: Automatically sends current file context with your questions
- **Model Selection**: Easily switch between different AI models
- **Code Explanation**: Right-click and send selected code to chat
- **Conversation History**: Maintains conversation history across sessions

## Requirements

- Python 3.9 or higher
- AICode CLI installed (`pip install -e /path/to/aicode`)
- Configured API key in AICode

## Installation

1. Install the AICode Python package
2. Configure AICode:
   ```bash
   aicode config init
   aicode config set global.api_key YOUR_API_KEY
   aicode model add gpt-4 --provider openai
   ```
3. Install this extension in VSCode

## Usage

### Open Chat Panel

- Press `Ctrl+Shift+A` (or `Cmd+Shift+A` on Mac)
- Or click the AICode icon in the status bar
- Or use the command palette: `AICode: Open Chat`

### Send Code to Chat

1. Select code in the editor
2. Right-click and choose "AICode: Send Selection to Chat"
3. Or press `Ctrl+Shift+C` (or `Cmd+Shift+C` on Mac)

### Change Model

- Click the "Model" button in the chat panel
- Or use the command palette: `AICode: Select Model`

### Clear History

- Click the "Clear" button in the chat panel
- Or use the command palette: `AICode: Clear History`

## Extension Settings

This extension contributes the following settings:

- `aicode.pythonPath`: Path to Python interpreter (default: `python`)
- `aicode.serverPath`: Path to aicode CLI directory (optional)
- `aicode.autoSendContext`: Automatically send current file context with messages (default: `true`)
- `aicode.maxContextFiles`: Maximum number of files to include in context (default: `3`)

## Known Issues

- Streaming responses not yet implemented
- Limited to stdio communication mode

## Release Notes

### 0.1.0

Initial release with basic chat functionality:
- Chat panel with webview UI
- JSON-RPC communication with Python backend
- Automatic file context
- Model selection
- Conversation history

## Development

### Build

```bash
cd vscode-extension
npm install
npm run compile
```

### Run Extension

1. Open this folder in VSCode
2. Press F5 to start debugging
3. A new VSCode window will open with the extension loaded

## License

MIT
