# Installing Multiple Python Versions

---

## Table of Contents

1. [Using pyenv on Linux / CloudShell](#1-using-pyenv-on-linux--cloudshell)
2. [Using pyenv-win on Windows](#2-using-pyenv-win-on-windows)
3. [Common pyenv Commands - Linux and Windows](#3-common-pyenv-commands---linux-and-windows)
4. [Practical Example - Different Python per Project](#4-practical-example---different-python-per-project)
5. [For Lambda Layer Building](#5-for-lambda-layer-building)

---

## 1. Using pyenv on Linux / CloudShell

### Step 1 - Install Dependencies

```bash
sudo yum install -y \
  gcc \
  zlib-devel \
  bzip2 \
  bzip2-devel \
  readline-devel \
  sqlite \
  sqlite-devel \
  openssl-devel \
  xz \
  xz-devel \
  libffi-devel \
  git
```

### Step 2 - Install pyenv

```bash
curl https://pyenv.run | bash
```

### Step 3 - Add pyenv to Shell

```bash
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc

# Reload
source ~/.bashrc
```

### Step 4 - Verify Installation

```bash
pyenv --version
```

### Step 5 - Install Python Versions

```bash
# See all available versions
pyenv install --list

# Install specific versions
pyenv install 3.12.0
pyenv install 3.13.0
pyenv install 3.14.0
```

---

## 2. Using pyenv-win on Windows

pyenv does not work on Windows natively. The Windows equivalent is **pyenv-win**.

### Step 1 - Install pyenv-win via PowerShell

Open PowerShell as Administrator and run:

```powershell
Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/pyenv-win/pyenv-win/master/pyenv-win/install-pyenv-win.ps1" -OutFile "./install-pyenv-win.ps1"; &"./install-pyenv-win.ps1"
```

### Step 2 - Restart PowerShell

Close and reopen PowerShell after installation.

### Step 3 - Verify Installation

```powershell
pyenv --version
```

### Step 4 - Install Python Versions

```powershell
# See all available versions
pyenv install --list

# Install specific versions
pyenv install 3.12.0
pyenv install 3.13.0
pyenv install 3.14.0
```

### Step 5 - Add to PATH (if pyenv commands not found)

```powershell
# Add these to your system environment variables
[System.Environment]::SetEnvironmentVariable('PYENV', "$env:USERPROFILE\.pyenv\pyenv-win", 'User')
[System.Environment]::SetEnvironmentVariable('PYENV_HOME', "$env:USERPROFILE\.pyenv\pyenv-win", 'User')
$path = [System.Environment]::GetEnvironmentVariable('PATH', 'User')
[System.Environment]::SetEnvironmentVariable('PATH', "$env:USERPROFILE\.pyenv\pyenv-win\bin;$env:USERPROFILE\.pyenv\pyenv-win\shims;$path", 'User')
```

Restart PowerShell again after this.

---

## 3. Common pyenv Commands - Linux and Windows

These commands work the same on both Linux (pyenv) and Windows (pyenv-win):

```bash
# List all installed versions
pyenv versions

# Check currently active version
pyenv version

# Set global default version (applies everywhere)
pyenv global 3.13.0

# Set version only for current folder/project
pyenv local 3.12.0

# Set version only for current terminal session
pyenv shell 3.14.0

# Verify which Python is active
python --version
```

---

**How pyenv version switching works:**

```
System Python:  /usr/bin/python3 (Linux) or C:\Python313 (Windows)  ← untouched
pyenv Python:   ~/.pyenv/shims/python (Linux)
                %USERPROFILE%\.pyenv\shims\python (Windows)

When you run "python":
        ↓
pyenv checks in this order:
1. pyenv shell  → current terminal session
2. pyenv local  → .python-version file in current folder
3. pyenv global → default version set globally
4. System Python → fallback
```

---

## 4. Practical Example - Different Python per Project

```bash
# Project 1 needs Python 3.12
cd ~/project1          # Linux
cd C:\projects\project1  # Windows

pyenv local 3.12.0
python --version   # Python 3.12.0

# Project 2 needs Python 3.13
cd ~/project2          # Linux
cd C:\projects\project2  # Windows

pyenv local 3.13.0
python --version   # Python 3.13.0
```

Each folder gets a `.python-version` file created automatically by `pyenv local`:

```bash
cat .python-version
# 3.13.0
```

---

## 5. For Lambda Layer Building

Always match the Python version of your layer to your Lambda runtime.

**Linux / CloudShell:**

```bash
# Switch to Python 3.12 to build layer for Python 3.12 Lambda
pyenv shell 3.12.0
mkdir python
pip install pandas -t python/
zip -r pandas-layer-py312.zip python/

# Switch to Python 3.13 to build layer for Python 3.13 Lambda
pyenv shell 3.13.0
rm -rf python
mkdir python
pip install pandas -t python/
zip -r pandas-layer-py313.zip python/
```

**Windows:**

```powershell
# Switch to Python 3.12
pyenv shell 3.12.0
mkdir python
pip install pandas -t python/
Compress-Archive -Path python -DestinationPath pandas-layer-py312.zip

# Switch to Python 3.13
pyenv shell 3.13.0
Remove-Item -Recurse -Force python
mkdir python
pip install pandas -t python/
Compress-Archive -Path python -DestinationPath pandas-layer-py313.zip
```

> **Important for Windows users:** Even if you build the layer on Windows with the correct Python version, the pandas/numpy binaries will still be Windows specific and will fail on Lambda. Always build Lambda layers on Linux or CloudShell to get Linux compatible binaries.
