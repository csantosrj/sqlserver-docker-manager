from PySide6.QtCore import QObject, Signal, Slot

from services.docker_sqlserver import DockerSqlServerService


class BackupWorker(QObject):
    """Executa BACKUP DATABASE em background para não congelar a interface."""

    log = Signal(str)
    progress = Signal(int, str)
    finished = Signal(bool, str)

    def __init__(
        self,
        container_name: str,
        sql_user: str,
        sql_password: str,
        database_name: str,
        backup_file: str,
        verify_after_backup: bool = True,
        backup_dir: str = "/var/opt/mssql/backup",
        use_compression: bool = True,
        copy_only: bool = False,
    ):
        super().__init__()

        self.container_name = container_name
        self.sql_user = sql_user
        self.sql_password = sql_password
        self.database_name = database_name
        self.backup_file = backup_file
        self.verify_after_backup = verify_after_backup
        self.backup_dir = backup_dir
        self.use_compression = use_compression
        self.copy_only = copy_only

        self.service = DockerSqlServerService(backup_dir=self.backup_dir)

    @Slot()
    def run(self):
        try:
            self.progress.emit(5, "A preparar backup...")
            self.log.emit("📦 A preparar BACKUP DATABASE...")
            self.log.emit(f"Base origem: {self.database_name}")
            self.log.emit(f"Ficheiro destino: {self.backup_file}")
            self.log.emit(f"Diretório destino: {self.backup_dir}")
            self.log.emit(f"Compression: {'sim' if self.use_compression else 'não'}")
            self.log.emit(f"Copy only: {'sim' if self.copy_only else 'não'}")
            self.log.emit("")

            sql = self.service.build_backup_sql(
                database_name=self.database_name,
                backup_file=self.backup_file,
                verify_after_backup=self.verify_after_backup,
                use_compression=self.use_compression,
                copy_only=self.copy_only,
            )

            self.progress.emit(20, "Backup iniciado...")
            self.log.emit("🚀 Backup iniciado. Aguarde...")
            self.log.emit("")

            def handle_output(line: str):
                if not line:
                    return

                self.log.emit(line)

                if "10 percent processed" in line:
                    self.progress.emit(30, "Backup 10%...")
                elif "20 percent processed" in line:
                    self.progress.emit(38, "Backup 20%...")
                elif "30 percent processed" in line:
                    self.progress.emit(46, "Backup 30%...")
                elif "40 percent processed" in line:
                    self.progress.emit(54, "Backup 40%...")
                elif "50 percent processed" in line:
                    self.progress.emit(62, "Backup 50%...")
                elif "60 percent processed" in line:
                    self.progress.emit(70, "Backup 60%...")
                elif "70 percent processed" in line:
                    self.progress.emit(78, "Backup 70%...")
                elif "80 percent processed" in line:
                    self.progress.emit(86, "Backup 80%...")
                elif "90 percent processed" in line:
                    self.progress.emit(92, "Backup 90%...")
                elif "100 percent processed" in line:
                    self.progress.emit(96, "Backup 100%...")

            self.service.backup_database_stream(
                container_name=self.container_name,
                sql_user=self.sql_user,
                sql_password=self.sql_password,
                backup_sql=sql,
                on_output=handle_output,
            )

            self.progress.emit(100, "Backup concluído.")
            self.log.emit("")
            self.log.emit("🎉 Backup criado com sucesso!")
            self.log.emit(f"📁 {self.backup_dir}/{self.backup_file}")

            self.finished.emit(True, "Backup criado com sucesso.")

        except Exception as exc:
            self.log.emit("")
            self.log.emit("❌ O backup falhou.")
            self.log.emit("")
            self.log.emit("Erro técnico completo:")
            self.log.emit(str(exc))

            self.finished.emit(False, str(exc))
