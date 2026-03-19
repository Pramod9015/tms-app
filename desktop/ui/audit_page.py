"""
Audit Log Page — admin view of system activity.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView
)

DARK_BG = "#0F172A"
CARD_BG = "#1E293B"
TEXT = "#F1F5F9"
MUTED = "#94A3B8"
BORDER = "#334155"


class AuditPage(QWidget):
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
        title = QLabel("📋 Audit Logs")
        title.setStyleSheet(f"color: {TEXT}; font-size: 22px; font-weight: 700;")
        layout.addWidget(title)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Timestamp", "User", "Action", "Resource", "IP"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(f"""
            QTableWidget {{ background-color: {CARD_BG}; color: {TEXT}; border: 1px solid {BORDER}; border-radius: 8px; gridline-color: {BORDER}; font-size: 13px; }}
            QHeaderView::section {{ background-color: #0F172A; color: {MUTED}; font-weight: 600; border: none; padding: 8px; }}
            QTableWidget::item:alternate {{ background-color: #162032; }}
        """)
        layout.addWidget(self.table)

    def refresh(self):
        r = self.api.list_audit_logs()
        if r.status_code == 200:
            data = r.json()
            self.table.setRowCount(len(data))
            for row, log in enumerate(data):
                self.table.setItem(row, 0, QTableWidgetItem(str(log["id"])))
                self.table.setItem(row, 1, QTableWidgetItem(log["timestamp"][:19]))
                self.table.setItem(row, 2, QTableWidgetItem(str(log.get("user_id", "—"))))
                self.table.setItem(row, 3, QTableWidgetItem(log["action"]))
                self.table.setItem(row, 4, QTableWidgetItem(log["resource"]))
                self.table.setItem(row, 5, QTableWidgetItem(log.get("ip_address") or "—"))
