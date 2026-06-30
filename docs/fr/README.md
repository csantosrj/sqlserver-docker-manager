# SQL Server Docker Manager

Application desktop en Python/PySide6 pour gérer les sauvegardes, restaurations et la consultation de bases SQL Server dans Docker.

## Langues disponibles

- Portugais Portugal
- Portugais Brésil
- Anglais
- Espagnol
- Français

La langue peut être changée dans **Settings > Interface > Langue**.

## Fonctionnalités

- Restaurer des sauvegardes `.bak`;
- Sauvegarder des bases existantes;
- Consulter les bases SQL Server;
- Paramètres locaux;
- Thèmes Dark Premium et Light Professional;
- Logs en temps réel;
- Mot de passe en session ou enregistré localement par choix explicite de l’utilisateur.

## Prérequis

- Python 3.10+ pour le mode développement;
- Docker installé;
- Conteneur SQL Server en cours d’exécution;
- `sqlcmd` disponible dans le conteneur;
- Permission d’exécuter `docker`.

## Exécuter en mode développement

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Sous Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Sécurité

Par défaut, le mot de passe reste uniquement en mémoire pendant que l’application est ouverte.
Si l’utilisateur active l’option d’enregistrement du mot de passe, il sera stocké localement sous sa propre responsabilité.

## Documentation

- [Build](BUILD.md)
- [Manual](MANUAL.md)
