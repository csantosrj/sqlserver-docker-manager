DARK_QSS = """
QMainWindow { background-color: #0F172A; }
QWidget { background-color: #0F172A; color: #E5E7EB; font-family: "Segoe UI", "Inter", "Arial"; font-size: 13px; }
QFrame#sidebar { background-color: #111827; border-right: 1px solid #1F2937; }
QFrame#contentPanel { background-color: #0F172A; }
QFrame#card { background-color: #111827; border: 1px solid #1F2937; border-radius: 14px; }
QFrame#smallCard { background-color: #111827; border: 1px solid #1F2937; border-radius: 12px; }
QLabel#appTitle { font-size: 20px; font-weight: 700; color: #F9FAFB; }
QLabel#appSubtitle { font-size: 12px; color: #9CA3AF; }
QLabel#pageTitle { font-size: 24px; font-weight: 700; color: #F9FAFB; }
QLabel#pageSubtitle { font-size: 13px; color: #9CA3AF; }
QLabel#sectionTitle { font-size: 16px; font-weight: 700; color: #F9FAFB; }
QLabel#mutedLabel { color: #9CA3AF; }
QLabel#cardValue { font-size: 16px; font-weight: 700; color: #F9FAFB; }
QLabel#cardHint { font-size: 12px; color: #9CA3AF; }
QLabel#statusBadge { padding: 7px 12px; border-radius: 14px; font-weight: 600; }
QPushButton { background-color: #1F2937; color: #E5E7EB; border: 1px solid #374151; border-radius: 10px; padding: 9px 14px; font-weight: 600; }
QPushButton:hover { background-color: #273449; border: 1px solid #4B5563; }
QPushButton:pressed { background-color: #111827; }
QPushButton:disabled { background-color: #111827; color: #6B7280; border: 1px solid #1F2937; }
QPushButton#primaryButton { background-color: #2563EB; border: 1px solid #3B82F6; color: white; }
QPushButton#primaryButton:hover { background-color: #1D4ED8; }
QPushButton#successButton { background-color: #059669; border: 1px solid #10B981; color: white; }
QPushButton#successButton:hover { background-color: #047857; }
QPushButton#secondaryButton { background-color: #1F2937; border: 1px solid #374151; }
QPushButton#ghostButton { background-color: transparent; border: 1px solid transparent; color: #9CA3AF; text-align: left; padding: 10px 12px; }
QPushButton#ghostButton:hover { background-color: #1F2937; color: #F9FAFB; }
QPushButton#navButton { background-color: transparent; border: 1px solid transparent; color: #9CA3AF; text-align: left; padding: 11px 14px; border-radius: 10px; }
QPushButton#navButton:hover { background-color: #1F2937; color: #F9FAFB; }
QPushButton#navButtonSelected { background-color: #1D4ED8; border: 1px solid #2563EB; color: #FFFFFF; text-align: left; padding: 11px 14px; border-radius: 10px; }
QPushButton#navButtonDanger { background-color: transparent; border: 1px solid transparent; color: #FCA5A5; text-align: left; padding: 11px 14px; border-radius: 10px; }
QPushButton#navButtonDanger:hover { background-color: rgba(239, 68, 68, 0.14); border: 1px solid rgba(239, 68, 68, 0.25); color: #F87171; }
QLineEdit, QComboBox { background-color: #020617; border: 1px solid #334155; border-radius: 10px; padding: 9px 11px; color: #F9FAFB; selection-background-color: #2563EB; }
QLineEdit:focus, QComboBox:focus { border: 1px solid #3B82F6; }
QLineEdit:disabled, QComboBox:disabled { background-color: #111827; color: #6B7280; border: 1px solid #1F2937; }
QComboBox::drop-down { border: none; width: 32px; }
QComboBox QAbstractItemView { background-color: #111827; color: #E5E7EB; border: 1px solid #374151; selection-background-color: #2563EB; outline: none; }
QCheckBox { color: #E5E7EB; spacing: 8px; }
QCheckBox::indicator { width: 18px; height: 18px; }
QPlainTextEdit#logOutput { background-color: #020617; border: 1px solid #1F2937; border-radius: 12px; color: #D1D5DB; font-family: "Consolas", "Cascadia Mono", "Courier New"; font-size: 12px; padding: 10px; }
QProgressBar { background-color: #020617; border: 1px solid #1F2937; border-radius: 10px; height: 18px; text-align: center; color: #F9FAFB; font-weight: 600; }
QProgressBar::chunk { background-color: #2563EB; border-radius: 9px; }
QScrollArea { background-color: #0F172A; border: none; }
QScrollBar:vertical { background-color: #020617; width: 10px; margin: 0; }
QScrollBar::handle:vertical { background-color: #374151; min-height: 24px; border-radius: 5px; }
QScrollBar::handle:vertical:hover { background-color: #4B5563; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""

LIGHT_QSS = """
QMainWindow { background-color: #F4F7FB; }
QWidget { background-color: #F4F7FB; color: #111827; font-family: "Segoe UI", "Inter", "Arial"; font-size: 13px; }
QFrame#sidebar { background-color: #FFFFFF; border-right: 1px solid #E5E7EB; }
QFrame#contentPanel { background-color: #F4F7FB; }
QFrame#card { background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 14px; }
QFrame#smallCard { background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px; }
QLabel#appTitle { font-size: 20px; font-weight: 700; color: #111827; }
QLabel#appSubtitle { font-size: 12px; color: #6B7280; }
QLabel#pageTitle { font-size: 24px; font-weight: 700; color: #111827; }
QLabel#pageSubtitle { font-size: 13px; color: #6B7280; }
QLabel#sectionTitle { font-size: 16px; font-weight: 700; color: #111827; }
QLabel#mutedLabel { color: #6B7280; }
QLabel#cardValue { font-size: 16px; font-weight: 700; color: #111827; }
QLabel#cardHint { font-size: 12px; color: #6B7280; }
QLabel#statusBadge { padding: 7px 12px; border-radius: 14px; font-weight: 600; }
QPushButton { background-color: #F9FAFB; color: #111827; border: 1px solid #D1D5DB; border-radius: 10px; padding: 9px 14px; font-weight: 600; }
QPushButton:hover { background-color: #EFF6FF; border: 1px solid #93C5FD; }
QPushButton:pressed { background-color: #DBEAFE; }
QPushButton:disabled { background-color: #F3F4F6; color: #9CA3AF; border: 1px solid #E5E7EB; }
QPushButton#primaryButton { background-color: #2563EB; border: 1px solid #2563EB; color: white; }
QPushButton#primaryButton:hover { background-color: #1D4ED8; }
QPushButton#successButton { background-color: #059669; border: 1px solid #059669; color: white; }
QPushButton#successButton:hover { background-color: #047857; }
QPushButton#secondaryButton { background-color: #F9FAFB; border: 1px solid #D1D5DB; color: #111827; }
QPushButton#navButton { background-color: transparent; border: 1px solid transparent; color: #4B5563; text-align: left; padding: 11px 14px; border-radius: 10px; }
QPushButton#navButton:hover { background-color: #EFF6FF; color: #1D4ED8; }
QPushButton#navButtonSelected { background-color: #2563EB; border: 1px solid #2563EB; color: #FFFFFF; text-align: left; padding: 11px 14px; border-radius: 10px; }
QPushButton#navButtonDanger { background-color: transparent; border: 1px solid transparent; color: #B91C1C; text-align: left; padding: 11px 14px; border-radius: 10px; }
QPushButton#navButtonDanger:hover { background-color: #FEE2E2; border: 1px solid #FCA5A5; color: #991B1B; }
QLineEdit, QComboBox { background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 10px; padding: 9px 11px; color: #111827; selection-background-color: #2563EB; }
QLineEdit:focus, QComboBox:focus { border: 1px solid #2563EB; }
QLineEdit:disabled, QComboBox:disabled { background-color: #F3F4F6; color: #9CA3AF; border: 1px solid #E5E7EB; }
QComboBox::drop-down { border: none; width: 32px; }
QComboBox QAbstractItemView { background-color: #FFFFFF; color: #111827; border: 1px solid #CBD5E1; selection-background-color: #2563EB; outline: none; }
QCheckBox { color: #111827; spacing: 8px; }
QCheckBox::indicator { width: 18px; height: 18px; }
QPlainTextEdit#logOutput { background-color: #FFFFFF; border: 1px solid #D1D5DB; border-radius: 12px; color: #111827; font-family: "Consolas", "Cascadia Mono", "Courier New"; font-size: 12px; padding: 10px; }
QProgressBar { background-color: #E5E7EB; border: 1px solid #D1D5DB; border-radius: 10px; height: 18px; text-align: center; color: #111827; font-weight: 600; }
QProgressBar::chunk { background-color: #2563EB; border-radius: 9px; }
QScrollArea { background-color: #F4F7FB; border: none; }
QScrollBar:vertical { background-color: #F3F4F6; width: 10px; margin: 0; }
QScrollBar::handle:vertical { background-color: #CBD5E1; min-height: 24px; border-radius: 5px; }
QScrollBar::handle:vertical:hover { background-color: #94A3B8; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""

APP_QSS = DARK_QSS

STATUS_STYLES = {
    "ready": """
        QLabel#statusBadge { background-color: rgba(59, 130, 246, 0.16); color: #60A5FA; border: 1px solid rgba(59, 130, 246, 0.35); padding: 7px 12px; border-radius: 14px; font-weight: 600; }
    """,
    "running": """
        QLabel#statusBadge { background-color: rgba(245, 158, 11, 0.16); color: #D97706; border: 1px solid rgba(245, 158, 11, 0.35); padding: 7px 12px; border-radius: 14px; font-weight: 600; }
    """,
    "success": """
        QLabel#statusBadge { background-color: rgba(16, 185, 129, 0.16); color: #059669; border: 1px solid rgba(16, 185, 129, 0.35); padding: 7px 12px; border-radius: 14px; font-weight: 600; }
    """,
    "error": """
        QLabel#statusBadge { background-color: rgba(239, 68, 68, 0.16); color: #DC2626; border: 1px solid rgba(239, 68, 68, 0.35); padding: 7px 12px; border-radius: 14px; font-weight: 600; }
    """,
}


def get_app_qss(theme: str) -> str:
    return LIGHT_QSS if theme == "light" else DARK_QSS


def get_table_qss(theme: str) -> str:
    if theme == "light":
        return """
        QTableWidget { background-color: #FFFFFF; border: 1px solid #D1D5DB; border-radius: 12px; color: #111827; gridline-color: #E5E7EB; selection-background-color: rgba(37, 99, 235, 0.20); selection-color: #111827; }
        QHeaderView::section { background-color: #F3F4F6; color: #374151; border: none; border-bottom: 1px solid #D1D5DB; padding: 8px; font-weight: 700; }
        QTableCornerButton::section { background-color: #F3F4F6; border: none; }
        """
    return """
    QTableWidget { background-color: #020617; border: 1px solid #1F2937; border-radius: 12px; color: #E5E7EB; gridline-color: #1F2937; selection-background-color: rgba(37, 99, 235, 0.38); selection-color: #FFFFFF; }
    QHeaderView::section { background-color: #111827; color: #CBD5E1; border: none; border-bottom: 1px solid #1F2937; padding: 8px; font-weight: 700; }
    QTableCornerButton::section { background-color: #111827; border: none; }
    """
