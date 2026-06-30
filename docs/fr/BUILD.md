# Guide de Build

Ce document explique comment générer les exécutables de SQL Server Docker Manager.

## Règle principale

Le build doit être fait sur le système cible:

| Cible | Où générer |
|---|---|
| Linux | Linux ou WSL |
| Windows | Windows |
| macOS | macOS |

## Préparer l’environnement

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pyinstaller
```

Sous Windows:

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

- Utilisez d’abord `--onedir`. C’est plus stable avec PySide6.
- Docker n’est pas inclus dans le paquet.
- L’utilisateur final doit avoir Docker et le conteneur SQL Server configurés.
