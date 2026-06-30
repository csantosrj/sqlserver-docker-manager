from PySide6.QtCore import QObject, Signal, Slot

from services.docker_sqlserver import DockerSqlServerService, DockerSqlServerError


class RestoreWorker(QObject):
    """Executa RESTORE DATABASE em background para não congelar a interface."""

    log = Signal(str)
    progress = Signal(int, str)
    finished = Signal(bool, str)

    def __init__(
        self,
        container_name: str,
        sql_user: str,
        sql_password: str,
        backup_file: str,
        database_name: str,
        backup_dir: str = "/var/opt/mssql/backup",
        data_dir: str = "/var/opt/mssql/data",
        validate_after_restore: bool = True,
    ):
        super().__init__()

        self.container_name = container_name
        self.sql_user = sql_user
        self.sql_password = sql_password
        self.backup_file = backup_file
        self.database_name = database_name
        self.backup_dir = backup_dir
        self.data_dir = data_dir
        self.validate_after_restore = validate_after_restore

        self.service = DockerSqlServerService(
            backup_dir=self.backup_dir,
            data_dir=self.data_dir,
        )

    @Slot()
    def run(self):
        try:
            self.progress.emit(5, "A verificar backup...")
            self.log.emit("🔎 A verificar se o backup existe dentro do container...")

            if not self.service.backup_exists(self.container_name, self.backup_file):
                raise DockerSqlServerError(
                    f"O ficheiro {self.backup_file} não existe em "
                    f"{self.backup_dir} dentro do container {self.container_name}."
                )

            self.progress.emit(20, "A ler estrutura do backup...")
            self.log.emit("📄 A executar RESTORE FILELISTONLY...")

            file_infos = self.service.restore_filelistonly(
                container_name=self.container_name,
                sql_user=self.sql_user,
                sql_password=self.sql_password,
                backup_file=self.backup_file,
            )

            self.log.emit("✅ Logical names encontrados:")

            for file_info in file_infos:
                self.log.emit(
                    f"   - {file_info.logical_name} "
                    f"tipo={file_info.file_type} "
                    f"origem={file_info.physical_name}"
                )

            self.progress.emit(40, "A preparar comando de restore...")
            self.log.emit("🧱 A preparar RESTORE DATABASE...")

            restore_sql = self.service.build_restore_sql(
                backup_file=self.backup_file,
                database_name=self.database_name,
                file_infos=file_infos,
            )

            self.progress.emit(55, "A restaurar base de dados...")
            self.log.emit("🚀 Restore iniciado. Isto pode demorar alguns minutos.")
            self.log.emit("")

            def handle_restore_output(line: str):
                if not line:
                    return

                self.log.emit(line)

                if "10 percent processed" in line:
                    self.progress.emit(60, "Restore 10%...")
                elif "20 percent processed" in line:
                    self.progress.emit(64, "Restore 20%...")
                elif "30 percent processed" in line:
                    self.progress.emit(68, "Restore 30%...")
                elif "40 percent processed" in line:
                    self.progress.emit(72, "Restore 40%...")
                elif "50 percent processed" in line:
                    self.progress.emit(76, "Restore 50%...")
                elif "60 percent processed" in line:
                    self.progress.emit(80, "Restore 60%...")
                elif "70 percent processed" in line:
                    self.progress.emit(84, "Restore 70%...")
                elif "80 percent processed" in line:
                    self.progress.emit(88, "Restore 80%...")
                elif "90 percent processed" in line:
                    self.progress.emit(92, "Restore 90%...")
                elif "100 percent processed" in line:
                    self.progress.emit(96, "Restore 100%...")

            self.service.restore_database_stream(
                container_name=self.container_name,
                sql_user=self.sql_user,
                sql_password=self.sql_password,
                restore_sql=restore_sql,
                on_output=handle_restore_output,
            )

            if self.validate_after_restore:
                self.progress.emit(98, "A validar base restaurada...")
                self.log.emit("")
                self.log.emit("🔍 A validar base restaurada...")

                validation_output = self.service.validate_database(
                    container_name=self.container_name,
                    sql_user=self.sql_user,
                    sql_password=self.sql_password,
                    database_name=self.database_name,
                )

                if validation_output.strip():
                    self.log.emit(validation_output.strip())
            else:
                self.progress.emit(98, "Validação ignorada por configuração...")
                self.log.emit("ℹ️ Validação pós-restore ignorada por configuração.")

            self.progress.emit(100, "Restore concluído.")
            self.log.emit("")
            self.log.emit("🎉 Base restaurada com sucesso!")

            self.finished.emit(True, "Base restaurada com sucesso.")

        except Exception as exc:
            self.log.emit("")
            self.log.emit("❌ O restore falhou.")
            self.log.emit("")
            self.log.emit("Erro técnico completo:")
            self.log.emit(str(exc))

            self.finished.emit(False, str(exc))
