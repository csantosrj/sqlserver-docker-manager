from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

try:
    import qtawesome as qta
except ImportError:
    qta = None


class StepProgress(QWidget):
    """
    Componente visual para mostrar as etapas do restore.

    Estados possíveis:
    - pending
    - active
    - done
    - error
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.steps = [
            {
                "title": "Verificar backup",
                "description": "Confirma se o .bak existe",
            },
            {
                "title": "Ler estrutura",
                "description": "Executa FILELISTONLY",
            },
            {
                "title": "Preparar restore",
                "description": "Monta comandos SQL",
            },
            {
                "title": "Restaurar database",
                "description": "Executa RESTORE DATABASE",
            },
            {
                "title": "Validar resultado",
                "description": "Confirma base restaurada",
            },
        ]

        self.step_widgets = []
        self.current_step = 0

        self._build_ui()
        self.reset()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(10)

        for index, step in enumerate(self.steps):
            step_card = QFrame()
            step_card.setMinimumHeight(82)

            card_layout = QHBoxLayout(step_card)
            card_layout.setContentsMargins(12, 10, 12, 10)
            card_layout.setSpacing(10)

            icon_label = QLabel()
            icon_label.setFixedSize(30, 30)
            icon_label.setAlignment(Qt.AlignCenter)

            text_layout = QVBoxLayout()
            text_layout.setSpacing(2)

            title_label = QLabel(step["title"])
            title_label.setWordWrap(True)

            description_label = QLabel(step["description"])
            description_label.setWordWrap(True)

            text_layout.addWidget(title_label)
            text_layout.addWidget(description_label)

            card_layout.addWidget(icon_label)
            card_layout.addLayout(text_layout)

            layout.addWidget(step_card, 1)

            self.step_widgets.append(
                {
                    "card": step_card,
                    "icon": icon_label,
                    "title": title_label,
                    "description": description_label,
                    "status": "pending",
                }
            )

    def reset(self):
        self.current_step = 0

        for index in range(len(self.step_widgets)):
            self.set_step_status(index, "pending")

    def set_step_status(self, index: int, status: str):
        if index < 0 or index >= len(self.step_widgets):
            return

        item = self.step_widgets[index]
        item["status"] = status

        if status == "pending":
            icon = self._icon("fa5s.circle", "#64748B")
            icon_bg = "rgba(100, 116, 139, 0.12)"
            icon_border = "rgba(100, 116, 139, 0.25)"
            card_bg = "#111827"
            card_border = "#1F2937"
            title_color = "#CBD5E1"
            description_color = "#64748B"

        elif status == "active":
            icon = self._icon("fa5s.spinner", "#FCD34D")
            icon_bg = "rgba(245, 158, 11, 0.16)"
            icon_border = "rgba(245, 158, 11, 0.42)"
            card_bg = "#161C2D"
            card_border = "#F59E0B"
            title_color = "#FDE68A"
            description_color = "#D1D5DB"

        elif status == "done":
            icon = self._icon("fa5s.check", "#6EE7B7")
            icon_bg = "rgba(16, 185, 129, 0.16)"
            icon_border = "rgba(16, 185, 129, 0.42)"
            card_bg = "#10231F"
            card_border = "#059669"
            title_color = "#A7F3D0"
            description_color = "#9CA3AF"

        elif status == "error":
            icon = self._icon("fa5s.times", "#FCA5A5")
            icon_bg = "rgba(239, 68, 68, 0.16)"
            icon_border = "rgba(239, 68, 68, 0.42)"
            card_bg = "#2A1216"
            card_border = "#EF4444"
            title_color = "#FCA5A5"
            description_color = "#D1D5DB"

        else:
            return

        item["card"].setStyleSheet(
            f"""
            QFrame {{
                background-color: {card_bg};
                border: 1px solid {card_border};
                border-radius: 12px;
            }}
            """
        )

        item["icon"].setPixmap(icon.pixmap(QSize(14, 14)))
        item["icon"].setStyleSheet(
            f"""
            QLabel {{
                background-color: {icon_bg};
                border: 1px solid {icon_border};
                border-radius: 15px;
            }}
            """
        )

        item["title"].setStyleSheet(
            f"""
            color: {title_color};
            font-size: 12px;
            font-weight: 700;
            background-color: transparent;
            border: none;
            """
        )

        item["description"].setStyleSheet(
            f"""
            color: {description_color};
            font-size: 11px;
            background-color: transparent;
            border: none;
            """
        )

    def set_active_step(self, index: int):
        self.current_step = index

        for i in range(len(self.step_widgets)):
            if i < index:
                self.set_step_status(i, "done")
            elif i == index:
                self.set_step_status(i, "active")
            else:
                self.set_step_status(i, "pending")

    def mark_all_done(self):
        for i in range(len(self.step_widgets)):
            self.set_step_status(i, "done")

    def mark_error(self):
        self.set_step_status(self.current_step, "error")

    def update_by_progress(self, value: int):
        """
        Mapeia o progresso numérico para etapas visuais.

        O worker atual já emite:
        5, 20, 40, 55, 98, 100
        """
        if value < 20:
            self.set_active_step(0)
        elif value < 40:
            self.set_active_step(1)
        elif value < 55:
            self.set_active_step(2)
        elif value < 98:
            self.set_active_step(3)
        elif value < 100:
            self.set_active_step(4)
        else:
            self.mark_all_done()

    def _icon(self, name: str, color: str) -> QIcon:
        if qta is None:
            return QIcon()

        try:
            return qta.icon(name, color=color)
        except Exception:
            return QIcon()