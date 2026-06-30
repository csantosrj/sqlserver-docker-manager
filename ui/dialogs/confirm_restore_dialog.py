from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from services.docker_sqlserver import DatabaseInfo
from ui.styles import APP_QSS
from i18n import tr as _


class ConfirmRestoreDialog(QDialog):
    """
    Janela de confirmação antes de sobrescrever uma base existente.

    A ideia é evitar restauração acidental por cima de uma base importante.
    """

    def __init__(
        self,
        container_name: str,
        backup_file: str,
        database_name: str,
        database_info: DatabaseInfo,
        parent=None,
    ):
        super().__init__(parent)

        self.container_name = container_name
        self.backup_file = backup_file
        self.database_name = database_name
        self.database_info = database_info

        self.setWindowTitle(_("Confirmar restore"))
        self.setMinimumWidth(620)
        self.setModal(True)
        self.setStyleSheet(APP_QSS)

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        title = QLabel(_("A base destino já existe"))
        title.setStyleSheet(
            """
            font-size: 22px;
            font-weight: 700;
            color: #FCA5A5;
            """
        )

        subtitle = QLabel(
            _("O restore irá substituir a base existente usando WITH REPLACE. "
              "Esta ação pode apagar os dados atuais da base destino.")
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(
            """
            color: #D1D5DB;
            font-size: 13px;
            """
        )

        layout.addWidget(title)
        layout.addWidget(subtitle)

        warning_card = QFrame()
        warning_card.setStyleSheet(
            """
            QFrame {
                background-color: rgba(239, 68, 68, 0.12);
                border: 1px solid rgba(239, 68, 68, 0.45);
                border-radius: 14px;
            }
            """
        )

        warning_layout = QVBoxLayout(warning_card)
        warning_layout.setContentsMargins(18, 16, 18, 16)

        warning_text = QLabel(
            _("Atenção: a base atual será colocada em SINGLE_USER, "
              "as ligações serão derrubadas e a base será restaurada por cima.")
        )
        warning_text.setWordWrap(True)
        warning_text.setStyleSheet(
            """
            color: #FECACA;
            font-weight: 600;
            background-color: transparent;
            border: none;
            """
        )

        warning_layout.addWidget(warning_text)
        layout.addWidget(warning_card)

        details_card = QFrame()
        details_card.setObjectName("card")

        details_layout = QGridLayout(details_card)
        details_layout.setContentsMargins(18, 16, 18, 16)
        details_layout.setHorizontalSpacing(18)
        details_layout.setVerticalSpacing(10)

        self._add_detail(details_layout, 0, _("Container:"), self.container_name)
        self._add_detail(details_layout, 1, _("Backup:"), self.backup_file)
        self._add_detail(details_layout, 2, _("Base destino:"), self.database_name)
        self._add_detail(details_layout, 3, _("Estado atual:"), self.database_info.state_desc)
        self._add_detail(
            details_layout,
            4,
            _("Collation atual:"),
            self.database_info.collation_name or _("Sem collation"),
        )

        layout.addWidget(details_card)

        self.confirm_checkbox = QCheckBox(
            _("Confirmo que quero sobrescrever esta base de dados.")
        )
        self.confirm_checkbox.setStyleSheet(
            """
            QCheckBox {
                color: #E5E7EB;
                font-weight: 600;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            """
        )
        self.confirm_checkbox.stateChanged.connect(self._on_checkbox_changed)

        layout.addWidget(self.confirm_checkbox)

        buttons = QHBoxLayout()
        buttons.addStretch()

        self.cancel_button = QPushButton(_("Cancelar"))
        self.cancel_button.setObjectName("secondaryButton")
        self.cancel_button.clicked.connect(self.reject)

        self.confirm_button = QPushButton(_("Sim, restaurar por cima"))
        self.confirm_button.setObjectName("primaryButton")
        self.confirm_button.setEnabled(False)
        self.confirm_button.clicked.connect(self.accept)

        buttons.addWidget(self.cancel_button)
        buttons.addWidget(self.confirm_button)

        layout.addLayout(buttons)

    def _add_detail(self, layout: QGridLayout, row: int, label: str, value: str):
        label_widget = QLabel(label)
        label_widget.setStyleSheet(
            """
            color: #9CA3AF;
            font-weight: 600;
            background-color: transparent;
            border: none;
            """
        )

        value_widget = QLabel(value)
        value_widget.setWordWrap(True)
        value_widget.setStyleSheet(
            """
            color: #F9FAFB;
            font-weight: 600;
            background-color: transparent;
            border: none;
            """
        )

        layout.addWidget(label_widget, row, 0, Qt.AlignTop)
        layout.addWidget(value_widget, row, 1, Qt.AlignTop)

    def _on_checkbox_changed(self):
        self.confirm_button.setEnabled(self.confirm_checkbox.isChecked())