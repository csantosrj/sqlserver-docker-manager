# User Manual

## First step: Settings

Open **Settings** and configure:

- Default container;
- SQL user;
- Password;
- Backup directory;
- Data directory;
- Language;
- Theme.

Then click **Test connection**.

## Databases

Use this menu to view the databases available in the configured container.

1. Open **Databases**.
2. Click **Refresh databases**.
3. Check the name, status, recovery model, collation, compatibility level, and size.

## Backup

1. Open **Backup**.
2. Click **Refresh databases**.
3. Select the source database.
4. Generate or enter the `.bak` file name.
5. Click **Create backup**.
6. Follow the logs.

The backup is created in the configured directory, usually `/var/opt/mssql/backup`.

## Restore

1. Open **Restore**.
2. Click **Refresh backups**.
3. Select the `.bak` file.
4. Enter the destination database name.
5. Click **Restore backup**.
6. Confirm if the destination database already exists.

To test safely, restore using a different name, for example `MyDatabase_Restored`.

## Logs

The log area shows progress and technical errors. Use **Copy log** to copy everything.

## Security

Use carefully in production. Overwrite confirmation helps prevent accidentally restoring over a real database.