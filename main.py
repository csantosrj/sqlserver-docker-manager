import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow


def resource_path(relative_path: str) -> str:
    """
    Resolve caminho de ficheiros tanto em modo normal
    como futuramente empacotado com PyInstaller.
    """
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return str(base_path / relative_path)


def main():
    app = QApplication(sys.argv)

    icon_path = resource_path("assets/app_icon.png")
    app_icon = QIcon(icon_path)

    app.setWindowIcon(app_icon)

    window = MainWindow()
    window.setWindowIcon(app_icon)
    window.showMaximized()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()