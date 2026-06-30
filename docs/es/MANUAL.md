# Manual de Usuario

## Primer paso: Ajustes

Abra **Settings** y configure:

- Contenedor predeterminado;
- Usuario SQL;
- Contraseña;
- Directorio de copias;
- Directorio de datos;
- Idioma;
- Tema.

Después haga clic en **Probar conexión**.

## Databases

Use este menú para consultar las bases disponibles en el contenedor configurado.

1. Abra **Databases**.
2. Haga clic en **Actualizar bases**.
3. Revise nombre, estado, recovery, collation, compatibilidad y tamaño.

## Backup

1. Abra **Backup**.
2. Haga clic en **Actualizar bases**.
3. Elija la base origen.
4. Genere o escriba el nombre del `.bak`.
5. Haga clic en **Crear copia**.
6. Siga los logs.

La copia se crea en el directorio configurado, normalmente `/var/opt/mssql/backup`.

## Restore

1. Abra **Restore**.
2. Haga clic en **Actualizar copias**.
3. Elija el `.bak`.
4. Informe la base destino.
5. Haga clic en **Restaurar copia**.
6. Confirme si la base destino ya existe.

Para probar con seguridad, restaure con otro nombre, por ejemplo `MiBase_Restored`.

## Logs

El área de logs muestra progreso y errores técnicos. Use **Copiar log** para copiar todo.

## Seguridad

Use con cuidado en producción. La confirmación evita sobrescribir una base real por error.
