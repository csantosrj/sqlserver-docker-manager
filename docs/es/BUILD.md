# Guía de Build

Este documento explica cómo generar paquetes ejecutables de SQL Server Docker Manager.

## Regla principal

El build debe hacerse en el sistema operativo destino:

| Destino | Dónde generar |
|---|---|
| Linux | Linux o WSL |
| Windows | Windows |
| macOS | macOS |

## Preparar entorno

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pyinstaller
```

En Windows:

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

## Notas

- Usa `--onedir` al principio. Es más estable con PySide6.
- Docker no se incluye en el paquete.
- El usuario final debe tener Docker y el contenedor SQL Server configurados.
