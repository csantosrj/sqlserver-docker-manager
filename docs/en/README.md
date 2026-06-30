# SQL Server Docker Manager

Python/PySide6 desktop application to manage backups, restores and database browsing for SQL Server running in Docker.

## Available languages

- Portuguese Portugal
- Portuguese Brazil
- English
- Spanish
- French

The language can be changed in **Settings > Interface > Language**.

## Features

- Restore `.bak` backups;
- Backup existing databases;
- Browse SQL Server databases;
- Local settings;
- Dark Premium and Light Professional themes;
- Real-time logs;
- Password kept in session or saved locally by explicit user choice.

## Requirements

- Python 3.10+ for development mode;
- Docker installed;
- SQL Server container running;
- `sqlcmd` available inside the container;
- Permission to run `docker`.

## Run in development mode

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

On Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Security

By default, the password is kept only in memory while the application is open.
If the user enables the save-password option, it is stored locally at the user's own risk.

## Documentation

- [Build](BUILD.md)
- [Manual](MANUAL.md)
