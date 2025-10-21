# PyPI Publishing Guide

## Prerequisites

1. PyPI account: https://pypi.org/account/register/
2. API token from https://pypi.org/manage/account/token/

## One-Time Setup

```bash
# Create ~/.pypirc (or %USERPROFILE%\.pypirc on Windows)
```

Add this content:
```ini
[pypi]
username = __token__
password = pypi-YOUR_TOKEN_HERE
```

## Publishing Steps

### 1. Clean previous builds (if any)
```bash
rm -r dist/ build/ *.egg-info
```

### 2. Build distribution packages
```bash
python -m build
```

This creates:
- `dist/async_mariadb_connector-0.1.0.tar.gz` (source distribution)
- `dist/async_mariadb_connector-0.1.0-py3-none-any.whl` (wheel)

### 3. Check packages
```bash
twine check dist/*
```

Both should show `PASSED`.

### 4. Test on TestPyPI (optional but recommended)

```bash
# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Test install
pip install --index-url https://test.pypi.org/simple/ async-mariadb-connector
```

### 5. Upload to PyPI

```bash
twine upload dist/*
```

Enter your PyPI credentials when prompted (or use API token from ~/.pypirc).

### 6. Verify upload

Visit: https://pypi.org/project/async-mariadb-connector/

### 7. Test installation

```bash
pip install async-mariadb-connector
```

### 8. Create git tag

```bash
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0
```

### 9. Create GitHub Release

Go to: https://github.com/chanikkyasaai/async-mariadb-ml/releases/new

- Tag: `v0.1.0`
- Title: `v0.1.0 - Initial Release`
- Description: Copy from CHANGELOG.md

## Troubleshooting

**Error: File already exists**
- Package version 0.1.0 is already on PyPI
- Increment version in `pyproject.toml` and rebuild

**Error: Invalid credentials**
- Check ~/.pypirc has correct API token
- Or use: `twine upload dist/* -u __token__ -p pypi-YOUR_TOKEN`

**Error: Package name taken**
- Change `name` in `pyproject.toml`
- Rebuild and re-upload

## Post-Publication Checklist

- [ ] Update README.md badges to live PyPI
- [ ] Update installation instructions
- [ ] Announce on LinkedIn/Twitter
- [ ] Submit to LangChain docs (Integration Track requirement)
