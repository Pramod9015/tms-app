"""
PyQt6 Login Window for TMS Desktop Application.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor, QPixmap

DARK_BG = "#0F172A"
CARD_BG = "#1E293B"
ACCENT = "#2563EB"
ACCENT_HOVER = "#1D4ED8"
TEXT = "#F1F5F9"
MUTED = "#94A3B8"
BORDER = "#334155"
ERROR = "#EF4444"
SUCCESS = "#22C55E"

STYLESHEET = f"""
QDialog {{
    background-color: {DARK_BG};
}}
QFrame#card {{
    background-color: {CARD_BG};
    border-radius: 16px;
    border: 1px solid {BORDER};
}}
QLabel#title {{
    color: {TEXT};
    font-size: 26px;
    font-weight: 700;
}}
QLabel#subtitle {{
    color: {MUTED};
    font-size: 13px;
}}
QLabel#field-label {{
    color: {MUTED};
    font-size: 12px;
    font-weight: 600;
}}
QLineEdit {{
    background-color: #0F172A;
    border: 1.5px solid {BORDER};
    border-radius: 8px;
    color: {TEXT};
    font-size: 14px;
    padding: 10px 14px;
}}
QLineEdit:focus {{
    border-color: {ACCENT};
}}
QPushButton#login-btn {{
    background-color: {ACCENT};
    color: white;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
    padding: 12px;
    border: none;
}}
QPushButton#login-btn:hover {{
    background-color: {ACCENT_HOVER};
}}
QLabel#error-label {{
    color: {ERROR};
    font-size: 12px;
}}
"""


class LoginWindow(QDialog):
    def __init__(self, api_client, on_success):
        super().__init__()
        self.api = api_client
        self.on_success = on_success
        self.setWindowTitle("TMS — Secure Login")
        self.setFixedSize(460, 520)
        self.setStyleSheet(STYLESHEET)
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.setContentsMargins(40, 40, 40, 40)

        card = QFrame(objectName="card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(36, 36, 36, 36)
        card_layout.setSpacing(16)

        # Logo / Title
        title_lbl = QLabel("🔐 TMS", objectName="title")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_lbl = QLabel("Secure Transaction Management", objectName="subtitle")
        subtitle_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Username
        user_label = QLabel("USERNAME", objectName="field-label")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")

        # Password
        pass_label = QLabel("PASSWORD", objectName="field-label")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        # Error label
        self.error_label = QLabel("", objectName="error-label")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setVisible(False)

        # Login button
        self.login_btn = QPushButton("Login", objectName="login-btn")
        self.login_btn.setMinimumHeight(46)
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.clicked.connect(self._do_login)
        self.password_input.returnPressed.connect(self._do_login)

        card_layout.addWidget(title_lbl)
        card_layout.addWidget(subtitle_lbl)
        card_layout.addSpacing(8)
        card_layout.addWidget(user_label)
        card_layout.addWidget(self.username_input)
        card_layout.addWidget(pass_label)
        card_layout.addWidget(self.password_input)
        card_layout.addWidget(self.error_label)
        card_layout.addSpacing(8)
        card_layout.addWidget(self.login_btn)

        outer.addWidget(card)

    def _do_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            self._show_error("Please enter username and password.")
            return

        self.login_btn.setText("Authenticating...")
        self.login_btn.setEnabled(False)

        try:
            response = self.api.login(username, password)
            if response.status_code == 200:
                self.accept()
                self.on_success()
            else:
                data = response.json()
                self._show_error(data.get("detail", "Login failed."))
        except Exception as e:
            self._show_error(f"Connection error: {str(e)}")
        finally:
            self.login_btn.setText("Login")
            self.login_btn.setEnabled(True)

    def _show_error(self, msg: str):
        self.error_label.setText(msg)
        self.error_label.setVisible(True)
