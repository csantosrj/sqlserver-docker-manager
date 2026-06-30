# Build Guide

This document explains how to build executable packages for SQL Server Docker Manager.

## Main rule

Build on the target operating system:

| Target | Build on |
|---|---|
| Linux | Linux or WSL |
| Windows | Windows |
| macOS | macOS |

## Prepare environment

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

- Use `--onedir` first. It is more stable with PySide6.
- Docker is not included in the package.
- The end user must already have Docker and the SQL Server container configured.
