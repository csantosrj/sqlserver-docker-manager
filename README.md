# SQL Server Docker Manager

Desktop app in Python/PySide6 for SQL Server backup, restore and database browsing inside Docker.

## Languages / Idiomas / Langues

- [Português Portugal](docs/pt-PT/README.md)
- [Português Brasil](docs/pt-BR/README.md)
- [English](docs/en/README.md)
- [Español](docs/es/README.md)
- [Français](docs/fr/README.md)

## Main features

- Restore `.bak` backups;
- Create `.bak` backups;
- Browse databases;
- Dark and light themes;
- Runtime language selection;
- Real-time logs;
- Local settings.

## Quick start

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

## Build and manual

- [Build Guide EN](docs/en/BUILD.md)
- [User Manual EN](docs/en/MANUAL.md)
- [Guia de Build PT-PT](docs/pt-PT/BUILD.md)
- [Manual PT-PT](docs/pt-PT/MANUAL.md)


## Recommended backup volume mapping

For a smoother experience, it is recommended to map a folder from your host machine to the SQL Server backup directory inside the container.

By default, this tool expects backup files inside the container at:

```text
/var/opt/mssql/backup
```

If you map this directory to a local folder, you can simply copy `.bak` files to your host folder and they will immediately be available inside the container.

### Example with Docker Compose

```yaml
services:
  sqlserver:
    image: mcr.microsoft.com/mssql/server:2022-latest
    container_name: okapa-sqlserver
    environment:
      ACCEPT_EULA: "Y"
      MSSQL_SA_PASSWORD: "YourStrongPasswordHere"
    ports:
      - "1433:1433"
    volumes:
      - sqlserver_data:/var/opt/mssql/data
      - ./backups:/var/opt/mssql/backup

volumes:
  sqlserver_data:
```

With this configuration:

```text
./backups
```

on your host machine is mapped to:

```text
/var/opt/mssql/backup
```

inside the SQL Server container.

### Why this is useful

This makes backup and restore operations much easier:

* To restore a database, copy the `.bak` file to the local `backups` folder.
* The file will automatically appear inside the container.
* The application can list and restore it without needing `docker cp`.
* New backups created by the application will also appear in the local `backups` folder.

### Example

If you place this file on your host:

```text
./backups/MyDatabase.bak
```

the SQL Server container will see it as:

```text
/var/opt/mssql/backup/MyDatabase.bak
```

Then, in SQL Server Docker Manager, open **Restore**, click **Refresh backups**, and select `MyDatabase.bak`.

### Notes

Make sure the folder exists before starting the container:

```bash
mkdir -p backups
```

On Linux, if SQL Server cannot read or write backup files, check folder permissions.

For local development, you can usually fix permissions with:

```bash
chmod -R 777 backups
```

For production environments, use more restrictive permissions according to your security requirements.
