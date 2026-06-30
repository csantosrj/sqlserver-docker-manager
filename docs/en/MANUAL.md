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

Use this menu to view databases available in the configured container.

1. Open **Databases**.
2. Click **Refresh databases**.
3. Check name, status, recovery, collation, compatibility and size.

## Backup

1. Open **Backup**.
2. Click **Refresh databases**.
3. Choose the source database.
4. Generate or type the `.bak` filename.
5. Click **Create backup**.
6. Follow the logs.

The backup is created in the configured directory, usually `/var/opt/mssql/backup`.

## Restore

1. Open **Restore**.
2. Click **Refresh backups**.
3. Choose the `.bak`.
4. Enter the target database.
5. Click **Restore backup**.
6. Confirm if the target database already exists.

For safe testing, restore using another name, for example `MyDatabase_Restored`.

## Logs

The log area shows progress and technical errors. Use **Copy log** to copy everything.

## Security

Use carefully in production. Overwrite confirmation helps avoid replacing a real database by mistake.
