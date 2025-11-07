# GitHub Actions CI/CD

This repository uses GitHub Actions for continuous integration and deployment.

## 🔄 Workflows

### 1. **CI Pipeline** (`ci.yml`)

Runs on every push and pull request to `main` and `develop` branches.

**Jobs:**
- **Test**: Run unit tests on Python 3.9, 3.10, 3.11, and 3.12
  - Executes pytest with coverage reporting
  - Uploads coverage to Codecov
- **Lint**: Code quality checks
  - flake8 for code style
  - black for formatting
  - isort for import ordering
  - mypy for type checking
- **Integration**: Run integration tests
- **Build**: Build Python package

**Badges:**
```markdown
![CI](https://github.com/xshii/llmcli/workflows/CI/badge.svg)
![Python Version](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue)
[![codecov](https://codecov.io/gh/xshii/llmcli/branch/main/graph/badge.svg)](https://codecov.io/gh/xshii/llmcli)
```

### 2. **PR Labeler** (`pr-labeler.yml`)

Automatically labels pull requests based on:
- **File changes**: Labels areas like `area: cli`, `area: llm`, etc.
- **PR size**: Labels size from `size/XS` to `size/XL`
- **Auto-comment**: Adds welcome comment with checklist

### 3. **CodeQL Security Scan** (`codeql.yml`)

Security vulnerability scanning:
- Runs on push to main/develop
- Weekly scheduled scan (Mondays 6 AM UTC)
- Analyzes Python code for security issues

### 4. **Release** (`release.yml`)

Automated release creation:
- Triggers on version tags (e.g., `v1.0.0`)
- Builds Python package
- Generates changelog from commits
- Creates GitHub release with artifacts
- Optional: Publish to PyPI (commented out)

**Usage:**
```bash
# Create and push a tag
git tag v1.0.0
git push origin v1.0.0
```

### 5. **Dependabot** (`dependabot.yml`)

Automated dependency updates:
- Weekly checks for Python packages
- Weekly checks for GitHub Actions versions
- Auto-creates PRs for updates

## 🚀 Setup

### Required Secrets

For full functionality, configure these secrets in repository settings:

1. **CODECOV_TOKEN** (Optional)
   - For coverage reporting
   - Get from: https://codecov.io

2. **PYPI_API_TOKEN** (Optional)
   - For publishing to PyPI
   - Get from: https://pypi.org/manage/account/token/

### Branch Protection

Recommended settings for `main` branch:
- ✅ Require pull request reviews
- ✅ Require status checks (CI tests)
- ✅ Require branches to be up to date
- ✅ Include administrators

## 📊 Status Badges

Add these badges to your README.md:

```markdown
[![CI](https://github.com/xshii/llmcli/workflows/CI/badge.svg)](https://github.com/xshii/llmcli/actions/workflows/ci.yml)
[![CodeQL](https://github.com/xshii/llmcli/workflows/CodeQL%20Security%20Scan/badge.svg)](https://github.com/xshii/llmcli/actions/workflows/codeql.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
```

## 🔧 Local Testing

Run checks locally before pushing:

```bash
# Unit tests
pytest tests/unit/ -v --cov=aicode

# Linting
flake8 aicode
black --check aicode tests
isort --check-only aicode tests
mypy aicode

# Integration tests
PYTHONPATH=$PWD pytest tests/integration/ -v
```

## 📝 Workflow Triggers

| Workflow | Trigger | Frequency |
|----------|---------|-----------|
| CI | Push, PR | On every change |
| PR Labeler | PR opened/updated | Automatic |
| CodeQL | Push, PR, Schedule | Weekly + on change |
| Release | Tag push | Manual (v*.*.*) |
| Dependabot | Schedule | Weekly (Monday) |

## 🐛 Troubleshooting

### CI Fails on Import Errors

Ensure all dependencies are in `requirements.txt`:
```bash
pip freeze > requirements.txt
```

### Coverage Not Uploading

Check that `CODECOV_TOKEN` is set in repository secrets.

### Release Not Creating

Verify tag format: `v1.0.0` (must start with 'v')

## 🔄 Updating Workflows

When modifying workflows:
1. Test locally if possible
2. Use `act` tool for local GitHub Actions testing
3. Create PR to test in branch protection
4. Merge when green ✅

## 📚 Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Workflow Syntax](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)
- [Security Best Practices](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)
