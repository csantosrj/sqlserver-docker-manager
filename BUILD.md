# Build Guide

This document explains how to generate executable packages for SQL Server Docker Manager.

## Main rule

The build must be created on the target operating system:

| Target  | Where to build |
| ------- | -------------- |
| Linux   | Linux or WSL   |
| Windows | Windows        |
| macOS   | macOS          |

## Prepare the environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pyinstaller
```

On Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install pyinstaller
```

## Linux

```bash
pyinstaller \
  --noconfirm \
  --clean \
  --onedir \
  --windowed \
  --name SQLServerDockerManager \
  --add-data "assets:assets" \
  --icon assets/app_icon.png \
  main.py
```

Output:

```text
dist/SQLServerDockerManager/
```

## Windows

```powershell
pyinstaller `
  --noconfirm `
  --clean `
  --onedir `
  --windowed `
  --name SQLServerDockerManager `
  --add-data "assets;assets" `
  --icon assets/app_icon.ico `
  main.py
```

Output:

```text
dist/SQLServerDockerManager/SQLServerDockerManager.exe
```

## macOS

```bash
pyinstaller \
  --noconfirm \
  --clean \
  --onedir \
  --windowed \
  --name SQLServerDockerManager \
  --add-data "assets:assets" \
  --icon assets/app_icon.icns \
  main.py
```

## Notes

* Use `--onedir` in the first stage. It is more stable with PySide6.
* Docker is not included in the package.
* The end user must have Docker installed and the SQL Server container configured.
