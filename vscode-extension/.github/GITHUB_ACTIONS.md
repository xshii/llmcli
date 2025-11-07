# GitHub Actions CI/CD for VSCode Extension

This document describes the CI/CD workflows for the AICode VSCode extension.

## 🔄 Workflows

### 1. **CI Pipeline** (`ci.yml`)

Runs on every push and pull request to `main` and `develop` branches.

**Jobs:**

#### 📋 **Lint**
- Runs ESLint on TypeScript code
- Performs TypeScript type checking with `tsc --noEmit`
- Ensures code quality and type safety

#### 🏗️ **Build**
- Tests building on multiple platforms: Ubuntu, Windows, macOS
- Tests multiple Node.js versions: 16, 18, 20
- Compiles TypeScript to JavaScript
- Validates compiled output

#### 📦 **Package**
- Packages extension into `.vsix` file using `vsce`
- Uploads VSIX as artifact (30-day retention)
- Ensures extension can be installed in VSCode

#### 🧪 **Test**
- Runs extension tests (when implemented)
- Currently marked as optional with `continue-on-error: true`

**Status Badge:**
```markdown
[![CI](https://github.com/xshii/llmcli/workflows/CI/badge.svg)](https://github.com/xshii/llmcli/actions/workflows/ci.yml)
```

---

### 2. **PR Labeler** (`pr-labeler.yml`)

Automatically enhances pull requests with labels and comments.

**Features:**
- **File-based labels**: Labels PRs based on changed files (e.g., `area: ui`, `area: rpc`)
- **Size labels**: Automatically labels PR size from `size/XS` to `size/XL`
- **Welcome comment**: Adds a checklist comment to new PRs

**Label Categories:**
- **Type**: `type: documentation`, `type: dependencies`, `type: config`
- **Area**: `area: ui`, `area: rpc`, `area: extension`, `area: diff`, `area: ci`
- **Size**: `size/XS` (≤10 lines) to `size/XL` (>1000 lines)

---

### 3. **CodeQL Security Scan** (`codeql.yml`)

Automated security vulnerability scanning.

**Triggers:**
- Push to main/develop branches
- Pull requests
- Weekly scheduled scan (Mondays 6 AM UTC)

**Capabilities:**
- Analyzes JavaScript/TypeScript code
- Detects security vulnerabilities
- Generates security alerts in GitHub Security tab

---

### 4. **Release** (`release.yml`)

Automated release creation and publishing.

**Trigger:** Version tags (e.g., `v0.1.0`, `v1.2.3`)

**Steps:**
1. Compiles TypeScript
2. Packages extension into `.vsix`
3. Generates changelog from commit history
4. Creates GitHub Release with VSIX file attached
5. *Optional*: Publishes to VS Code Marketplace

**Usage:**
```bash
# Create and push a version tag
git tag v0.2.0
git push origin v0.2.0
```

---

## 🚀 Setup

### Required Secrets

Configure these secrets in repository settings for full functionality:

#### 1. **VSCE_PAT** (Optional - for Marketplace publishing)
   - Personal Access Token for VS Code Marketplace
   - **How to get:**
     1. Go to [Azure DevOps](https://dev.azure.com/)
     2. Create a Personal Access Token with "Marketplace (Publish)" scope
     3. Add to GitHub Secrets as `VSCE_PAT`
   - **Enable publishing:** Uncomment the publish step in `release.yml`

#### 2. **GITHUB_TOKEN** (Automatic)
   - Automatically provided by GitHub Actions
   - No configuration needed

---

## 📊 Architecture Reference

This CI/CD setup follows the same architectural patterns as the main CLI project:

### **Separation of Concerns**
```
CLI Project (Python)          →  VSCode Extension (TypeScript)
├── Linting (flake8, black)   →  ESLint
├── Type checking (mypy)      →  TypeScript compiler
├── Multi-version test (3.9+) →  Multi-version test (Node 16+)
├── Build package (pip)       →  Package extension (vsce)
├── Security scan (CodeQL)    →  Security scan (CodeQL)
└── Release automation        →  Release automation + Marketplace
```

### **Key Similarities**

1. **Multi-platform Testing**
   - CLI: Tests on Python 3.9, 3.10, 3.11, 3.12
   - Extension: Tests on Node.js 16, 18, 20 + Ubuntu/Windows/macOS

2. **Linting & Type Safety**
   - CLI: flake8 + mypy
   - Extension: ESLint + TypeScript

3. **Automated Releases**
   - CLI: PyPI publishing (optional)
   - Extension: VS Code Marketplace publishing (optional)

4. **Security First**
   - Both use CodeQL security scanning
   - Weekly automated scans
   - PR-based security checks

5. **PR Automation**
   - Automatic labeling by file changes
   - Size-based labels
   - Welcome comments with checklists

---

## 🔧 Local Testing

Run checks locally before pushing:

```bash
cd vscode-extension

# Install dependencies
npm install

# Linting
npm run lint

# Type checking
npx tsc --noEmit

# Compile
npm run compile

# Package extension
npm install -g @vscode/vsce
vsce package

# Test in VSCode
# Press F5 in VSCode to launch extension host
```

---

## 📝 Workflow Triggers

| Workflow | Trigger | Frequency |
|----------|---------|-----------|
| CI | Push, PR | On every change |
| PR Labeler | PR opened/updated | Automatic |
| CodeQL | Push, PR, Schedule | Weekly + on change |
| Release | Tag push (v*.*.*) | Manual |

---

## 🐛 Troubleshooting

### **CI Fails on npm ci**

Ensure `package-lock.json` is committed:
```bash
cd vscode-extension
npm install
git add package-lock.json
git commit -m "Add package-lock.json"
```

### **TypeScript Compilation Errors**

Check locally first:
```bash
npx tsc --noEmit
npm run compile
```

### **Extension Packaging Fails**

Verify `vsce` can package locally:
```bash
npm install -g @vscode/vsce
vsce package
```

### **Release Not Creating**

Verify tag format:
```bash
# ✅ Correct
git tag v0.1.0

# ❌ Wrong
git tag 0.1.0
git tag version-0.1.0
```

---

## 🔄 Differences from CLI Project

While following the same architectural principles, the VSCode extension CI has some key differences:

### **Technology Stack**
- **CLI**: Python, pip, pytest, SQLite
- **Extension**: TypeScript, npm, VSCode API, JSON-RPC

### **Build Process**
- **CLI**:
  - Build Python wheel/sdist
  - Run pytest with coverage
- **Extension**:
  - Compile TypeScript → JavaScript
  - Package into VSIX file
  - Multi-OS compatibility testing

### **Distribution**
- **CLI**: PyPI (Python Package Index)
- **Extension**: VS Code Marketplace + GitHub Releases

### **Testing Strategy**
- **CLI**:
  - Unit tests (187 passing)
  - Integration tests
  - Network test skipping in CI
- **Extension**:
  - Currently minimal tests (to be implemented)
  - Extension host testing (F5 debug mode)

---

## 📚 Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [VS Code Extension API](https://code.visualstudio.com/api)
- [vsce - Publishing Tool](https://code.visualstudio.com/api/working-with-extensions/publishing-extension)
- [TypeScript Documentation](https://www.typescriptlang.org/docs/)
- [CodeQL JavaScript Analysis](https://codeql.github.com/docs/codeql-language-guides/codeql-for-javascript/)

---

## 🎯 Next Steps

1. **Enable Marketplace Publishing**
   - Get `VSCE_PAT` from Azure DevOps
   - Add to GitHub Secrets
   - Uncomment publish step in `release.yml`

2. **Add Extension Tests**
   - Implement VSCode extension tests
   - Update CI to run tests
   - Add coverage reporting

3. **Add More Labels**
   - Create custom labels in GitHub
   - Update `labeler.yml` with more rules

4. **Branch Protection**
   - Require CI checks to pass
   - Require PR reviews
   - Enable status checks

---

## 💡 Best Practices

### **Commit Message Convention**
```bash
# Follow conventional commits
feat: Add new command
fix: Resolve RPC connection issue
docs: Update setup guide
chore: Update dependencies
```

### **Version Tagging**
```bash
# Semantic versioning: MAJOR.MINOR.PATCH
v0.1.0  # Initial release
v0.1.1  # Bug fix
v0.2.0  # New feature
v1.0.0  # Major release
```

### **PR Size Guidelines**
- **XS (≤10 lines)**: Typo fixes, small docs changes
- **S (≤100 lines)**: Bug fixes, small features
- **M (≤500 lines)**: Medium features, refactoring
- **L (≤1000 lines)**: Large features
- **XL (>1000 lines)**: Consider breaking into smaller PRs

---

## 🔗 Related Documentation

- [Main CLI CI/CD](../../.github/GITHUB_ACTIONS.md)
- [Extension Setup Guide](../SETUP.md)
- [Extension README](../README.md)
