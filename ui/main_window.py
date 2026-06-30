import base64
import os
import re
from datetime import datetime

from PySide6.QtCore import Qt, QThread, QSize, QSettings
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QInputDialog,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QProgressBar,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QVBoxLayout,
    QWidget,
)

from services.docker_sqlserver import DockerSqlServerService
from workers.restore_worker import RestoreWorker
from workers.backup_worker import BackupWorker
from ui.styles import APP_QSS, LIGHT_QSS, STATUS_STYLES, get_app_qss, get_table_qss
from ui.components.step_progress import StepProgress
from ui.dialogs.confirm_restore_dialog import ConfirmRestoreDialog
from i18n import available_languages, language_label, set_language, tr as _


try:
    import qtawesome as qta
except ImportError:
    qta = None


DEFAULT_CONTAINER_NAME = "okapa-sqlserver"
PAGE_RESTORE = 0
PAGE_BACKUP = 1
PAGE_DATABASES = 2
PAGE_SETTINGS = 3


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.settings = QSettings("SentryTechLab", "SqlServerDockerManager")
        self.current_theme = str(self.settings.value("ui/theme", "dark"))
        self.current_language = str(self.settings.value("ui/language", "pt_PT"))
        set_language(self.current_language)

        self.setWindowTitle(_("SQL Server Docker Manager"))
        self._set_window_icon()
        self.setMinimumSize(1180, 760)
        self.resize(1450, 900)

        self.service = DockerSqlServerService()

        self.current_page = PAGE_RESTORE
        self.session_sql_password = ""

        self.restore_thread = None
        self.restore_worker = None
        self.backup_thread = None
        self.backup_worker = None

        self._build_ui()
        self._load_defaults()
        self._apply_static_translations()
        self.refresh_containers()

    # -------------------------------------------------------------------------
    # UI
    # -------------------------------------------------------------------------

    def _build_ui(self):
        self.setStyleSheet(get_app_qss(self.current_theme))

        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        sidebar = self._build_sidebar()
        content = self._build_content()

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setWidget(content)

        root_layout.addWidget(sidebar)
        root_layout.addWidget(scroll_area, 1)

        self.setCentralWidget(root)

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(245)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(18, 22, 18, 18)
        layout.setSpacing(14)

        title_row = QHBoxLayout()

        logo = QLabel()
        logo.setFixedSize(36, 36)
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet(
            """
            background-color: #2563EB;
            border-radius: 10px;
            color: white;
            font-weight: bold;
            font-size: 16px;
            """
        )
        logo.setText("SQL")

        title_box = QVBoxLayout()

        app_title = QLabel("Docker SQL")
        app_title.setObjectName("appTitle")

        app_subtitle = QLabel("Backup Manager")
        app_subtitle.setObjectName("appSubtitle")

        title_box.addWidget(app_title)
        title_box.addWidget(app_subtitle)

        title_row.addWidget(logo)
        title_row.addLayout(title_box)

        layout.addLayout(title_row)
        layout.addSpacing(18)

        self.restore_nav_button = self._nav_button("Restore", "fa5s.database", selected=True)
        self.restore_nav_button.clicked.connect(self.show_restore_page)

        self.backup_nav_button = self._nav_button("Backup", "fa5s.archive", selected=False, enabled=True)
        self.backup_nav_button.clicked.connect(self.show_backup_page)

        self.databases_nav_button = self._nav_button("Databases", "fa5s.server", selected=False, enabled=True)
        self.databases_nav_button.clicked.connect(self.show_databases_page)

        self.settings_nav_button = self._nav_button("Settings", "fa5s.cog", selected=False, enabled=True)
        self.settings_nav_button.clicked.connect(self.show_settings_page)

        self.exit_button = self._nav_button("Sair", "fa5s.sign-out-alt", selected=False, enabled=True)
        self.exit_button.setObjectName("navButtonDanger")
        self.exit_button.clicked.connect(self.close)

        layout.addWidget(self.restore_nav_button)
        layout.addWidget(self.backup_nav_button)
        layout.addWidget(self.databases_nav_button)
        layout.addWidget(self.settings_nav_button)
        layout.addWidget(self.exit_button)

        layout.addStretch()

        footer_card = QFrame()
        footer_card.setObjectName("smallCard")

        footer_layout = QVBoxLayout(footer_card)
        footer_layout.setContentsMargins(14, 14, 14, 14)

        footer_title = QLabel("Versão inicial")
        footer_title.setObjectName("cardValue")

        footer_hint = QLabel("Restore e Backup básicos\nativos para SQL Server Docker.")
        footer_hint.setObjectName("cardHint")
        footer_hint.setWordWrap(True)

        footer_layout.addWidget(footer_title)
        footer_layout.addWidget(footer_hint)

        layout.addWidget(footer_card)

        return sidebar

    def _build_content(self) -> QFrame:
        content = QFrame()
        content.setObjectName("contentPanel")

        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)

        header = self._build_header()
        summary = self._build_summary_cards()

        self.pages = QStackedWidget()
        self.pages.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.restore_page = self._build_restore_page()
        self.backup_page = self._build_backup_page()
        self.databases_page = self._build_databases_page()
        self.settings_page = self._build_settings_page()

        self.pages.addWidget(self.restore_page)
        self.pages.addWidget(self.backup_page)
        self.pages.addWidget(self.databases_page)
        self.pages.addWidget(self.settings_page)
        self._apply_page_height(PAGE_RESTORE)

        progress_card = self._build_progress_card()
        logs_card = self._build_logs_card()

        layout.addLayout(header)
        layout.addLayout(summary)
        layout.addWidget(self.pages)
        layout.addWidget(progress_card)
        layout.addWidget(logs_card, 1)

        return content

    def _build_header(self) -> QHBoxLayout:
        header = QHBoxLayout()

        title_box = QVBoxLayout()

        self.page_title = QLabel("Restore Backup")
        self.page_title.setObjectName("pageTitle")

        self.page_subtitle = QLabel(
            "Restaure bases SQL Server dentro de containers Docker com logs em tempo real."
        )
        self.page_subtitle.setObjectName("pageSubtitle")

        title_box.addWidget(self.page_title)
        title_box.addWidget(self.page_subtitle)

        self.status_badge = QLabel("Pronto")
        self.status_badge.setObjectName("statusBadge")
        self.status_badge.setAlignment(Qt.AlignCenter)
        self.status_badge.setStyleSheet(STATUS_STYLES["ready"])

        header.addLayout(title_box)
        header.addStretch()
        header.addWidget(self.status_badge)

        return header

    def _build_summary_cards(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(14)

        self.container_summary_value = self._small_card(
            title="Container",
            value=DEFAULT_CONTAINER_NAME,
            hint="SQL Server em Docker",
            icon_name="fa5s.cube",
        )

        self.backup_summary_value = self._small_card(
            title="Backup",
            value="Nenhum selecionado",
            hint="/var/opt/mssql/backup",
            icon_name="fa5s.file-archive",
        )

        self.database_summary_value = self._small_card(
            title="Base destino",
            value="Não definida",
            hint="/var/opt/mssql/data",
            icon_name="fa5s.database",
        )

        layout.addWidget(self.container_summary_value["card"])
        layout.addWidget(self.backup_summary_value["card"])
        layout.addWidget(self.database_summary_value["card"])

        return layout

    def _build_restore_page(self) -> QWidget:
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)
        page_layout.addWidget(self._build_restore_card())
        return page

    def _build_backup_page(self) -> QWidget:
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)
        page_layout.addWidget(self._build_backup_card())
        return page

    def _build_databases_page(self) -> QWidget:
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)

        # Este ecrã deve ter uma altura própria.
        # Não usamos stretch aqui, porque o QStackedWidget pode criar um gap grande
        # entre a tabela e os cards de progresso/logs.
        page_layout.addWidget(self._build_databases_card())
        return page

    def _build_settings_page(self) -> QWidget:
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)
        page_layout.addWidget(self._build_settings_card())
        return page


    def _build_restore_card(self) -> QFrame:
        """Card do menu Restore. A ligação vem do Settings."""
        card = QFrame()
        card.setObjectName("card")
        card.setMinimumHeight(310)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 22, 24, 24)
        layout.setSpacing(18)

        title_row = QHBoxLayout()
        title_row.setSpacing(12)

        section_title = QLabel("Configuração do restore")
        section_title.setObjectName("sectionTitle")

        self.refresh_containers_button = QPushButton("Atualizar containers")
        self.refresh_containers_button.setObjectName("secondaryButton")
        self.refresh_containers_button.setIcon(self._icon("fa5s.sync-alt"))
        self.refresh_containers_button.setMinimumHeight(38)
        self.refresh_containers_button.clicked.connect(self.refresh_containers)

        title_row.addWidget(section_title)
        title_row.addStretch()
        title_row.addWidget(self.refresh_containers_button)
        layout.addLayout(title_row)

        # Campos internos. Não aparecem no ecrã; são preenchidos pelo Settings.
        self.container_combo = QComboBox()
        self.container_combo.setEditable(True)
        self.container_combo.currentTextChanged.connect(self.update_summary_cards)
        self.container_combo.hide()

        self.user_input = QLineEdit()
        self.user_input.hide()

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.hide()

        connection_hint = QLabel("A ligação usada no restore vem do menu Settings.")
        connection_hint.setObjectName("mutedLabel")
        connection_hint.setWordWrap(True)
        layout.addWidget(connection_hint)

        # Formulário em linhas verticais para evitar sobreposição quando há botão ao lado.
        fields_box = QVBoxLayout()
        fields_box.setContentsMargins(0, 4, 0, 0)
        fields_box.setSpacing(14)

        backup_row = QHBoxLayout()
        backup_row.setContentsMargins(0, 0, 0, 0)
        backup_row.setSpacing(12)

        backup_label = QLabel("Backup .bak:")
        backup_label.setObjectName("mutedLabel")
        backup_label.setFixedWidth(120)
        backup_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        self.backup_combo = QComboBox()
        self.backup_combo.setEditable(False)
        self.backup_combo.setMinimumHeight(44)
        self.backup_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.backup_combo.currentTextChanged.connect(self.update_summary_cards)

        self.refresh_backups_button = QPushButton("Atualizar backups")
        self.refresh_backups_button.setObjectName("secondaryButton")
        self.refresh_backups_button.setIcon(self._icon("fa5s.redo"))
        self.refresh_backups_button.setMinimumHeight(44)
        self.refresh_backups_button.setFixedWidth(185)
        self.refresh_backups_button.clicked.connect(self.refresh_backups)

        backup_row.addWidget(backup_label)
        backup_row.addWidget(self.backup_combo, 1)
        backup_row.addWidget(self.refresh_backups_button)

        database_row = QHBoxLayout()
        database_row.setContentsMargins(0, 0, 0, 0)
        database_row.setSpacing(12)

        database_label = QLabel("Base destino:")
        database_label.setObjectName("mutedLabel")
        database_label.setFixedWidth(120)
        database_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        self.database_input = QLineEdit()
        self.database_input.setPlaceholderText("Nome da base destino")
        self.database_input.setMinimumHeight(44)
        self.database_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.database_input.textChanged.connect(self.update_summary_cards)

        # Espaçador invisível com a mesma largura do botão da linha de cima.
        # Assim os dois campos terminam alinhados e nunca passam por baixo dos botões.
        database_spacer = QWidget()
        database_spacer.setFixedWidth(185)

        database_row.addWidget(database_label)
        database_row.addWidget(self.database_input, 1)
        database_row.addWidget(database_spacer)

        fields_box.addLayout(backup_row)
        fields_box.addLayout(database_row)
        layout.addLayout(fields_box)

        actions = QHBoxLayout()
        actions.setContentsMargins(0, 10, 0, 0)
        actions.setSpacing(12)

        self.restore_button = QPushButton("Restaurar backup")
        self.restore_button.setObjectName("primaryButton")
        self.restore_button.setIcon(self._icon("fa5s.play"))
        self.restore_button.setIconSize(QSize(15, 15))
        self.restore_button.setMinimumHeight(44)
        self.restore_button.setMinimumWidth(175)
        self.restore_button.clicked.connect(self.start_restore)

        self.clear_log_button = QPushButton("Limpar log")
        self.clear_log_button.setObjectName("secondaryButton")
        self.clear_log_button.setIcon(self._icon("fa5s.trash-alt"))
        self.clear_log_button.setMinimumHeight(44)
        self.clear_log_button.setMinimumWidth(130)
        self.clear_log_button.clicked.connect(self.clear_log)

        actions.addStretch()
        actions.addWidget(self.clear_log_button)
        actions.addWidget(self.restore_button)
        layout.addLayout(actions)

        return card

    def _build_backup_card(self) -> QFrame:
        """Card do menu Backup. A ligação vem do Settings."""
        card = QFrame()
        card.setObjectName("card")
        card.setMinimumHeight(380)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 22, 24, 24)
        layout.setSpacing(18)

        title_row = QHBoxLayout()
        title_row.setSpacing(12)

        section_title = QLabel("Configuração do backup")
        section_title.setObjectName("sectionTitle")

        self.refresh_backup_containers_button = QPushButton("Atualizar containers")
        self.refresh_backup_containers_button.setObjectName("secondaryButton")
        self.refresh_backup_containers_button.setIcon(self._icon("fa5s.sync-alt"))
        self.refresh_backup_containers_button.setMinimumHeight(38)
        self.refresh_backup_containers_button.clicked.connect(self.refresh_containers)

        title_row.addWidget(section_title)
        title_row.addStretch()
        title_row.addWidget(self.refresh_backup_containers_button)
        layout.addLayout(title_row)

        # Campos internos. Não aparecem no ecrã; são preenchidos pelo Settings.
        self.backup_container_combo = QComboBox()
        self.backup_container_combo.setEditable(True)
        self.backup_container_combo.currentTextChanged.connect(self.update_summary_cards)
        self.backup_container_combo.hide()

        self.backup_user_input = QLineEdit()
        self.backup_user_input.hide()

        self.backup_password_input = QLineEdit()
        self.backup_password_input.setEchoMode(QLineEdit.Password)
        self.backup_password_input.hide()

        connection_hint = QLabel("A ligação usada no backup vem do menu Settings.")
        connection_hint.setObjectName("mutedLabel")
        connection_hint.setWordWrap(True)
        layout.addWidget(connection_hint)

        fields_box = QVBoxLayout()
        fields_box.setContentsMargins(0, 4, 0, 0)
        fields_box.setSpacing(14)

        source_row = QHBoxLayout()
        source_row.setContentsMargins(0, 0, 0, 0)
        source_row.setSpacing(12)

        source_label = QLabel("Base origem:")
        source_label.setObjectName("mutedLabel")
        source_label.setFixedWidth(120)
        source_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        self.source_database_combo = QComboBox()
        self.source_database_combo.setEditable(False)
        self.source_database_combo.setMinimumHeight(44)
        self.source_database_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.source_database_combo.currentTextChanged.connect(self.on_source_database_changed)

        self.refresh_databases_button = QPushButton("Atualizar bases")
        self.refresh_databases_button.setObjectName("secondaryButton")
        self.refresh_databases_button.setIcon(self._icon("fa5s.database"))
        self.refresh_databases_button.setMinimumHeight(44)
        self.refresh_databases_button.setFixedWidth(175)
        self.refresh_databases_button.clicked.connect(self.refresh_databases)

        source_row.addWidget(source_label)
        source_row.addWidget(self.source_database_combo, 1)
        source_row.addWidget(self.refresh_databases_button)

        file_row = QHBoxLayout()
        file_row.setContentsMargins(0, 0, 0, 0)
        file_row.setSpacing(12)

        file_label = QLabel("Ficheiro .bak:")
        file_label.setObjectName("mutedLabel")
        file_label.setFixedWidth(120)
        file_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        self.backup_file_input = QLineEdit()
        self.backup_file_input.setPlaceholderText("Exemplo: MinhaBase_20260629_153000.bak")
        self.backup_file_input.setMinimumHeight(44)
        self.backup_file_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.backup_file_input.textChanged.connect(self.update_summary_cards)

        file_spacer = QWidget()
        file_spacer.setFixedWidth(175)

        file_row.addWidget(file_label)
        file_row.addWidget(self.backup_file_input, 1)
        file_row.addWidget(file_spacer)

        validation_row = QHBoxLayout()
        validation_row.setContentsMargins(0, 0, 0, 0)
        validation_row.setSpacing(12)

        validation_label = QLabel("Validação:")
        validation_label.setObjectName("mutedLabel")
        validation_label.setFixedWidth(120)
        validation_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        self.verify_backup_checkbox = QCheckBox("Validar backup depois de criar com RESTORE VERIFYONLY")
        self.verify_backup_checkbox.setChecked(True)
        self.verify_backup_checkbox.setMinimumHeight(38)

        validation_row.addWidget(validation_label)
        validation_row.addWidget(self.verify_backup_checkbox, 1)

        fields_box.addLayout(source_row)
        fields_box.addLayout(file_row)
        fields_box.addLayout(validation_row)
        layout.addLayout(fields_box)

        actions = QHBoxLayout()
        actions.setContentsMargins(0, 10, 0, 0)
        actions.setSpacing(12)

        self.generate_backup_name_button = QPushButton("Gerar nome")
        self.generate_backup_name_button.setObjectName("secondaryButton")
        self.generate_backup_name_button.setIcon(self._icon("fa5s.magic"))
        self.generate_backup_name_button.setMinimumHeight(44)
        self.generate_backup_name_button.setMinimumWidth(135)
        self.generate_backup_name_button.clicked.connect(self.generate_backup_filename)

        self.start_backup_button = QPushButton("Fazer backup")
        self.start_backup_button.setObjectName("successButton")
        self.start_backup_button.setIcon(self._icon("fa5s.archive"))
        self.start_backup_button.setIconSize(QSize(15, 15))
        self.start_backup_button.setMinimumHeight(44)
        self.start_backup_button.setMinimumWidth(155)
        self.start_backup_button.clicked.connect(self.start_backup)

        actions.addStretch()
        actions.addWidget(self.generate_backup_name_button)
        actions.addWidget(self.start_backup_button)
        layout.addLayout(actions)

        return card

    def _build_databases_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        card.setMinimumHeight(455)
        card.setMaximumHeight(500)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 22, 24, 24)
        layout.setSpacing(16)

        # Cabeçalho compacto: título, ligação em uso e ação principal.
        header_row = QHBoxLayout()
        header_row.setSpacing(14)

        title_box = QVBoxLayout()
        title_box.setSpacing(4)

        section_title = QLabel("Bases de dados")
        section_title.setObjectName("sectionTitle")

        connection_hint = QLabel("Consulta usando a ligação definida no Settings.")
        connection_hint.setObjectName("mutedLabel")
        connection_hint.setWordWrap(True)

        title_box.addWidget(section_title)
        title_box.addWidget(connection_hint)

        self.refresh_database_list_button = QPushButton("Atualizar bases")
        self.refresh_database_list_button.setObjectName("primaryButton")
        self.refresh_database_list_button.setIcon(self._icon("fa5s.database"))
        self.refresh_database_list_button.setMinimumHeight(42)
        self.refresh_database_list_button.setMinimumWidth(165)
        self.refresh_database_list_button.clicked.connect(self.refresh_database_list)

        header_row.addLayout(title_box, 1)
        header_row.addWidget(self.refresh_database_list_button, 0, Qt.AlignTop)
        layout.addLayout(header_row)

        # Linha informativa pequena. Não repete campos editáveis, só mostra a origem da conexão.
        info_strip = QFrame()
        info_strip.setObjectName("smallCard")
        info_strip.setMaximumHeight(62)

        info_layout = QHBoxLayout(info_strip)
        info_layout.setContentsMargins(14, 10, 14, 10)
        info_layout.setSpacing(16)

        self.databases_connection_label = QLabel("Ligação: Settings")
        self.databases_connection_label.setObjectName("mutedLabel")

        self.databases_status_label = QLabel("Estado: aguardando consulta")
        self.databases_status_label.setObjectName("mutedLabel")
        self.databases_status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        info_layout.addWidget(self.databases_connection_label, 1)
        info_layout.addWidget(self.databases_status_label, 1)

        layout.addWidget(info_strip)

        # Campos internos. Não aparecem no ecrã; são preenchidos pelo Settings.
        self.databases_container_combo = QComboBox()
        self.databases_container_combo.setEditable(True)
        self.databases_container_combo.currentTextChanged.connect(self.update_summary_cards)
        self.databases_container_combo.hide()

        self.databases_user_input = QLineEdit()
        self.databases_user_input.hide()

        self.databases_password_input = QLineEdit()
        self.databases_password_input.setEchoMode(QLineEdit.Password)
        self.databases_password_input.hide()

        self.databases_table = QTableWidget()
        self.databases_table.setStyleSheet(get_table_qss(self.current_theme))
        self.databases_table.setColumnCount(6)
        self.databases_table.setHorizontalHeaderLabels([
            "Base",
            "Estado",
            "Recovery",
            "Collation",
            "Compat.",
            "Tamanho MB",
        ])
        self.databases_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.databases_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.databases_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.databases_table.setAlternatingRowColors(False)
        self.databases_table.verticalHeader().setVisible(False)
        self.databases_table.setMinimumHeight(260)
        self.databases_table.setMaximumHeight(300)
        self.databases_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        header = self.databases_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)

        layout.addWidget(self.databases_table)

        return card

    def _build_settings_card(self) -> QFrame:
        """Ecrã de configurações locais da ferramenta."""
        card = QFrame()
        card.setObjectName("card")
        card.setMinimumHeight(980)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 22, 24, 24)
        layout.setSpacing(22)

        title_row = QHBoxLayout()
        section_title = QLabel("Settings")
        section_title.setObjectName("sectionTitle")

        hint = QLabel("Guarde preferências locais da ferramenta. A password só é gravada se ativar essa opção explicitamente.")
        hint.setObjectName("mutedLabel")
        hint.setWordWrap(True)

        title_box = QVBoxLayout()
        title_box.addWidget(section_title)
        title_box.addWidget(hint)

        self.save_settings_button = QPushButton("Guardar configurações")
        self.save_settings_button.setObjectName("primaryButton")
        self.save_settings_button.setIcon(self._icon("fa5s.save"))
        self.save_settings_button.setMinimumHeight(42)
        self.save_settings_button.clicked.connect(self.save_settings)

        self.reset_settings_button = QPushButton("Restaurar padrão")
        self.reset_settings_button.setObjectName("secondaryButton")
        self.reset_settings_button.setIcon(self._icon("fa5s.undo"))
        self.reset_settings_button.setMinimumHeight(42)
        self.reset_settings_button.clicked.connect(self.reset_settings)

        self.test_connection_button = QPushButton("Testar conexão")
        self.test_connection_button.setObjectName("secondaryButton")
        self.test_connection_button.setIcon(self._icon("fa5s.plug"))
        self.test_connection_button.setMinimumHeight(42)
        self.test_connection_button.clicked.connect(self.test_settings_connection)

        title_row.addLayout(title_box)
        title_row.addStretch()
        title_row.addWidget(self.test_connection_button)
        title_row.addWidget(self.reset_settings_button)
        title_row.addWidget(self.save_settings_button)
        layout.addLayout(title_row)

        cards_row_1 = QHBoxLayout()
        cards_row_1.setSpacing(16)
        cards_row_1.setAlignment(Qt.AlignTop)
        cards_row_1.addWidget(self._build_connection_settings_card())
        cards_row_1.addWidget(self._build_interface_settings_card())

        cards_row_2 = QHBoxLayout()
        cards_row_2.setSpacing(16)
        cards_row_2.setAlignment(Qt.AlignTop)
        cards_row_2.addWidget(self._build_restore_settings_card())
        cards_row_2.addWidget(self._build_backup_settings_card())

        layout.addLayout(cards_row_1)
        layout.addSpacing(8)
        layout.addLayout(cards_row_2)

        return card

    def _build_connection_settings_card(self) -> QFrame:
        card = self._settings_subcard("Conexão", "fa5s.plug")
        card.setMinimumHeight(520)
        layout = card.layout()

        form = self._settings_form()
        form.setVerticalSpacing(14)

        self.settings_default_container_input = QLineEdit()
        self.settings_default_container_input.setPlaceholderText("okapa-sqlserver")
        self.settings_default_container_input.setMinimumHeight(40)
        form.addRow("Container padrão:", self.settings_default_container_input)

        self.settings_default_user_input = QLineEdit()
        self.settings_default_user_input.setPlaceholderText("sa")
        self.settings_default_user_input.setMinimumHeight(40)
        form.addRow("Utilizador padrão:", self.settings_default_user_input)

        password_row = QHBoxLayout()
        password_row.setSpacing(10)

        self.settings_session_password_input = QLineEdit()
        self.settings_session_password_input.setEchoMode(QLineEdit.Password)
        self.settings_session_password_input.setPlaceholderText("Password SQL da sessão atual")
        self.settings_session_password_input.setMinimumHeight(40)
        self.settings_session_password_input.textChanged.connect(self.update_session_status)

        self.settings_toggle_password_button = QPushButton("Mostrar")
        self.settings_toggle_password_button.setObjectName("secondaryButton")
        self.settings_toggle_password_button.setIcon(self._icon("fa5s.eye"))
        self.settings_toggle_password_button.setMinimumHeight(40)
        self.settings_toggle_password_button.setMinimumWidth(110)
        self.settings_toggle_password_button.clicked.connect(self.toggle_session_password_visibility)

        self.settings_clear_session_password_button = QPushButton("Limpar")
        self.settings_clear_session_password_button.setObjectName("secondaryButton")
        self.settings_clear_session_password_button.setIcon(self._icon("fa5s.trash-alt"))
        self.settings_clear_session_password_button.setMinimumHeight(40)
        self.settings_clear_session_password_button.setMinimumWidth(95)
        self.settings_clear_session_password_button.clicked.connect(self.clear_session_password)

        password_row.addWidget(self.settings_session_password_input, 1)
        password_row.addWidget(self.settings_toggle_password_button)
        password_row.addWidget(self.settings_clear_session_password_button)
        form.addRow("Password:", password_row)

        self.settings_save_password_checkbox = QPushButton("Guardar password: Não")
        self.settings_save_password_checkbox.setCheckable(True)
        self.settings_save_password_checkbox.setChecked(False)
        self.settings_save_password_checkbox.setMinimumHeight(40)
        self.settings_save_password_checkbox.setToolTip(
            "Quando ativo, a password será guardada localmente nas configurações deste utilizador."
        )
        self.settings_save_password_checkbox.toggled.connect(self.update_save_password_button_style)
        self.settings_save_password_checkbox.toggled.connect(lambda _checked: self.update_session_status())
        self.update_save_password_button_style()
        form.addRow("Guardar:", self.settings_save_password_checkbox)

        self.settings_session_status_label = QLabel("Sessão sem password definida.")
        self.settings_session_status_label.setObjectName("mutedLabel")
        self.settings_session_status_label.setWordWrap(True)
        self.settings_session_status_label.setMinimumHeight(38)
        form.addRow("Estado:", self.settings_session_status_label)

        self.settings_backup_dir_input = QLineEdit()
        self.settings_backup_dir_input.setPlaceholderText("/var/opt/mssql/backup")
        self.settings_backup_dir_input.setMinimumHeight(40)
        form.addRow("Diretório backup:", self.settings_backup_dir_input)

        self.settings_data_dir_input = QLineEdit()
        self.settings_data_dir_input.setPlaceholderText("/var/opt/mssql/data")
        self.settings_data_dir_input.setMinimumHeight(40)
        form.addRow("Diretório dados:", self.settings_data_dir_input)

        layout.addLayout(form)

        security_note = QLabel(
            "Password segura por padrão. A password fica apenas na memória enquanto a aplicação estiver aberta. "
            "Ao ativar Guardar password, ela será gravada localmente nas configurações do utilizador. "
            "Use esta opção apenas em computador pessoal ou ambiente de confiança."
        )
        security_note.setWordWrap(True)
        security_note.setMinimumHeight(76)
        security_note.setStyleSheet(
            """
            QLabel {
                background-color: rgba(59, 130, 246, 0.10);
                border: 1px solid rgba(59, 130, 246, 0.28);
                border-radius: 10px;
                color: #CBD5E1;
                padding: 10px 12px;
                line-height: 1.35em;
            }
            """
        )
        layout.addWidget(security_note)

        return card

    def _build_restore_settings_card(self) -> QFrame:
        card = self._settings_subcard("Restore", "fa5s.database")
        card.setMinimumHeight(300)
        layout = card.layout()

        form = self._settings_form()

        self.settings_confirm_overwrite_checkbox = QCheckBox("Confirmar antes de sobrescrever base existente")
        self.settings_confirm_overwrite_checkbox.setChecked(True)
        form.addRow("Segurança:", self.settings_confirm_overwrite_checkbox)

        self.settings_restore_suffix_input = QLineEdit()
        self.settings_restore_suffix_input.setPlaceholderText("_Restored")
        self.settings_restore_suffix_input.setMinimumHeight(40)
        form.addRow("Sufixo para testes:", self.settings_restore_suffix_input)

        self.settings_validate_restore_checkbox = QCheckBox("Validar base depois do restore")
        self.settings_validate_restore_checkbox.setChecked(True)
        form.addRow("Validação:", self.settings_validate_restore_checkbox)

        layout.addLayout(form)
        return card

    def _build_backup_settings_card(self) -> QFrame:
        card = self._settings_subcard("Backup", "fa5s.archive")
        card.setMinimumHeight(300)
        layout = card.layout()

        form = self._settings_form()

        self.settings_backup_compression_checkbox = QCheckBox("Usar COMPRESSION")
        self.settings_backup_compression_checkbox.setChecked(True)
        form.addRow("Compressão:", self.settings_backup_compression_checkbox)

        self.settings_backup_verify_checkbox = QCheckBox("Validar com RESTORE VERIFYONLY")
        self.settings_backup_verify_checkbox.setChecked(True)
        form.addRow("Verificação:", self.settings_backup_verify_checkbox)

        self.settings_backup_copy_only_checkbox = QCheckBox("Usar COPY_ONLY")
        self.settings_backup_copy_only_checkbox.setChecked(False)
        form.addRow("Modo:", self.settings_backup_copy_only_checkbox)

        self.settings_backup_pattern_input = QLineEdit()
        self.settings_backup_pattern_input.setPlaceholderText("{database}_{yyyyMMdd}_{HHmmss}.bak")
        self.settings_backup_pattern_input.setMinimumHeight(40)
        form.addRow("Padrão do nome:", self.settings_backup_pattern_input)

        layout.addLayout(form)
        return card

    def _build_interface_settings_card(self) -> QFrame:
        card = self._settings_subcard("Interface", "fa5s.paint-brush")
        card.setMinimumHeight(360)
        layout = card.layout()

        form = self._settings_form()

        self.settings_language_combo = QComboBox()
        self.settings_language_combo.setMinimumHeight(40)
        for lang_code, lang_name in available_languages():
            self.settings_language_combo.addItem(lang_name, lang_code)
        self.settings_language_combo.currentIndexChanged.connect(self.apply_language_from_settings)
        form.addRow("Idioma:", self.settings_language_combo)

        self.settings_theme_combo = QComboBox()
        self.settings_theme_combo.setMinimumHeight(40)
        self.settings_theme_combo.addItem("Dark Premium", "dark")
        self.settings_theme_combo.addItem("Light Professional", "light")
        self.settings_theme_combo.currentIndexChanged.connect(self.apply_theme_from_settings)
        form.addRow("Tema:", self.settings_theme_combo)

        self.settings_open_maximized_checkbox = QCheckBox("Abrir aplicação maximizada")
        self.settings_open_maximized_checkbox.setChecked(True)
        form.addRow("Janela:", self.settings_open_maximized_checkbox)

        self.settings_save_logs_checkbox = QCheckBox("Guardar logs das operações em ficheiro")
        self.settings_save_logs_checkbox.setChecked(False)
        form.addRow("Logs:", self.settings_save_logs_checkbox)

        self.settings_log_dir_input = QLineEdit()
        self.settings_log_dir_input.setPlaceholderText("./logs")
        self.settings_log_dir_input.setMinimumHeight(40)
        form.addRow("Pasta dos logs:", self.settings_log_dir_input)

        layout.addLayout(form)
        return card

    def _settings_subcard(self, title: str, icon_name: str) -> QFrame:
        card = QFrame()
        card.setObjectName("smallCard")
        card.setMinimumHeight(280)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 18)
        layout.setSpacing(14)

        title_row = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setFixedSize(32, 32)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(
            """
            background-color: rgba(37, 99, 235, 0.16);
            border: 1px solid rgba(59, 130, 246, 0.32);
            border-radius: 10px;
            """
        )
        icon_label.setPixmap(self._icon(icon_name, color="#93C5FD").pixmap(15, 15))

        title_label = QLabel(title)
        title_label.setObjectName("sectionTitle")

        title_row.addWidget(icon_label)
        title_row.addWidget(title_label)
        title_row.addStretch()

        layout.addLayout(title_row)
        return card

    def _settings_form(self) -> QFormLayout:
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        form.setFormAlignment(Qt.AlignTop)
        form.setHorizontalSpacing(18)
        form.setVerticalSpacing(14)
        form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        form.setRowWrapPolicy(QFormLayout.DontWrapRows)
        return form

    def _build_progress_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        card.setMinimumHeight(220)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 18)
        layout.setSpacing(14)

        top = QHBoxLayout()

        section_title = QLabel("Progresso da operação")
        section_title.setObjectName("sectionTitle")

        self.status_label = QLabel("Pronto.")
        self.status_label.setObjectName("mutedLabel")
        self.status_label.setAlignment(Qt.AlignRight)

        top.addWidget(section_title)
        top.addStretch()
        top.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)

        self.step_progress = StepProgress()

        self.step_label = QLabel("Aguardando uma operação.")
        self.step_label.setObjectName("mutedLabel")

        layout.addLayout(top)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.step_progress)
        layout.addWidget(self.step_label)

        return card

    def _build_logs_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        card.setMinimumHeight(210)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 20)
        layout.setSpacing(12)

        top = QHBoxLayout()

        section_title = QLabel("Logs em tempo real")
        section_title.setObjectName("sectionTitle")

        hint = QLabel("Aqui aparecem mensagens amigáveis e erros técnicos completos.")
        hint.setObjectName("mutedLabel")

        title_box = QVBoxLayout()
        title_box.addWidget(section_title)
        title_box.addWidget(hint)

        self.copy_log_button = QPushButton("Copiar log")
        self.copy_log_button.setObjectName("secondaryButton")
        self.copy_log_button.setIcon(self._icon("fa5s.copy"))
        self.copy_log_button.clicked.connect(self.copy_log)

        top.addLayout(title_box)
        top.addStretch()
        top.addWidget(self.copy_log_button)

        self.log_output = QPlainTextEdit()
        self.log_output.setObjectName("logOutput")
        self.log_output.setReadOnly(True)
        self.log_output.setPlaceholderText("Os logs aparecerão aqui...")

        layout.addLayout(top)
        layout.addWidget(self.log_output, 1)

        return card

    # -------------------------------------------------------------------------
    # Navegação
    # -------------------------------------------------------------------------

    def show_restore_page(self):
        self.current_page = PAGE_RESTORE
        self.pages.setCurrentIndex(PAGE_RESTORE)
        self._apply_page_height(PAGE_RESTORE)
        self._set_translated_text(self.page_title, "Restore Backup")
        self._set_translated_text(self.page_subtitle, "Restaure bases SQL Server dentro de containers Docker com logs em tempo real.")
        self.step_progress.show()
        self._set_translated_text(self.step_label, "Aguardando uma operação.")
        self._set_nav_selected(PAGE_RESTORE)
        self.update_summary_cards()

    def show_backup_page(self):
        self.current_page = PAGE_BACKUP
        self.pages.setCurrentIndex(PAGE_BACKUP)
        self._apply_page_height(PAGE_BACKUP)
        self._set_translated_text(self.page_title, "Backup Database")
        self._set_translated_text(self.page_subtitle, "Crie backups .bak de bases SQL Server dentro do container Docker.")
        self.step_progress.hide()
        self._set_translated_text(self.step_label, "Aguardando backup.")
        self._set_nav_selected(PAGE_BACKUP)
        self.update_summary_cards()

    def show_databases_page(self):
        self.current_page = PAGE_DATABASES
        self.pages.setCurrentIndex(PAGE_DATABASES)
        self._apply_page_height(PAGE_DATABASES)
        self._set_translated_text(self.page_title, "Databases")
        self._set_translated_text(self.page_subtitle, "Consulte bases SQL Server disponíveis no container selecionado.")
        self.step_progress.hide()
        self._set_translated_text(self.step_label, "Aguardando consulta de bases.")
        self._set_nav_selected(PAGE_DATABASES)
        self.update_summary_cards()

    def show_settings_page(self):
        self.current_page = PAGE_SETTINGS
        self.pages.setCurrentIndex(PAGE_SETTINGS)
        self._apply_page_height(PAGE_SETTINGS)
        self._set_translated_text(self.page_title, "Settings")
        self._set_translated_text(self.page_subtitle, "Configure defaults, tema e preferências locais da ferramenta.")
        self.step_progress.hide()
        self._set_translated_text(self.step_label, "Configurações locais da aplicação.")
        self._set_nav_selected(PAGE_SETTINGS)
        self.update_summary_cards()

    def _apply_page_height(self, page_index: int):
        """
        Define uma altura própria para cada página do QStackedWidget.

        Sem isto, o QStackedWidget pode assumir a altura da maior página
        (Settings) e criar um espaço vazio enorme nos ecrãs menores,
        como Databases, Restore e Backup.
        """
        heights = {
            # Estas alturas precisam ser maiores ou iguais à altura mínima
            # dos cards internos. Se forem menores, o QStackedWidget corta
            # o card e o próximo painel parece ficar sobreposto.
            PAGE_RESTORE: 345,
            PAGE_BACKUP: 415,
            PAGE_DATABASES: 520,
            PAGE_SETTINGS: 1040,  # Settings precisa de mais altura para evitar sobreposição dos cards
        }

        height = heights.get(page_index, 320)

        if hasattr(self, "pages"):
            self.pages.setMinimumHeight(height)
            self.pages.setMaximumHeight(height)
            self.pages.setFixedHeight(height)

        current_widget = self.pages.widget(page_index) if hasattr(self, "pages") else None
        if current_widget is not None:
            current_widget.setMinimumHeight(height)
            current_widget.setMaximumHeight(height)

    def _set_nav_selected(self, page_index: int):
        self.restore_nav_button.setObjectName("navButtonSelected" if page_index == PAGE_RESTORE else "navButton")
        self.backup_nav_button.setObjectName("navButtonSelected" if page_index == PAGE_BACKUP else "navButton")
        self.databases_nav_button.setObjectName("navButtonSelected" if page_index == PAGE_DATABASES else "navButton")
        self.settings_nav_button.setObjectName("navButtonSelected" if page_index == PAGE_SETTINGS else "navButton")
        self.restore_nav_button.setStyleSheet("")
        self.backup_nav_button.setStyleSheet("")
        self.databases_nav_button.setStyleSheet("")
        self.settings_nav_button.setStyleSheet("")
        self.exit_button.setObjectName("navButtonDanger")
        self.exit_button.setStyleSheet("")

    # -------------------------------------------------------------------------
    # Helpers visuais
    # -------------------------------------------------------------------------

    def _small_card(self, title: str, value: str, hint: str, icon_name: str):
        card = QFrame()
        card.setObjectName("smallCard")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        card.setMinimumHeight(105)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(12)

        icon_label = QLabel()
        icon_label.setFixedSize(40, 40)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(
            """
            background-color: rgba(37, 99, 235, 0.18);
            border: 1px solid rgba(59, 130, 246, 0.35);
            border-radius: 12px;
            """
        )
        icon_label.setPixmap(self._icon(icon_name, color="#93C5FD").pixmap(18, 18))

        text_box = QVBoxLayout()

        title_label = QLabel(title)
        title_label.setObjectName("cardHint")

        value_label = QLabel(value)
        value_label.setObjectName("cardValue")
        value_label.setWordWrap(False)

        hint_label = QLabel(hint)
        hint_label.setObjectName("cardHint")

        text_box.addWidget(title_label)
        text_box.addWidget(value_label)
        text_box.addWidget(hint_label)

        layout.addWidget(icon_label)
        layout.addLayout(text_box)

        return {"card": card, "title": title_label, "value": value_label, "hint": hint_label}

    def _nav_button(self, text: str, icon_name: str, selected: bool = False, enabled: bool = True) -> QPushButton:
        button = QPushButton(text)
        button.setObjectName("navButtonSelected" if selected else "navButton")
        button.setIcon(self._icon(icon_name))
        button.setIconSize(QSize(15, 15))
        button.setEnabled(enabled)
        return button

    def _icon(self, name: str, color: str = "#E5E7EB") -> QIcon:
        if qta is None:
            return QIcon()

        try:
            return qta.icon(name, color=color)
        except Exception:
            return QIcon()

    def set_status_badge(self, status: str, text: str):
        self.status_badge.setText(_(text))
        self.status_badge.setProperty("_i18n_source_text", text)
        self.status_badge.setStyleSheet(STATUS_STYLES.get(status, STATUS_STYLES["ready"]))

    def update_summary_cards(self):
        if self.current_page == PAGE_SETTINGS:
            theme = "Light" if self.current_theme == "light" else "Dark"
            container_name = self.settings_default_container_input.text().strip() if hasattr(self, "settings_default_container_input") else DEFAULT_CONTAINER_NAME
            self.backup_summary_value["title"].setText(_("Tema"))
            self.database_summary_value["title"].setText(_("Configuração"))
            self.database_summary_value["hint"].setText(_("Preferências locais"))
            self.container_summary_value["value"].setText(container_name or DEFAULT_CONTAINER_NAME)
            self.backup_summary_value["value"].setText(_("Light") if theme == "Light" else _("Dark"))
            self.database_summary_value["value"].setText(_("Guardada"))
            return

        if self.current_page == PAGE_DATABASES:
            container_name = self.get_selected_databases_container_name() or DEFAULT_CONTAINER_NAME
            user_name = self.get_settings_user_name() if hasattr(self, "settings_default_user_input") else "sa"
            count = self.databases_table.rowCount() if hasattr(self, "databases_table") else 0

            self.backup_summary_value["title"].setText(_("Bases encontradas"))
            self.database_summary_value["title"].setText(_("Consulta"))
            self.database_summary_value["hint"].setText(_("Estado das bases"))

            self.container_summary_value["value"].setText(container_name)
            self.backup_summary_value["value"].setText(str(count))
            self.database_summary_value["value"].setText(_("Pronto") if count else _("Não carregada"))

            if hasattr(self, "databases_connection_label"):
                self.databases_connection_label.setText(
                    _("Ligação: ") + f"{container_name}  •  " + _("utilizador ") + f"{user_name}"
                )

            if hasattr(self, "databases_status_label"):
                self.databases_status_label.setText(
                    (_("Estado: ") + f"{count} " + _("base(s) carregada(s)")) if count else _("Estado: aguardando consulta")
                )

            return

        if self.current_page == PAGE_BACKUP:
            container_name = self.get_selected_backup_container_name() or DEFAULT_CONTAINER_NAME
            source_db = self.source_database_combo.currentText().strip() if hasattr(self, "source_database_combo") else ""
            backup_file = self.backup_file_input.text().strip() if hasattr(self, "backup_file_input") else ""

            self.backup_summary_value["title"].setText(_("Backup destino"))
            self.database_summary_value["title"].setText(_("Base origem"))
            self.database_summary_value["hint"].setText(_("Base a exportar"))

            self.container_summary_value["value"].setText(container_name)
            self.backup_summary_value["value"].setText(backup_file if backup_file else _("Não definido"))
            self.database_summary_value["value"].setText(source_db if source_db else _("Não selecionada"))
            return

        container_name = self.get_selected_container_name() or DEFAULT_CONTAINER_NAME
        backup_name = self.backup_combo.currentText().strip() if hasattr(self, "backup_combo") else ""
        database_name = self.database_input.text().strip() if hasattr(self, "database_input") else ""

        self.backup_summary_value["title"].setText(_("Backup"))
        self.database_summary_value["title"].setText(_("Base destino"))
        self.database_summary_value["hint"].setText("/var/opt/mssql/data")

        self.container_summary_value["value"].setText(container_name)
        self.backup_summary_value["value"].setText(backup_name if backup_name else _("Nenhum selecionado"))
        self.database_summary_value["value"].setText(database_name if database_name else _("Não definida"))

    # -------------------------------------------------------------------------
    # Dados iniciais
    # -------------------------------------------------------------------------

    def _load_defaults(self):
        default_container = str(self.settings.value("connection/default_container", DEFAULT_CONTAINER_NAME))
        sql_user = str(self.settings.value("connection/default_user", "sa"))
        backup_dir = str(self.settings.value("paths/backup_dir", "/var/opt/mssql/backup"))
        data_dir = str(self.settings.value("paths/data_dir", "/var/opt/mssql/data"))

        self.container_combo.setEditText(default_container)
        self.backup_container_combo.setEditText(default_container)
        self.databases_container_combo.setEditText(default_container)

        self.user_input.setText(sql_user)
        self.backup_user_input.setText(sql_user)
        self.databases_user_input.setText(sql_user)

        self.password_input.setText("")
        self.backup_password_input.setText("")
        self.databases_password_input.setText("")

        self.verify_backup_checkbox.setChecked(self._setting_bool("backup/verify_after_backup", True))

        self.settings_default_container_input.setText(default_container)
        self.settings_default_user_input.setText(sql_user)

        save_password = self._setting_bool("connection/save_password", False)
        saved_password = ""
        if save_password:
            saved_password = self._decode_saved_password(
                str(self.settings.value("connection/saved_password", ""))
            )

        self.session_sql_password = saved_password
        self.settings_session_password_input.blockSignals(True)
        self.settings_session_password_input.setText(saved_password)
        self.settings_session_password_input.blockSignals(False)
        self.settings_save_password_checkbox.setChecked(save_password and bool(saved_password))
        self.update_save_password_button_style()
        self.update_session_status()

        self.settings_backup_dir_input.setText(backup_dir)
        self.settings_data_dir_input.setText(data_dir)
        self.settings_confirm_overwrite_checkbox.setChecked(self._setting_bool("restore/confirm_overwrite", True))
        self.settings_restore_suffix_input.setText(str(self.settings.value("restore/default_suffix", "_Restored")))
        self.settings_validate_restore_checkbox.setChecked(self._setting_bool("restore/validate_after_restore", True))
        self.settings_backup_compression_checkbox.setChecked(self._setting_bool("backup/use_compression", True))
        self.settings_backup_verify_checkbox.setChecked(self._setting_bool("backup/verify_after_backup", True))
        self.settings_backup_copy_only_checkbox.setChecked(self._setting_bool("backup/copy_only", False))
        self.settings_backup_pattern_input.setText(str(self.settings.value("backup/name_pattern", "{database}_{yyyyMMdd}_{HHmmss}.bak")))
        self.settings_open_maximized_checkbox.setChecked(self._setting_bool("ui/open_maximized", True))
        self.settings_save_logs_checkbox.setChecked(self._setting_bool("logs/save_to_file", False))
        self.settings_log_dir_input.setText(str(self.settings.value("logs/log_dir", "./logs")))

        lang_index = self.settings_language_combo.findData(self.current_language)
        if lang_index >= 0:
            self.settings_language_combo.blockSignals(True)
            self.settings_language_combo.setCurrentIndex(lang_index)
            self.settings_language_combo.blockSignals(False)

        index = self.settings_theme_combo.findData(self.current_theme)
        if index >= 0:
            self.settings_theme_combo.blockSignals(True)
            self.settings_theme_combo.setCurrentIndex(index)
            self.settings_theme_combo.blockSignals(False)

        self.service = DockerSqlServerService(backup_dir=backup_dir, data_dir=data_dir)
        self.apply_theme(self.current_theme)
        self.update_summary_cards()

    def _setting_bool(self, key: str, default: bool) -> bool:
        value = self.settings.value(key, default)
        if isinstance(value, bool):
            return value
        return str(value).lower() in ("1", "true", "yes", "sim", "on")

    def _encode_saved_password(self, password: str) -> str:
        if not password:
            return ""
        raw = password.encode("utf-8")
        return "b64:" + base64.b64encode(raw).decode("ascii")

    def _decode_saved_password(self, stored_value: str) -> str:
        if not stored_value:
            return ""
        try:
            if stored_value.startswith("b64:"):
                raw = stored_value[4:].encode("ascii")
                return base64.b64decode(raw).decode("utf-8")
            # Compatibilidade caso algum valor antigo tenha sido guardado em texto simples.
            return stored_value
        except Exception:
            return ""

    def get_default_container_setting(self) -> str:
        if hasattr(self, "settings_default_container_input"):
            return self.settings_default_container_input.text().strip() or DEFAULT_CONTAINER_NAME
        return str(self.settings.value("connection/default_container", DEFAULT_CONTAINER_NAME))

    def get_default_user_setting(self) -> str:
        if hasattr(self, "settings_default_user_input"):
            return self.settings_default_user_input.text().strip() or "sa"
        return str(self.settings.value("connection/default_user", "sa"))

    def get_settings_user_name(self) -> str:
        """Compatibilidade para o ecrã Databases.

        Algumas partes da UI antiga chamavam este nome.
        A fonte correta agora é sempre o Settings.
        """
        return self.get_default_user_setting()

    def get_password_source_setting(self) -> str:
        return "session"

    def get_password_env_name_setting(self) -> str:
        return ""

    def _sanitize_env_name(self, value: str) -> str:
        return ""

    def get_vault_key(self, container_name: str | None = None, sql_user: str | None = None) -> str:
        return "session-only"

    def get_sql_password_from_values(
        self,
        container_name: str,
        sql_user: str,
        password_source: str = "session",
        password_env_name: str = "",
    ) -> str:
        if hasattr(self, "settings_session_password_input"):
            typed_password = self.settings_session_password_input.text()
            if typed_password:
                self.session_sql_password = typed_password

        return self.session_sql_password or ""

    def get_sql_password_from_settings(self) -> str:
        return self.get_sql_password_from_values(
            container_name=self.get_default_container_setting(),
            sql_user=self.get_default_user_setting(),
        )

    def update_password_source_ui(self):
        self.update_session_status()

    def update_session_status(self):
        if not hasattr(self, "settings_session_status_label"):
            return

        current = ""
        if hasattr(self, "settings_session_password_input"):
            current = self.settings_session_password_input.text()

        if current:
            self.session_sql_password = current

        has_password = bool(current or self.session_sql_password)
        wants_save = False
        if hasattr(self, "settings_save_password_checkbox"):
            wants_save = self.settings_save_password_checkbox.isChecked()

        if has_password and wants_save:
            self.settings_session_status_label.setText(
                _("Password definida. Será carregada automaticamente nas próximas aberturas.")
            )
        elif has_password:
            self.settings_session_status_label.setText(
                _("Password definida apenas para esta sessão. Não será guardada.")
            )
        else:
            self.settings_session_status_label.setText(_("Sessão sem password definida."))

    def update_save_password_button_style(self):
        if not hasattr(self, "settings_save_password_checkbox"):
            return

        checked = self.settings_save_password_checkbox.isChecked()

        if checked:
            self.settings_save_password_checkbox.setText(_("Guardar password: Sim"))
            self.settings_save_password_checkbox.setIcon(self._icon("fa5s.lock", color="#FFFFFF"))
            self.settings_save_password_checkbox.setStyleSheet(
                """
                QPushButton {
                    background-color: #059669;
                    border: 1px solid #10B981;
                    color: white;
                    border-radius: 10px;
                    padding: 9px 14px;
                    font-weight: 700;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #047857;
                }
                """
            )
        else:
            self.settings_save_password_checkbox.setText(_("Guardar password: Não"))
            self.settings_save_password_checkbox.setIcon(self._icon("fa5s.lock-open", color="#CBD5E1"))
            self.settings_save_password_checkbox.setStyleSheet(
                """
                QPushButton {
                    background-color: #1F2937;
                    border: 1px solid #374151;
                    color: #CBD5E1;
                    border-radius: 10px;
                    padding: 9px 14px;
                    font-weight: 700;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #273449;
                    border: 1px solid #4B5563;
                }
                """
            )

    def set_session_password(self):
        # Mantido por compatibilidade. A versão atual usa o campo Password no Settings.
        if hasattr(self, "settings_session_password_input"):
            self.session_sql_password = self.settings_session_password_input.text()
        self.update_session_status()

    def clear_session_password(self):
        self.session_sql_password = ""
        if hasattr(self, "settings_session_password_input"):
            self.settings_session_password_input.clear()
            self.settings_session_password_input.setEchoMode(QLineEdit.Password)
        if hasattr(self, "settings_toggle_password_button"):
            self.settings_toggle_password_button.setText(_("Mostrar"))
            self.settings_toggle_password_button.setIcon(self._icon("fa5s.eye"))
        if hasattr(self, "settings_save_password_checkbox"):
            self.settings_save_password_checkbox.setChecked(False)

        self.settings.setValue("connection/save_password", False)
        self.settings.remove("connection/saved_password")
        self.settings.sync()

        self.update_session_status()
        self.append_log("ℹ️ Password removida da sessão e das configurações locais.")

    def update_vault_status(self):
        # Cofre local removido nesta versão. A password fica apenas na sessão atual.
        return

    def save_password_to_vault(self):
        # Cofre local removido nesta versão. A password fica apenas na sessão atual.
        return

    def clear_password_from_vault(self):
        # Cofre local removido nesta versão. A password fica apenas na sessão atual.
        return


    def toggle_session_password_visibility(self):
        if not hasattr(self, "settings_session_password_input"):
            return

        if self.settings_session_password_input.echoMode() == QLineEdit.Password:
            self.settings_session_password_input.setEchoMode(QLineEdit.Normal)
            self.settings_toggle_password_button.setText(_("Ocultar"))
            self.settings_toggle_password_button.setIcon(self._icon("fa5s.eye-slash"))
        else:
            self.settings_session_password_input.setEchoMode(QLineEdit.Password)
            self.settings_toggle_password_button.setText(_("Mostrar"))
            self.settings_toggle_password_button.setIcon(self._icon("fa5s.eye"))

    def get_connection_config(self):
        """
        Devolve a ligação ativa definida no Settings.

        A password vem do campo Settings. Se o utilizador marcou para guardar,
        ela também é carregada das configurações locais ao abrir a aplicação.
        """
        container_name = self.get_default_container_setting()
        sql_user = self.get_default_user_setting()
        sql_password = self.get_sql_password_from_settings()
        return container_name, sql_user, sql_password, "session"

    def validate_connection_config(self, require_password: bool = True) -> tuple[str, str, str]:
        """
        Valida a ligação definida em Settings e devolve container, utilizador e password.
        """
        container_name, sql_user, sql_password, _password_source = self.get_connection_config()

        if not container_name:
            raise ValueError("Informe o container padrão no menu Settings.")

        if not sql_user:
            raise ValueError("Informe o utilizador SQL padrão no menu Settings.")

        if require_password and not sql_password:
            raise ValueError(
                "A password não foi definida. "
                "Vá ao menu Settings e informe a password no campo Password."
            )

        return container_name, sql_user, sql_password

    def show_connection_config_error(self, exc: Exception):
        self.append_log("")
        self.append_log("❌ Erro na configuração de ligação:")
        self.append_log(str(exc))
        self.set_status_badge("error", "Erro")
        self.status_label.setText("Configuração de ligação inválida.")
        self.step_label.setText("Veja o menu Settings e confirme container, utilizador e password.")
        QMessageBox.critical(
            self,
            "Erro de configuração",
            "Não foi possível obter a ligação configurada em Settings.\n\n"
            f"Detalhe: {exc}",
        )

    def get_backup_dir_setting(self) -> str:
        if hasattr(self, "settings_backup_dir_input"):
            return self.settings_backup_dir_input.text().strip() or "/var/opt/mssql/backup"
        return str(self.settings.value("paths/backup_dir", "/var/opt/mssql/backup"))

    def get_data_dir_setting(self) -> str:
        if hasattr(self, "settings_data_dir_input"):
            return self.settings_data_dir_input.text().strip() or "/var/opt/mssql/data"
        return str(self.settings.value("paths/data_dir", "/var/opt/mssql/data"))

    def test_settings_connection(self):
        """Testa a ligação SQL definida no Settings sem expor a password."""
        try:
            container_name, sql_user, sql_password = self.validate_connection_config(require_password=True)

            self.append_log("")
            self.append_log("🔌 A testar conexão definida no Settings...")
            self.append_log(f"Container: {container_name}")
            self.append_log(f"Utilizador: {sql_user}")

            databases = self.service.list_databases(
                container_name=container_name,
                sql_user=sql_user,
                sql_password=sql_password,
            )

            self.set_status_badge("success", "Conectado")
            self.status_label.setText("Conexão testada com sucesso.")
            self.step_label.setText(f"SQL Server respondeu. Bases encontradas: {len(databases)}.")
            self.append_log(f"✅ Conexão OK. Bases encontradas: {len(databases)}.")

            QMessageBox.information(
                self,
                "Conexão OK",
                "A conexão com o SQL Server foi testada com sucesso.\n\n"
                f"Container: {container_name}\n"
                f"Utilizador: {sql_user}\n"
                f"Bases encontradas: {len(databases)}",
            )

        except Exception as exc:
            self.show_connection_config_error(exc)

    def save_settings(self):
        self.session_sql_password = self.settings_session_password_input.text()
        save_password = False
        if hasattr(self, "settings_save_password_checkbox"):
            save_password = self.settings_save_password_checkbox.isChecked()

        if save_password and not self.session_sql_password:
            QMessageBox.warning(
                self,
                "Password vazia",
                "Marcou a opção para guardar a password, mas o campo Password está vazio."
            )
            return

        self.settings.setValue("connection/default_container", self.settings_default_container_input.text().strip() or DEFAULT_CONTAINER_NAME)
        self.settings.setValue("connection/default_user", self.settings_default_user_input.text().strip() or "sa")
        self.settings.setValue("connection/password_source", "settings")
        self.settings.setValue("connection/save_password", save_password)
        if save_password:
            self.settings.setValue("connection/saved_password", self._encode_saved_password(self.session_sql_password))
        else:
            self.settings.remove("connection/saved_password")
        self.settings.setValue("paths/backup_dir", self.get_backup_dir_setting())
        self.settings.setValue("paths/data_dir", self.get_data_dir_setting())
        self.settings.setValue("restore/confirm_overwrite", self.settings_confirm_overwrite_checkbox.isChecked())
        self.settings.setValue("restore/default_suffix", self.settings_restore_suffix_input.text().strip() or "_Restored")
        self.settings.setValue("restore/validate_after_restore", self.settings_validate_restore_checkbox.isChecked())
        self.settings.setValue("backup/use_compression", self.settings_backup_compression_checkbox.isChecked())
        self.settings.setValue("backup/verify_after_backup", self.settings_backup_verify_checkbox.isChecked())
        self.settings.setValue("backup/copy_only", self.settings_backup_copy_only_checkbox.isChecked())
        self.settings.setValue("backup/name_pattern", self.settings_backup_pattern_input.text().strip() or "{database}_{yyyyMMdd}_{HHmmss}.bak")
        self.settings.setValue("ui/theme", self.current_theme)
        self.settings.setValue("ui/language", self.current_language)
        self.settings.setValue("ui/open_maximized", self.settings_open_maximized_checkbox.isChecked())
        self.settings.setValue("logs/save_to_file", self.settings_save_logs_checkbox.isChecked())
        self.settings.setValue("logs/log_dir", self.settings_log_dir_input.text().strip() or "./logs")
        self.settings.sync()

        self.service = DockerSqlServerService(
            backup_dir=self.get_backup_dir_setting(),
            data_dir=self.get_data_dir_setting(),
        )

        default_container = self.settings_default_container_input.text().strip() or DEFAULT_CONTAINER_NAME
        default_user = self.settings_default_user_input.text().strip() or "sa"

        self.container_combo.setEditText(default_container)
        self.backup_container_combo.setEditText(default_container)
        self.databases_container_combo.setEditText(default_container)
        self.user_input.setText(default_user)
        self.backup_user_input.setText(default_user)
        self.databases_user_input.setText(default_user)
        self.password_input.setText(self.session_sql_password)
        self.backup_password_input.setText(self.session_sql_password)
        self.databases_password_input.setText(self.session_sql_password)
        self.verify_backup_checkbox.setChecked(self.settings_backup_verify_checkbox.isChecked())

        self.update_session_status()
        if save_password:
            self.append_log("✅ Configurações guardadas. A password foi guardada localmente por opção do utilizador.")
        else:
            self.append_log("✅ Configurações guardadas. A password ficou apenas na sessão atual.")
        self.set_status_badge("success", "Guardado")
        self.status_label.setText("Configurações guardadas.")
        self.step_label.setText("As novas preferências foram aplicadas.")
        self.update_summary_cards()

    def reset_settings(self):
        self.settings_default_container_input.setText(DEFAULT_CONTAINER_NAME)
        self.settings_default_user_input.setText("sa")
        self.settings_session_password_input.clear()
        if hasattr(self, "settings_save_password_checkbox"):
            self.settings_save_password_checkbox.setChecked(False)
        self.clear_session_password()
        self.settings_backup_dir_input.setText("/var/opt/mssql/backup")
        self.settings_data_dir_input.setText("/var/opt/mssql/data")
        self.settings_confirm_overwrite_checkbox.setChecked(True)
        self.settings_restore_suffix_input.setText("_Restored")
        self.settings_validate_restore_checkbox.setChecked(True)
        self.settings_backup_compression_checkbox.setChecked(True)
        self.settings_backup_verify_checkbox.setChecked(True)
        self.settings_backup_copy_only_checkbox.setChecked(False)
        self.settings_backup_pattern_input.setText("{database}_{yyyyMMdd}_{HHmmss}.bak")
        self.settings_open_maximized_checkbox.setChecked(True)
        self.settings_save_logs_checkbox.setChecked(False)
        self.settings_log_dir_input.setText("./logs")
        index = self.settings_theme_combo.findData("dark")
        if index >= 0:
            self.settings_theme_combo.setCurrentIndex(index)
        self.append_log("ℹ️ Configurações restauradas para o padrão. Clique em Guardar configurações para aplicar.")

    def apply_language_from_settings(self):
        language = self.settings_language_combo.currentData() or "pt_PT"
        self.apply_language(str(language))

    def apply_language(self, language: str):
        self.current_language = str(language) if str(language) in dict(available_languages()) else "pt_PT"
        set_language(self.current_language)
        self._apply_static_translations()
        # refresh the current page title/subtitle after language change
        if self.current_page == PAGE_RESTORE:
            self.show_restore_page()
        elif self.current_page == PAGE_BACKUP:
            self.show_backup_page()
        elif self.current_page == PAGE_DATABASES:
            self.show_databases_page()
        elif self.current_page == PAGE_SETTINGS:
            self.show_settings_page()

    def apply_theme_from_settings(self):
        theme = self.settings_theme_combo.currentData() or "dark"
        self.apply_theme(str(theme))

    def apply_theme(self, theme: str):
        self.current_theme = "light" if theme == "light" else "dark"
        self.setStyleSheet(get_app_qss(self.current_theme))
        self._apply_table_theme()
        self._set_nav_selected(self.current_page)

    def _apply_table_theme(self):
        if hasattr(self, "databases_table"):
            self.databases_table.setStyleSheet(get_table_qss(self.current_theme))


    def _set_translated_text(self, widget, source_text: str):
        widget.setProperty("_i18n_source_text", source_text)
        widget.setText(_(source_text))

    def _apply_static_translations(self):
        """
        Translate visible static Qt texts using the original Portuguese text as the key.

        Widgets keep their original text in a Qt property, so switching the language
        multiple times does not lose the source text.
        """
        for widget in self.findChildren(QWidget):
            if isinstance(widget, (QLabel, QPushButton, QCheckBox)):
                source = widget.property("_i18n_source_text")
                if source is None:
                    source = widget.text()
                    widget.setProperty("_i18n_source_text", source)
                if source:
                    widget.setText(_(str(source)))

            if isinstance(widget, QLineEdit):
                source = widget.property("_i18n_placeholder_text")
                if source is None:
                    source = widget.placeholderText()
                    widget.setProperty("_i18n_placeholder_text", source)
                if source:
                    widget.setPlaceholderText(_(str(source)))

            if isinstance(widget, QComboBox):
                for i in range(widget.count()):
                    source = widget.itemData(i, Qt.UserRole + 10)
                    if source is None:
                        source = widget.itemText(i)
                        widget.setItemData(i, source, Qt.UserRole + 10)
                    # Do not translate language names themselves.
                    if widget is getattr(self, "settings_language_combo", None):
                        continue
                    widget.setItemText(i, _(str(source)))

        if hasattr(self, "databases_table"):
            headers = ["Base", "Estado", "Recovery", "Collation", "Compat.", "Tamanho MB"]
            self.databases_table.setHorizontalHeaderLabels([_(h) for h in headers])

        if hasattr(self, "settings_language_combo"):
            for i, (code, label) in enumerate(available_languages()):
                self.settings_language_combo.setItemText(i, label)

        self.update_save_password_button_style()
        self.update_session_status()
        self.update_summary_cards()
        self._apply_table_theme()

    # -------------------------------------------------------------------------
    # Containers, backups e bases
    # -------------------------------------------------------------------------

    def refresh_containers(self):
        self.append_log("🔄 A procurar containers SQL Server...")

        try:
            containers = self.service.list_sqlserver_containers()

            current_restore_text = self.container_combo.currentText().strip()
            current_backup_text = self.backup_container_combo.currentText().strip()
            current_databases_text = self.databases_container_combo.currentText().strip()

            self.container_combo.clear()
            self.backup_container_combo.clear()
            self.databases_container_combo.clear()

            for container in containers:
                label = f"{container.name}  |  {container.image}"
                icon = self._icon("fa5s.cube", color="#93C5FD")

                self.container_combo.addItem(icon, label, container.name)
                self.backup_container_combo.addItem(icon, label, container.name)
                self.databases_container_combo.addItem(icon, label, container.name)

            if containers:
                default_container = self.get_default_container_setting()
                selected_index = 0

                for i, container in enumerate(containers):
                    if container.name == default_container:
                        selected_index = i
                        break

                self.container_combo.setCurrentIndex(selected_index)
                self.backup_container_combo.setCurrentIndex(selected_index)
                self.databases_container_combo.setCurrentIndex(selected_index)

                selected_name = self._get_combo_container_name(self.container_combo)
                self.append_log(f"✅ {len(containers)} container(s) encontrado(s).")
                self.append_log(f"ℹ️ Container ativo definido pelo Settings: {selected_name}")
                self.update_summary_cards()
                self.refresh_backups()

            else:
                default_container = self.get_default_container_setting()
                self.container_combo.setEditText(current_restore_text or default_container)
                self.backup_container_combo.setEditText(current_backup_text or default_container)
                self.databases_container_combo.setEditText(current_databases_text or default_container)

                self.append_log("⚠️ Nenhum container SQL Server encontrado automaticamente.")
                self.append_log("Pode escrever manualmente o nome do container no campo acima.")
                self.update_summary_cards()

        except Exception as exc:
            self.append_log("❌ Erro ao listar containers:")
            self.append_log(str(exc))
            self.set_status_badge("error", "Erro")

    def refresh_backups(self):
        try:
            container_name, _, _ = self.validate_connection_config(require_password=False)
        except Exception as exc:
            self.show_connection_config_error(exc)
            return

        self.append_log("")
        self.append_log(f"🔄 A listar backups em {container_name}...")

        try:
            backups = self.service.list_backups(container_name)

            self.backup_combo.clear()

            for backup in backups:
                self.backup_combo.addItem(self._icon("fa5s.file-archive", color="#93C5FD"), backup)

            if backups:
                self.append_log(f"✅ {len(backups)} backup(s) encontrado(s).")

                if not self.database_input.text().strip():
                    suggested_name = backups[0].rsplit(".", 1)[0]
                    suffix = str(self.settings.value("restore/default_suffix", "_Restored"))
                    self.database_input.setText(f"{suggested_name}{suffix}")
            else:
                self.append_log("⚠️ Nenhum ficheiro .bak encontrado em /var/opt/mssql/backup.")

            self.update_summary_cards()

        except Exception as exc:
            self.append_log("❌ Erro ao listar backups:")
            self.append_log(str(exc))
            self.set_status_badge("error", "Erro")

    def refresh_databases(self):
        """
        Carrega bases para o menu Backup usando a ligação definida em Settings.
        """
        try:
            container_name, sql_user, sql_password = self.validate_connection_config(require_password=True)
        except Exception as exc:
            self.show_connection_config_error(exc)
            return

        self.append_log("")
        self.append_log(f"🔄 A listar bases em {container_name} com o utilizador {sql_user}...")

        try:
            databases = self.service.list_databases(
                container_name=container_name,
                sql_user=sql_user,
                sql_password=sql_password,
            )

            self.source_database_combo.clear()

            for database in databases:
                self.source_database_combo.addItem(self._icon("fa5s.database", color="#93C5FD"), database)

            if databases:
                self.append_log(f"✅ {len(databases)} base(s) encontrada(s).")
                self.generate_backup_filename()
            else:
                self.append_log("⚠️ Nenhuma base de utilizador encontrada.")

            self.update_summary_cards()

        except Exception as exc:
            self.append_log("❌ Erro ao listar bases:")
            self.append_log(str(exc))
            self.set_status_badge("error", "Erro")

    def refresh_database_list(self):
        """
        Carrega a tabela do menu Databases usando a ligação definida em Settings.
        """
        try:
            container_name, sql_user, sql_password = self.validate_connection_config(require_password=True)
        except Exception as exc:
            self.show_connection_config_error(exc)
            return

        self.append_log("")
        self.append_log(f"🔄 A consultar bases em {container_name} com o utilizador {sql_user}...")
        self.status_label.setText("A consultar bases...")
        self.step_label.setText("A carregar lista de bases.")
        self.set_status_badge("running", "A consultar")

        try:
            databases = self.service.list_database_details(
                container_name=container_name,
                sql_user=sql_user,
                sql_password=sql_password,
            )

            self.databases_table.setRowCount(0)

            for row, database in enumerate(databases):
                self.databases_table.insertRow(row)
                self.databases_table.setItem(row, 0, QTableWidgetItem(database.name))
                self.databases_table.setItem(row, 1, QTableWidgetItem(database.state_desc))
                self.databases_table.setItem(row, 2, QTableWidgetItem(database.recovery_model_desc))
                self.databases_table.setItem(row, 3, QTableWidgetItem(database.collation_name or ""))
                self.databases_table.setItem(row, 4, QTableWidgetItem(str(database.compatibility_level)))
                self.databases_table.setItem(row, 5, QTableWidgetItem(f"{database.size_mb:.2f}"))

            if databases:
                self.append_log(f"✅ {len(databases)} base(s) encontrada(s).")
                self.status_label.setText("Lista de bases atualizada.")
                self.step_label.setText("Consulta concluída.")
                self.set_status_badge("success", "Atualizado")
            else:
                self.append_log("⚠️ Nenhuma base de utilizador encontrada.")
                self.status_label.setText("Nenhuma base encontrada.")
                self.step_label.setText("Consulta concluída sem bases de utilizador.")
                self.set_status_badge("ready", "Sem bases")

            self.update_summary_cards()

        except Exception as exc:
            self.append_log("❌ Erro ao consultar bases:")
            self.append_log(str(exc))
            self.status_label.setText("Erro ao consultar bases.")
            self.step_label.setText("Veja o erro técnico completo nos logs.")
            self.set_status_badge("error", "Erro")
            QMessageBox.critical(
                self,
                "Erro ao consultar bases",
                "Não foi possível consultar as bases.\n\nVeja o log completo para perceber o motivo.",
            )

    # -------------------------------------------------------------------------
    # Restore

    # -------------------------------------------------------------------------

    def start_restore(self):
        try:
            container_name, sql_user, sql_password = self.validate_connection_config(require_password=True)
        except Exception as exc:
            self.show_connection_config_error(exc)
            return

        backup_file = self.backup_combo.currentText().strip()
        database_name = self.database_input.text().strip()

        if not backup_file:
            QMessageBox.warning(self, "Atenção", "Escolha um ficheiro .bak.")
            return

        if not database_name:
            QMessageBox.warning(self, "Atenção", "Informe o nome da base destino.")
            return

        try:
            self.status_label.setText("A verificar se a base destino já existe...")
            self.step_label.setText("A verificar base destino...")
            self.set_status_badge("running", "A verificar")

            database_info = self.service.get_database_info(
                container_name=container_name,
                sql_user=sql_user,
                sql_password=sql_password,
                database_name=database_name,
            )

            if database_info is not None and self.settings_confirm_overwrite_checkbox.isChecked():
                dialog = ConfirmRestoreDialog(
                    container_name=container_name,
                    backup_file=backup_file,
                    database_name=database_name,
                    database_info=database_info,
                    parent=self,
                )

                result = dialog.exec()

                if result != QDialog.Accepted:
                    self.status_label.setText("Restore cancelado pelo utilizador.")
                    self.step_label.setText("Operação cancelada antes de alterar a base.")
                    self.set_status_badge("ready", "Cancelado")
                    self.append_log("")
                    self.append_log("⚠️ Restore cancelado pelo utilizador.")
                    return

        except Exception as exc:
            self.set_status_badge("error", "Erro")
            self.status_label.setText("Erro ao verificar base destino.")
            self.step_label.setText("Não foi possível verificar se a base já existe.")

            self.append_log("")
            self.append_log("❌ Erro ao verificar se a base destino já existe:")
            self.append_log(str(exc))

            QMessageBox.critical(
                self,
                "Erro ao verificar base",
                "Não foi possível verificar se a base destino já existe.\n\n"
                "Veja o log completo para perceber o motivo.",
            )
            return

        self.progress_bar.setValue(0)
        self.step_progress.show()
        self.step_progress.reset()
        self.step_progress.set_active_step(0)

        self.status_label.setText("Restore iniciado...")
        self.step_label.setText("A preparar operação...")
        self.set_status_badge("running", "A restaurar")

        self.append_log("")
        self.append_log("=" * 90)
        self.append_log("🚀 RESTORE INICIADO")
        self.append_log(f"Container: {container_name}")
        self.append_log(f"Utilizador SQL: {sql_user}")
        self.append_log(f"Backup: {backup_file}")
        self.append_log(f"Base destino: {database_name}")
        self.append_log("=" * 90)

        self.set_operation_running(True)

        self.restore_thread = QThread()
        self.restore_worker = RestoreWorker(
            container_name=container_name,
            sql_user=sql_user,
            sql_password=sql_password,
            backup_file=backup_file,
            database_name=database_name,
            backup_dir=self.get_backup_dir_setting(),
            data_dir=self.get_data_dir_setting(),
            validate_after_restore=self.settings_validate_restore_checkbox.isChecked(),
        )

        self.restore_worker.moveToThread(self.restore_thread)
        self.restore_thread.started.connect(self.restore_worker.run)

        self.restore_worker.log.connect(self.append_log)
        self.restore_worker.progress.connect(self.update_progress)
        self.restore_worker.finished.connect(self.restore_finished)

        self.restore_worker.finished.connect(self.restore_thread.quit)
        self.restore_worker.finished.connect(self.restore_worker.deleteLater)
        self.restore_thread.finished.connect(self.restore_thread.deleteLater)
        self.restore_thread.finished.connect(self.cleanup_restore_thread)

        self.restore_thread.start()

    def restore_finished(self, success: bool, message: str):
        self.set_operation_running(False)

        if success:
            self.progress_bar.setValue(100)
            self.step_progress.mark_all_done()
            self.status_label.setText("Restore concluído com sucesso.")
            self.step_label.setText("Base restaurada e validada.")
            self.set_status_badge("success", "Sucesso")
            QMessageBox.information(self, "Sucesso", message)
        else:
            self.step_progress.mark_error()
            self.status_label.setText("Restore falhou.")
            self.step_label.setText("Veja o erro técnico completo nos logs.")
            self.set_status_badge("error", "Falhou")
            QMessageBox.critical(
                self,
                "Erro no restore",
                "O restore falhou.\n\nVeja o log completo na área de logs para perceber o motivo.",
            )

    def cleanup_restore_thread(self):
        self.restore_thread = None
        self.restore_worker = None

    # -------------------------------------------------------------------------
    # Backup
    # -------------------------------------------------------------------------

    def on_source_database_changed(self):
        if self.current_page == PAGE_BACKUP:
            self.generate_backup_filename()
        self.update_summary_cards()

    def generate_backup_filename(self):
        database_name = self.source_database_combo.currentText().strip()

        if not database_name:
            return

        try:
            safe_name = self.service._safe_file_base(database_name)
            now = datetime.now()
            pattern = self.settings_backup_pattern_input.text().strip() or "{database}_{yyyyMMdd}_{HHmmss}.bak"
            filename = (
                pattern
                .replace("{database}", safe_name)
                .replace("{yyyyMMdd}", now.strftime("%Y%m%d"))
                .replace("{HHmmss}", now.strftime("%H%M%S"))
            )

            if not filename.lower().endswith(".bak"):
                filename += ".bak"

            self.backup_file_input.setText(filename)
            self.update_summary_cards()
        except Exception as exc:
            self.append_log("❌ Erro ao gerar nome do backup:")
            self.append_log(str(exc))

    def start_backup(self):
        try:
            container_name, sql_user, sql_password = self.validate_connection_config(require_password=True)
        except Exception as exc:
            self.show_connection_config_error(exc)
            return

        database_name = self.source_database_combo.currentText().strip()
        backup_file = self.backup_file_input.text().strip()
        verify_after_backup = self.verify_backup_checkbox.isChecked()

        if not database_name:
            QMessageBox.warning(self, "Atenção", "Escolha a base origem.")
            return

        if not backup_file:
            QMessageBox.warning(self, "Atenção", "Informe o nome do ficheiro .bak.")
            return

        if not backup_file.lower().endswith(".bak"):
            QMessageBox.warning(self, "Atenção", "O ficheiro precisa terminar com .bak.")
            return

        self.progress_bar.setValue(0)
        self.step_progress.hide()
        self.status_label.setText("Backup iniciado...")
        self.step_label.setText("A preparar backup...")
        self.set_status_badge("running", "A fazer backup")

        self.append_log("")
        self.append_log("=" * 90)
        self.append_log("📦 BACKUP INICIADO")
        self.append_log(f"Container: {container_name}")
        self.append_log(f"Utilizador SQL: {sql_user}")
        self.append_log(f"Base origem: {database_name}")
        self.append_log(f"Ficheiro destino: {backup_file}")
        self.append_log("=" * 90)

        self.set_operation_running(True)

        self.backup_thread = QThread()
        self.backup_worker = BackupWorker(
            container_name=container_name,
            sql_user=sql_user,
            sql_password=sql_password,
            database_name=database_name,
            backup_file=backup_file,
            verify_after_backup=verify_after_backup,
            backup_dir=self.get_backup_dir_setting(),
            use_compression=self.settings_backup_compression_checkbox.isChecked(),
            copy_only=self.settings_backup_copy_only_checkbox.isChecked(),
        )

        self.backup_worker.moveToThread(self.backup_thread)
        self.backup_thread.started.connect(self.backup_worker.run)

        self.backup_worker.log.connect(self.append_log)
        self.backup_worker.progress.connect(self.update_progress)
        self.backup_worker.finished.connect(self.backup_finished)

        self.backup_worker.finished.connect(self.backup_thread.quit)
        self.backup_worker.finished.connect(self.backup_worker.deleteLater)
        self.backup_thread.finished.connect(self.backup_thread.deleteLater)
        self.backup_thread.finished.connect(self.cleanup_backup_thread)

        self.backup_thread.start()

    def backup_finished(self, success: bool, message: str):
        self.set_operation_running(False)

        if success:
            self.progress_bar.setValue(100)
            self.status_label.setText("Backup concluído com sucesso.")
            self.step_label.setText("Backup criado em /var/opt/mssql/backup.")
            self.set_status_badge("success", "Sucesso")
            QMessageBox.information(self, "Sucesso", message)
        else:
            self.status_label.setText("Backup falhou.")
            self.step_label.setText("Veja o erro técnico completo nos logs.")
            self.set_status_badge("error", "Falhou")
            QMessageBox.critical(
                self,
                "Erro no backup",
                "O backup falhou.\n\nVeja o log completo na área de logs para perceber o motivo.",
            )

    def cleanup_backup_thread(self):
        self.backup_thread = None
        self.backup_worker = None

    # -------------------------------------------------------------------------
    # Estado da interface
    # -------------------------------------------------------------------------

    def set_operation_running(self, running: bool):
        widgets = [
            self.restore_button,
            self.refresh_backups_button,
            self.refresh_containers_button,
            self.container_combo,
            self.backup_combo,
            self.database_input,
            self.user_input,
            self.password_input,
            self.clear_log_button,
            self.start_backup_button,
            self.refresh_databases_button,
            self.refresh_backup_containers_button,
            self.backup_container_combo,
            self.backup_user_input,
            self.backup_password_input,
            self.source_database_combo,
            self.backup_file_input,
            self.generate_backup_name_button,
            self.verify_backup_checkbox,
            self.refresh_database_containers_button,
            self.databases_container_combo,
            self.databases_user_input,
            self.databases_password_input,
            self.refresh_database_list_button,
            self.restore_nav_button,
            self.backup_nav_button,
            self.databases_nav_button,
            self.settings_nav_button,
            self.save_settings_button,
            self.reset_settings_button,
        ]

        for widget in widgets:
            widget.setEnabled(not running)

    def update_progress(self, value: int, text: str):
        self.progress_bar.setValue(value)
        self.status_label.setText(text)
        self.step_label.setText(text)

        if self.current_page == PAGE_RESTORE and hasattr(self, "step_progress"):
            self.step_progress.update_by_progress(value)

    # -------------------------------------------------------------------------
    # Logs
    # -------------------------------------------------------------------------

    def append_log(self, text: str):
        self.log_output.appendPlainText(text)
        scrollbar = self.log_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def copy_log(self):
        QApplication.clipboard().setText(self.log_output.toPlainText())
        self.status_label.setText("Log copiado para a área de transferência.")
        self.step_label.setText("Log copiado.")

    def clear_log(self):
        self.log_output.clear()
        self.progress_bar.setValue(0)

        if hasattr(self, "step_progress"):
            self.step_progress.reset()
            if self.current_page == PAGE_RESTORE:
                self.step_progress.show()
            else:
                self.step_progress.hide()

        self.status_label.setText("Pronto.")
        if self.current_page == PAGE_RESTORE:
            self._set_translated_text(self.step_label, "Aguardando uma operação.")
        elif self.current_page == PAGE_BACKUP:
            self._set_translated_text(self.step_label, "Aguardando backup.")
        elif self.current_page == PAGE_DATABASES:
            self._set_translated_text(self.step_label, "Aguardando consulta de bases.")
        else:
            self._set_translated_text(self.step_label, "Configurações locais da aplicação.")
        self.set_status_badge("ready", "Pronto")

    # -------------------------------------------------------------------------
    # Utilitários
    # -------------------------------------------------------------------------

    def _set_window_icon(self):
        from pathlib import Path
        icon_path = Path(__file__).resolve().parent.parent / "assets" / "app_icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

    def get_selected_container_name(self) -> str:
        # Restore usa sempre o container definido em Settings.
        return self.get_default_container_setting()

    def get_selected_backup_container_name(self) -> str:
        # Backup usa sempre o container definido em Settings.
        return self.get_default_container_setting()

    def get_selected_databases_container_name(self) -> str:
        # Databases usa sempre o container definido em Settings.
        return self.get_default_container_setting()

    def _get_combo_container_name(self, combo: QComboBox) -> str:
        current_data = combo.currentData()

        if current_data:
            return str(current_data).strip()

        text = combo.currentText().strip()

        if "|" in text:
            return text.split("|", 1)[0].strip()

        return text
