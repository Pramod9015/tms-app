"""
Admin Page — user management for admin users.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QComboBox, QMessageBox
)
from PyQt6.QtCore import Qt

DARK_BG = "#0F172A"
CARD_BG = "#1E293B"
ACCENT = "#2563EB"
TEXT = "#F1F5F9"
MUTED = "#94A3B8"
BORDER = "#334155"


class AdminPage(QWidget):
    def __init__(self, api_client):
        super().__init__()
        self.api = api_client
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        self.setStyleSheet(f"background-color: {DARK_BG}; color: {TEXT};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("⚙️ User Management")
        title.setStyleSheet(f"color: {TEXT}; font-size: 22px; font-weight: 700;")
        layout.addWidget(title)

        # Add user form
        form = QFrame()
        form.setStyleSheet(f"QFrame {{ background: {CARD_BG}; border-radius: 12px; border: 1px solid {BORDER}; }}")
        form_lay = QHBoxLayout(form)
        form_lay.setContentsMargins(20, 16, 20, 16)
        form_lay.setSpacing(12)

        style = f"QLineEdit, QComboBox {{ background: {DARK_BG}; border: 1.5px solid {BORDER}; border-radius: 6px; color: {TEXT}; padding: 8px; font-size: 13px; }} QLineEdit:focus, QComboBox:focus {{ border-color: {ACCENT}; }} QComboBox QAbstractItemView {{ background: {CARD_BG}; color: {TEXT}; }}"
        self.setStyleSheet(self.styleSheet() + style)

        self.new_username = QLineEdit(); self.new_username.setPlaceholderText("Username")
        self.new_email = QLineEdit(); self.new_email.setPlaceholderText("Email")
        self.new_password = QLineEdit(); self.new_password.setPlaceholderText("Password"); self.new_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_role = QComboBox(); self.new_role.addItems(["user", "admin"])

        add_btn = QPushButton("+ Add User")
        add_btn.setStyleSheet(f"QPushButton {{ background-color: {ACCENT}; color: white; border-radius: 7px; font-weight: 600; padding: 10px 20px; border: none; }} QPushButton:hover {{ background-color: #1D4ED8; }}")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._add_user)

        for w in [self.new_username, self.new_email, self.new_password]:
            form_lay.addWidget(w, 1)
        form_lay.addWidget(self.new_role)
        form_lay.addWidget(add_btn)
        layout.addWidget(form)

        # Users table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Username", "Email", "Role", "Active"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(f"""
            QTableWidget {{ background-color: {CARD_BG}; color: {TEXT}; border: 1px solid {BORDER}; border-radius: 8px; gridline-color: {BORDER}; font-size: 13px; }}
            QHeaderView::section {{ background-color: #0F172A; color: {MUTED}; font-weight: 600; font-size: 12px; border: none; padding: 8px; }}
            QTableWidget::item:alternate {{ background-color: #162032; }}
        """)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._context_menu)
        layout.addWidget(self.table)

    def refresh(self):
        r = self.api.list_users()
        if r.status_code == 200:
            data = r.json()
            self.table.setRowCount(len(data))
            for row, u in enumerate(data):
                self.table.setItem(row, 0, QTableWidgetItem(str(u["id"])))
                self.table.setItem(row, 1, QTableWidgetItem(u["username"]))
                self.table.setItem(row, 2, QTableWidgetItem(u["email"]))
                self.table.setItem(row, 3, QTableWidgetItem(u["role"]))
                self.table.setItem(row, 4, QTableWidgetItem("✓ Active" if u["is_active"] else "✗ Inactive"))

    def _add_user(self):
        data = {
            "username": self.new_username.text().strip(),
            "email": self.new_email.text().strip(),
            "password": self.new_password.text(),
            "role": self.new_role.currentText(),
        }
        if not all([data["username"], data["email"], data["password"]]):
            QMessageBox.warning(self, "Validation", "All fields are required.")
            return
        r = self.api.create_user(data)
        if r.status_code == 201:
            QMessageBox.information(self, "Success", "User created.")
            self.new_username.clear(); self.new_email.clear(); self.new_password.clear()
            self.refresh()
        else:
            QMessageBox.warning(self, "Error", r.text)

    def _context_menu(self, pos):
        from PyQt6.QtWidgets import QMenu
        row = self.table.rowAt(pos.y())
        if row < 0: return
        user_id = int(self.table.item(row, 0).text())
        menu = QMenu(self)
        menu.setStyleSheet(f"QMenu {{ background: {CARD_BG}; color: {TEXT}; border: 1px solid {BORDER}; }} QMenu::item:selected {{ background: {ACCENT}; }}")
        del_action = menu.addAction("🗑 Delete User")
        if menu.exec(self.table.viewport().mapToGlobal(pos)) == del_action:
            if QMessageBox.question(self, "Confirm", f"Delete user #{user_id}?") == QMessageBox.StandardButton.Yes:
                self.api.delete_user(user_id)
                self.refresh()
