# Development Guide

## Python Version Management with pyenv

### Installation

**macOS/Linux:**
```bash
# Install pyenv
curl https://pyenv.run | bash

# Add to your shell profile (~/.bashrc, ~/.zshrc, etc.)
export PYENV_ROOT="$HOME/.pyenv"
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
```

**Windows (using pyenv-win):**
```powershell
# Install pyenv-win via PowerShell
Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/pyenv-win/pyenv-win/master/pyenv-win/install-pyenv-win.ps1" -OutFile "./install-pyenv-win.ps1"; &"./install-pyenv-win.ps1"

# Add to your PowerShell profile
[Environment]::SetEnvironmentVariable("PYENV", "$env:USERPROFILE\.pyenv\pyenv-win\", "User")
[Environment]::SetEnvironmentVariable("path", "$env:USERPROFILE\.pyenv\pyenv-win\bin;$env:USERPROFILE\.pyenv\pyenv-win\shims;$env:Path", "User")
```

### Installing Python Versions

Install all supported Python versions (3.9-3.13):

```bash
# List available versions
pyenv install --list

# Install required versions
pyenv install 3.9.18
pyenv install 3.10.13
pyenv install 3.11.8
pyenv install 3.12.2
pyenv install 3.13.0

# Set global versions
pyenv global 3.11.8 3.10.13 3.9.18 3.12.2 3.13.0

# Verify installation
pyenv versions
```

## Testing with tox

### Installation

```bash
pip install tox
```

### Available Environments

- `tox -e py39` - Test with Python 3.9
- `tox -e py310` - Test with Python 3.10  
- `tox -e py311` - Test with Python 3.11
- `tox -e py312` - Test with Python 3.12
- `tox -e py313` - Test with Python 3.13
- `tox -e py` - Test with all Python versions
- `tox -e lint` - Run code quality checks (black, flake8)
- `tox -e type` - Run type checking (mypy)
- `tox -e format` - Apply code formatting

### Running Tests

```bash
# Run tests on all supported Python versions
tox

# Run tests on a specific version
tox -e py311

# Run tests with specific pytest arguments
tox -e py311 -- -xvs tests/test_decorators.py

# Run code quality checks
tox -e lint

# Run type checking
tox -e type

# Apply code formatting
tox -e format
```

### Local Development Workflow

1. **Set up Python versions:**
   ```bash
   pyenv install 3.9.18 3.10.13 3.11.8 3.12.2 3.13.0
   pyenv global 3.11.8  # Use 3.11 as default for development
   ```

2. **Install development dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   pip install tox
   ```

3. **Run local tests:**
   ```bash
   # Quick test with current Python version
   pytest
   
   # Full compatibility test
   tox
   ```

4. **Code quality checks:**
   ```bash
   # Check formatting and linting
   tox -e lint
   
   # Type checking
   tox -e type
   ```

5. **Apply formatting:**
   ```bash
   tox -e format
   ```

## GitHub Actions Integration

The CI/CD pipeline automatically runs tests on all supported Python versions (3.9-3.13) across multiple operating systems (Linux, Windows, macOS).

- **Test Matrix**: 5 Python versions × 3 operating systems = 15 test environments
- **Code Quality**: Runs on Ubuntu with Python 3.11
- **Automatic Publishing**: Publishes to PyPI on release tags

## Troubleshooting

### Common pyenv Issues

**"Python version not found":**
```bash
# Update pyenv
pyenv update

# Check available versions
pyenv install --list | grep 3.13
```

**Build dependencies missing (Linux/macOS):**
```bash
# Ubuntu/Debian
sudo apt-get install build-essential libssl-dev zlib1g-dev libbz2-dev \
libreadline-dev libsqlite3-dev wget curl llvm libncursesw5-dev xz-utils \
tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev

# macOS (with Homebrew)
brew install openssl readline sqlite3 xz zlib tcl-tk
```

### Common tox Issues

**"Interpreter not found":**
Make sure the Python version is installed via pyenv and available in your PATH.

**Slow first run:**
tox creates virtual environments on first run, which takes time. Subsequent runs are faster.

**Cache issues:**
```bash
# Clean tox cache
tox --recreate

# Clean all tox environments
tox -a | xargs -I {} tox -e {} --recreate
```