# AICode VSCode Extension - Setup Guide

## Prerequisites

1. **Python 3.9+** installed
2. **Node.js 18+** and npm installed
3. **VSCode 1.80+**

## Setup Steps

### 1. Install AICode Python Package

```bash
cd /Users/gakki/dev/llmcli
source venv/bin/activate
pip install -e .
```

### 2. Configure AICode

```bash
# Initialize configuration
aicode config init

# Set your API key
aicode config set global.api_key YOUR_API_KEY_HERE

# Add a model
aicode model add gpt-4 \
  --provider openai \
  --max-input 8192 \
  --max-output 4096 \
  --code-score 9.0

# Verify setup
aicode config show
aicode model list
```

### 3. Build VSCode Extension

```bash
cd vscode-extension
npm install
npm run compile
```

### 4. Install Extension in VSCode

#### Option A: Development Mode (F5)

1. Open `vscode-extension` folder in VSCode
2. Press `F5` to start debugging
3. A new VSCode window opens with the extension loaded

#### Option B: Install from VSIX

1. Package the extension:
   ```bash
   npm install -g vsce
   vsce package
   ```

2. Install the generated `.vsix` file:
   - Open VSCode
   - Go to Extensions (`Cmd+Shift+X`)
   - Click "..." menu → "Install from VSIX..."
   - Select the `.vsix` file

### 5. Configure Extension (Optional)

In VSCode settings:

```json
{
  "aicode.pythonPath": "python",  // or full path to venv python
  "aicode.serverPath": "",        // leave empty if aicode is in PATH
  "aicode.autoSendContext": true,
  "aicode.maxContextFiles": 3
}
```

If AICode is not in your system PATH, set the full path:

```json
{
  "aicode.pythonPath": "/Users/gakki/dev/llmcli/venv/bin/python",
  "aicode.serverPath": "/Users/gakki/dev/llmcli"
}
```

## Usage

### Open Chat

- **Keyboard**: `Ctrl+Shift+A` (Mac: `Cmd+Shift+A`)
- **Status Bar**: Click "AICode" in bottom right
- **Command Palette**: `AICode: Open Chat`

### Send Code to Chat

1. Select code in editor
2. **Right-click** → "AICode: Send Selection to Chat"
3. Or press `Ctrl+Shift+C` (Mac: `Cmd+Shift+C`)

### Chat Interface

- **Type message** in the text area
- **Press** `Ctrl+Enter` or `Cmd+Enter` to send
- **Click "Model"** to switch AI models
- **Click "Clear"** to clear conversation history

## Troubleshooting

### Extension doesn't activate

1. Check Output panel: View → Output → Select "AICode"
2. Verify Python path in settings
3. Test CLI manually:
   ```bash
   aicode server --mode stdio
   # Should start and wait for input
   ```

### Chat doesn't respond

1. Check if API key is configured:
   ```bash
   aicode config show
   ```

2. Check server logs in Output panel
3. Try selecting a different model

### "Module not found" error

Make sure AICode is installed in the Python environment:

```bash
source venv/bin/activate
pip list | grep aicode
```

If not listed:

```bash
pip install -e /Users/gakki/dev/llmcli
```

## Development

### Project Structure

```
vscode-extension/
├── package.json          # Extension manifest
├── tsconfig.json         # TypeScript config
├── src/
│   ├── extension.ts      # Main entry point
│   ├── rpcClient.ts      # JSON-RPC client
│   └── chatPanel.ts      # Webview UI
├── resources/
│   └── icon.svg          # Extension icon
└── out/                  # Compiled JavaScript
```

### Build and Watch

```bash
# One-time compile
npm run compile

# Watch mode (auto-recompile on changes)
npm run watch
```

### Debug

1. Open extension folder in VSCode
2. Set breakpoints in TypeScript files
3. Press F5
4. Debug in the new VSCode window that opens

## Next Steps

- Try asking questions about your code
- Experiment with different models
- Adjust context settings for better responses
- Report issues or suggest features
