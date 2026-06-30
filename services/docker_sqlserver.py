import re
import shlex
import subprocess
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, List, Optional


DEFAULT_BACKUP_DIR = "/var/opt/mssql/backup"
DEFAULT_DATA_DIR = "/var/opt/mssql/data"


@dataclass
class DockerContainer:
    name: str
    image: str
    status: str


@dataclass
class SqlFileInfo:
    logical_name: str
    physical_name: str
    file_type: str


@dataclass
class DatabaseInfo:
    name: str
    collation_name: str
    state_desc: str


@dataclass
class DatabaseDetails:
    name: str
    state_desc: str
    recovery_model_desc: str
    collation_name: str
    compatibility_level: int
    size_mb: float


class DockerSqlServerError(Exception):
    pass


class DockerSqlServerService:
    """Serviço responsável por conversar com Docker e SQL Server."""

    def __init__(
        self,
        backup_dir: str = DEFAULT_BACKUP_DIR,
        data_dir: str = DEFAULT_DATA_DIR,
    ):
        self.backup_dir = backup_dir
        self.data_dir = data_dir

    # ------------------------------------------------------------------
    # Docker
    # ------------------------------------------------------------------

    def list_sqlserver_containers(self) -> List[DockerContainer]:
        result = subprocess.run(
            [
                "docker",
                "ps",
                "--format",
                "{{.Names}}\t{{.Image}}\t{{.Status}}",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        if result.returncode != 0:
            raise DockerSqlServerError(result.stderr.strip() or result.stdout.strip())

        containers: List[DockerContainer] = []

        for line in result.stdout.splitlines():
            parts = line.split("\t")
            if len(parts) < 3:
                continue

            name, image, status = parts[0], parts[1], parts[2]
            text = f"{name} {image}".lower()

            if "mssql" in text or "sqlserver" in text or "sql-server" in text:
                containers.append(DockerContainer(name=name, image=image, status=status))

        return containers

    def list_backups(self, container_name: str) -> List[str]:
        safe_dir = shlex.quote(self.backup_dir)

        bash_command = (
            f"shopt -s nullglob; "
            f"for f in {safe_dir}/*.bak {safe_dir}/*.BAK; do "
            f"basename \"$f\"; "
            f"done | sort -u"
        )

        result = self._docker_exec_bash(container_name, bash_command)

        return [
            line.strip()
            for line in result.splitlines()
            if line.strip().lower().endswith(".bak")
        ]

    def backup_exists(self, container_name: str, backup_file: str) -> bool:
        self._validate_backup_filename(backup_file)

        full_path = f"{self.backup_dir}/{backup_file}"
        bash_command = f"test -f {shlex.quote(full_path)}"

        result = subprocess.run(
            ["docker", "exec", container_name, "bash", "-lc", bash_command],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        return result.returncode == 0

    # ------------------------------------------------------------------
    # Databases
    # ------------------------------------------------------------------

    def list_databases(
        self,
        container_name: str,
        sql_user: str,
        sql_password: str,
    ) -> List[str]:
        self._validate_credentials(sql_user, sql_password)

        sql = """
SET NOCOUNT ON;

SELECT name
FROM sys.databases
WHERE database_id > 4
  AND state_desc = 'ONLINE'
ORDER BY name;
"""

        output = self._run_sql_capture(
            container_name=container_name,
            sql_user=sql_user,
            sql_password=sql_password,
            sql=sql,
            extra_sqlcmd_args=["-W", "-s", "|", "-h", "-1"],
        )

        databases: List[str] = []

        for line in output.splitlines():
            name = line.strip()
            if name and "|" not in name and not name.startswith("Changed database"):
                databases.append(name)

        return databases

    def list_database_details(
        self,
        container_name: str,
        sql_user: str,
        sql_password: str,
    ) -> List[DatabaseDetails]:
        """
        Lista bases de utilizador com informações úteis para o ecrã Databases.

        Mostra apenas database_id > 4 para ocultar master, model, msdb e tempdb.
        """
        self._validate_credentials(sql_user, sql_password)

        sql = """
SET NOCOUNT ON;

SELECT
    d.name,
    d.state_desc,
    d.recovery_model_desc,
    ISNULL(d.collation_name, ''),
    d.compatibility_level,
    CAST(ISNULL(SUM(mf.size), 0) * 8.0 / 1024.0 AS decimal(18,2)) AS size_mb
FROM sys.databases d
LEFT JOIN sys.master_files mf
    ON d.database_id = mf.database_id
WHERE d.database_id > 4
GROUP BY
    d.name,
    d.state_desc,
    d.recovery_model_desc,
    d.collation_name,
    d.compatibility_level
ORDER BY d.name;
"""

        output = self._run_sql_capture(
            container_name=container_name,
            sql_user=sql_user,
            sql_password=sql_password,
            sql=sql,
            extra_sqlcmd_args=["-W", "-s", "|", "-h", "-1"],
        )

        databases: List[DatabaseDetails] = []

        for line in output.splitlines():
            line = line.strip()

            if not line or "|" not in line:
                continue

            parts = [part.strip() for part in line.split("|")]

            if len(parts) < 6:
                continue

            try:
                compatibility_level = int(parts[4])
            except ValueError:
                compatibility_level = 0

            try:
                size_mb = float(parts[5].replace(",", "."))
            except ValueError:
                size_mb = 0.0

            databases.append(
                DatabaseDetails(
                    name=parts[0],
                    state_desc=parts[1],
                    recovery_model_desc=parts[2],
                    collation_name=parts[3],
                    compatibility_level=compatibility_level,
                    size_mb=size_mb,
                )
            )

        return databases

    def get_database_info(
        self,
        container_name: str,
        sql_user: str,
        sql_password: str,
        database_name: str,
    ) -> Optional[DatabaseInfo]:
        self._validate_credentials(sql_user, sql_password)
        self._validate_database_name(database_name)

        sql = f"""
SET NOCOUNT ON;

SELECT
    name,
    ISNULL(collation_name, ''),
    state_desc
FROM sys.databases
WHERE name = {self._sql_string(database_name)};
"""

        output = self._run_sql_capture(
            container_name=container_name,
            sql_user=sql_user,
            sql_password=sql_password,
            sql=sql,
            extra_sqlcmd_args=["-W", "-s", "|", "-h", "-1"],
        )

        for line in output.splitlines():
            line = line.strip()

            if not line or "|" not in line:
                continue

            parts = [part.strip() for part in line.split("|")]

            if len(parts) < 3:
                continue

            name = parts[0]
            collation_name = parts[1]
            state_desc = parts[2]

            if name == database_name:
                return DatabaseInfo(
                    name=name,
                    collation_name=collation_name,
                    state_desc=state_desc,
                )

        return None

    # ------------------------------------------------------------------
    # Restore
    # ------------------------------------------------------------------

    def restore_filelistonly(
        self,
        container_name: str,
        sql_user: str,
        sql_password: str,
        backup_file: str,
    ) -> List[SqlFileInfo]:
        self._validate_credentials(sql_user, sql_password)
        self._validate_backup_filename(backup_file)

        backup_path = f"{self.backup_dir}/{backup_file}"

        sql = f"""
RESTORE FILELISTONLY
FROM DISK = {self._sql_string(backup_path)};
"""

        output = self._run_sql_capture(
            container_name=container_name,
            sql_user=sql_user,
            sql_password=sql_password,
            sql=sql,
            extra_sqlcmd_args=["-W", "-s", "|", "-h", "-1"],
        )

        files: List[SqlFileInfo] = []

        for line in output.splitlines():
            line = line.strip()

            if not line or "|" not in line:
                continue

            parts = [p.strip() for p in line.split("|")]

            if len(parts) < 3:
                continue

            logical_name = parts[0]
            physical_name = parts[1]
            file_type = parts[2]

            if logical_name and file_type in ("D", "L", "S", "F"):
                files.append(
                    SqlFileInfo(
                        logical_name=logical_name,
                        physical_name=physical_name,
                        file_type=file_type,
                    )
                )

        if not files:
            raise DockerSqlServerError(
                "Não foi possível interpretar o resultado do RESTORE FILELISTONLY.\n\n"
                f"Saída técnica:\n{output}"
            )

        return files

    def build_restore_sql(
        self,
        backup_file: str,
        database_name: str,
        file_infos: List[SqlFileInfo],
    ) -> str:
        self._validate_backup_filename(backup_file)
        self._validate_database_name(database_name)

        backup_path = f"{self.backup_dir}/{backup_file}"
        db_identifier = self._sql_identifier(database_name)
        db_string = self._sql_string(database_name)

        move_lines = []
        data_count = 0
        log_count = 0

        safe_file_base = self._safe_file_base(database_name)

        for file_info in file_infos:
            if file_info.file_type == "D":
                data_count += 1
                target_file = f"{safe_file_base}.mdf" if data_count == 1 else f"{safe_file_base}_{data_count}.ndf"
            elif file_info.file_type == "L":
                log_count += 1
                target_file = f"{safe_file_base}_log.ldf" if log_count == 1 else f"{safe_file_base}_log_{log_count}.ldf"
            else:
                raise DockerSqlServerError(
                    f"Tipo de ficheiro não suportado nesta versão: {file_info.file_type}. "
                    f"Logical name: {file_info.logical_name}"
                )

            target_path = f"{self.data_dir}/{target_file}"

            move_lines.append(
                f"MOVE {self._sql_string(file_info.logical_name)} "
                f"TO {self._sql_string(target_path)}"
            )

        if data_count == 0:
            raise DockerSqlServerError("O backup não contém ficheiro de dados.")
        if log_count == 0:
            raise DockerSqlServerError("O backup não contém ficheiro de log.")

        moves_sql = ",\n    ".join(move_lines)

        return f"""
DECLARE @db sysname = {db_string};

IF DB_ID(@db) IS NOT NULL
BEGIN
    DECLARE @singleUserSql nvarchar(max);

    SET @singleUserSql =
        N'ALTER DATABASE ' + QUOTENAME(@db) +
        N' SET SINGLE_USER WITH ROLLBACK IMMEDIATE';

    EXEC (@singleUserSql);
END;

RESTORE DATABASE {db_identifier}
FROM DISK = {self._sql_string(backup_path)}
WITH
    {moves_sql},
    REPLACE,
    RECOVERY,
    STATS = 10;

DECLARE @multiUserSql nvarchar(max);

SET @multiUserSql =
    N'ALTER DATABASE ' + QUOTENAME(@db) +
    N' SET MULTI_USER';

EXEC (@multiUserSql);

SELECT
    name,
    collation_name,
    state_desc
FROM sys.databases
WHERE name = @db;
"""

    def restore_database_stream(
        self,
        container_name: str,
        sql_user: str,
        sql_password: str,
        restore_sql: str,
        on_output: Optional[Callable[[str], None]] = None,
    ) -> str:
        self._validate_credentials(sql_user, sql_password)

        return self._run_sql_stream(
            container_name=container_name,
            sql_user=sql_user,
            sql_password=sql_password,
            sql=restore_sql,
            on_output=on_output,
        )

    def validate_database(
        self,
        container_name: str,
        sql_user: str,
        sql_password: str,
        database_name: str,
    ) -> str:
        self._validate_credentials(sql_user, sql_password)
        self._validate_database_name(database_name)

        sql = f"""
SET NOCOUNT ON;

SELECT
    name,
    collation_name,
    state_desc
FROM sys.databases
WHERE name = {self._sql_string(database_name)};
"""

        return self._run_sql_capture(
            container_name=container_name,
            sql_user=sql_user,
            sql_password=sql_password,
            sql=sql,
            extra_sqlcmd_args=["-W", "-s", "|", "-h", "-1"],
        )

    # ------------------------------------------------------------------
    # Backup
    # ------------------------------------------------------------------

    def suggest_backup_filename(self, database_name: str) -> str:
        self._validate_database_name(database_name)

        safe_name = self._safe_file_base(database_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        return f"{safe_name}_{timestamp}.bak"

    def build_backup_sql(
        self,
        database_name: str,
        backup_file: str,
        verify_after_backup: bool = True,
        use_compression: bool = True,
        copy_only: bool = False,
    ) -> str:
        self._validate_database_name(database_name)
        self._validate_backup_filename(backup_file)

        backup_path = f"{self.backup_dir}/{backup_file}"
        db_identifier = self._sql_identifier(database_name)

        options = ["INIT", "CHECKSUM", "STATS = 10"]

        if use_compression:
            options.insert(1, "COMPRESSION")

        if copy_only:
            options.insert(1, "COPY_ONLY")

        options_sql = ",\n    ".join(options)

        verify_sql = ""
        if verify_after_backup:
            verify_sql = f"""
PRINT 'A validar backup com RESTORE VERIFYONLY...';
RESTORE VERIFYONLY
FROM DISK = {self._sql_string(backup_path)};
"""

        return f"""
SET NOCOUNT OFF;

PRINT 'A iniciar backup...';

BACKUP DATABASE {db_identifier}
TO DISK = {self._sql_string(backup_path)}
WITH
    {options_sql};

{verify_sql}

PRINT 'Backup concluído.';
"""

    def backup_database_stream(
        self,
        container_name: str,
        sql_user: str,
        sql_password: str,
        backup_sql: str,
        on_output: Optional[Callable[[str], None]] = None,
    ) -> str:
        self._validate_credentials(sql_user, sql_password)

        return self._run_sql_stream(
            container_name=container_name,
            sql_user=sql_user,
            sql_password=sql_password,
            sql=backup_sql,
            on_output=on_output,
        )

    # ------------------------------------------------------------------
    # Low-level helpers
    # ------------------------------------------------------------------

    def _docker_exec_bash(self, container_name: str, bash_command: str) -> str:
        result = subprocess.run(
            ["docker", "exec", container_name, "bash", "-lc", bash_command],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        if result.returncode != 0:
            raise DockerSqlServerError(
                result.stderr.strip()
                or result.stdout.strip()
                or "Erro ao executar comando dentro do container."
            )

        return result.stdout

    def _run_sql_capture(
        self,
        container_name: str,
        sql_user: str,
        sql_password: str,
        sql: str,
        extra_sqlcmd_args: Optional[List[str]] = None,
    ) -> str:
        if extra_sqlcmd_args is None:
            extra_sqlcmd_args = []

        bash_script = self._build_sqlcmd_bash_script(extra_sqlcmd_args)
        input_text = sql_user + "\n" + sql_password + "\n" + sql

        result = subprocess.run(
            ["docker", "exec", "-i", container_name, "bash", "-lc", bash_script],
            input=input_text,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        output = (result.stdout or "") + (result.stderr or "")

        if result.returncode != 0:
            raise DockerSqlServerError(output.strip() or "Erro ao executar sqlcmd.")

        return output

    def _run_sql_stream(
        self,
        container_name: str,
        sql_user: str,
        sql_password: str,
        sql: str,
        on_output: Optional[Callable[[str], None]] = None,
    ) -> str:
        bash_script = self._build_sqlcmd_bash_script([])

        process = subprocess.Popen(
            ["docker", "exec", "-i", container_name, "bash", "-lc", bash_script],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )

        full_output_lines = []

        assert process.stdin is not None
        assert process.stdout is not None

        process.stdin.write(sql_user + "\n")
        process.stdin.write(sql_password + "\n")
        process.stdin.write(sql)
        process.stdin.close()

        for line in process.stdout:
            line = line.rstrip()
            full_output_lines.append(line)

            if on_output:
                on_output(line)

        return_code = process.wait()
        full_output = "\n".join(full_output_lines)

        if return_code != 0:
            raise DockerSqlServerError(full_output or "Erro ao executar sqlcmd.")

        return full_output

    def _build_sqlcmd_bash_script(self, extra_sqlcmd_args: List[str]) -> str:
        extra_args = " ".join(shlex.quote(arg) for arg in extra_sqlcmd_args)

        return f"""
set -e

read -r SQL_USER
read -r SQL_PASS

SQL_FILE="$(mktemp)"
cat > "$SQL_FILE"

if [ -x /opt/mssql-tools18/bin/sqlcmd ]; then
    SQLCMD="/opt/mssql-tools18/bin/sqlcmd"
elif [ -x /opt/mssql-tools/bin/sqlcmd ]; then
    SQLCMD="/opt/mssql-tools/bin/sqlcmd"
else
    SQLCMD="sqlcmd"
fi

"$SQLCMD" \\
    -S localhost \\
    -U "$SQL_USER" \\
    -P "$SQL_PASS" \\
    -C \\
    -b \\
    -r1 \\
    {extra_args} \\
    -i "$SQL_FILE"

CODE=$?

rm -f "$SQL_FILE"

exit $CODE
"""

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    def _validate_backup_filename(self, backup_file: str) -> None:
        if not backup_file:
            raise DockerSqlServerError("O nome do backup está vazio.")

        if "/" in backup_file or "\\" in backup_file:
            raise DockerSqlServerError(
                "Informe apenas o nome do ficheiro .bak, não o caminho completo."
            )

        if not backup_file.lower().endswith(".bak"):
            raise DockerSqlServerError("O ficheiro precisa terminar com .bak.")

    def _validate_database_name(self, database_name: str) -> None:
        if not database_name or not database_name.strip():
            raise DockerSqlServerError("Informe o nome da base de dados.")

        if len(database_name) > 128:
            raise DockerSqlServerError(
                "O nome da base é demasiado grande. Máximo: 128 caracteres."
            )

    def _validate_credentials(self, sql_user: str, sql_password: str) -> None:
        if not sql_user or not sql_user.strip():
            raise DockerSqlServerError("Informe o utilizador SQL Server.")

        if not sql_password:
            raise DockerSqlServerError("Informe a password do utilizador SQL Server.")

        if "\n" in sql_user or "\r" in sql_user:
            raise DockerSqlServerError("O utilizador não pode conter quebra de linha.")

        if "\n" in sql_password or "\r" in sql_password:
            raise DockerSqlServerError("A password não pode conter quebra de linha.")

    def _sql_string(self, value: str) -> str:
        escaped = value.replace("'", "''")
        return f"N'{escaped}'"

    def _sql_identifier(self, value: str) -> str:
        escaped = value.replace("]", "]]" )
        return f"[{escaped}]"

    def _safe_file_base(self, database_name: str) -> str:
        value = database_name.strip()
        value = re.sub(r"[^A-Za-z0-9_.-]+", "_", value)
        value = value.strip("._-")

        if not value:
            value = "database"

        return value
