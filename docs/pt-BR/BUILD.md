# Guia de Build

Este documento explica como gerar pacotes executáveis do SQL Server Docker Manager.

## Regra principal

O build deve ser feito no sistema operacional alvo:

| Alvo | Onde gerar |
|---|---|
| Linux | Linux ou WSL |
| Windows | Windows |
| macOS | macOS |

## Preparar ambiente

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pyinstaller
```

No Windows:

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

- Use `--onedir` inicialmente. É mais estável com PySide6.
- Docker não é incluído no pacote.
- O usuário final precisa ter Docker e o container SQL Server configurados.
