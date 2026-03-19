"""
Reports Page — date range filter and export controls (CSV, Excel, PDF).
"""
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QFrame, QDateEdit, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QDate

DARK_BG = "#0F172A"
CARD_BG = "#1E293B"
ACCENT = "#2563EB"
TEXT = "#F1F5F9"
MUTED = "#94A3B8"
BORDER = "#334155"
SUCCESS = "#22C55E"


class ReportsPage(QWidget):
    def __init__(self, api_client):
        super().__init__()
        self.api = api_client
        self.banks = []
        self._build_ui()
        self._load_banks()

    def _build_ui(self):
        self.setStyleSheet(f"background-color: {DARK_BG}; color: {TEXT};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        title = QLabel("📄 Reports & Export")
        title.setStyleSheet(f"color: {TEXT}; font-size: 22px; font-weight: 700;")
        layout.addWidget(title)

        frame = QFrame()
        frame.setStyleSheet(f"QFrame {{ background: {CARD_BG}; border-radius: 12px; border: 1px solid {BORDER}; }}")
        frame_lay = QVBoxLayout(frame)
        frame_lay.setContentsMargins(24, 20, 24, 20)
        frame_lay.setSpacing(16)

        header = QLabel("Filter & Export Transactions")
        header.setStyleSheet(f"color: {TEXT}; font-size: 15px; font-weight: 600; border: none;")
        frame_lay.addWidget(header)

        # Date range
        date_row = QHBoxLayout()
        date_row.setSpacing(12)
        from_lbl = QLabel("From:")
        from_lbl.setStyleSheet(f"color: {MUTED}; font-size: 12px;")
        self.date_from = QDateEdit(QDate.currentDate().addMonths(-1))
        self.date_from.setCalendarPopup(True)
        self.date_from.setStyleSheet(f"QDateEdit {{ background: {DARK_BG}; border: 1.5px solid {BORDER}; border-radius: 6px; color: {TEXT}; padding: 8px; }}")
        to_lbl = QLabel("To:")
        to_lbl.setStyleSheet(f"color: {MUTED}; font-size: 12px;")
        self.date_to = QDateEdit(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        self.date_to.setStyleSheet(f"QDateEdit {{ background: {DARK_BG}; border: 1.5px solid {BORDER}; border-radius: 6px; color: {TEXT}; padding: 8px; }}")

        bank_lbl = QLabel("Bank:")
        bank_lbl.setStyleSheet(f"color: {MUTED}; font-size: 12px;")
        self.bank_combo = QComboBox()
        self.bank_combo.addItem("All Banks", None)
        self.bank_combo.setStyleSheet(f"QComboBox {{ background: {DARK_BG}; border: 1.5px solid {BORDER}; border-radius: 6px; color: {TEXT}; padding: 8px; }} QComboBox QAbstractItemView {{ background: {CARD_BG}; color: {TEXT}; selection-background-color: {ACCENT}; }}")

        app_lbl = QLabel("App:")
        app_lbl.setStyleSheet(f"color: {MUTED}; font-size: 12px;")
        self.app_combo = QComboBox()
        self.app_combo.addItem("All Apps", None)
        self.app_combo.addItems(["PhonePe", "Paytm", "PayNear", "Bank App", "ATM", "UPI", "Cash", "Other"])
        self.app_combo.setStyleSheet(self.bank_combo.styleSheet())

        date_row.addWidget(from_lbl)
        date_row.addWidget(self.date_from)
        date_row.addWidget(to_lbl)
        date_row.addWidget(self.date_to)
        date_row.addWidget(bank_lbl)
        date_row.addWidget(self.bank_combo)
        date_row.addWidget(app_lbl)
        date_row.addWidget(self.app_combo)
        date_row.addStretch()
        frame_lay.addLayout(date_row)

        # Export buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        for label, color, fn in [
            ("📊 Export CSV", "#059669", self._export_csv),
            ("📗 Export Excel", "#0891B2", self._export_excel),
            ("📕 Export PDF", "#EF4444", self._export_pdf),
        ]:
            btn = QPushButton(label)
            btn.setStyleSheet(f"QPushButton {{ background-color: {color}; color: white; border-radius: 7px; font-weight: 600; padding: 12px 24px; border: none; font-size: 14px; }} QPushButton:hover {{ opacity: 0.9; }}")
            btn.setMinimumHeight(46)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(fn)
            btn_row.addWidget(btn)
        btn_row.addStretch()
        frame_lay.addLayout(btn_row)

        layout.addWidget(frame)
        layout.addStretch()

    def _load_banks(self):
        r = self.api.list_banks()
        if r.status_code == 200:
            for b in r.json():
                self.bank_combo.addItem(b["bank_name"], b["id"])

    def _get_params(self):
        params = {
            "date_from": self.date_from.date().toString("yyyy-MM-dd"),
            "date_to": self.date_to.date().toString("yyyy-MM-dd"),
        }
        bank_id = self.bank_combo.currentData()
        app = self.app_combo.currentData()
        if bank_id: params["bank_id"] = bank_id
        if app: params["app_used"] = app
        return params

    def _save_file(self, content: bytes, default_name: str, file_filter: str):
        path, _ = QFileDialog.getSaveFileName(self, "Save File", default_name, file_filter)
        if path:
            with open(path, "wb") as f:
                f.write(content)
            QMessageBox.information(self, "Saved", f"File saved:\n{path}")

    def _export_csv(self):
        r = self.api.export_csv(**self._get_params())
        if r.status_code == 200:
            self._save_file(r.content, "transactions.csv", "CSV Files (*.csv)")
        else:
            QMessageBox.warning(self, "Error", "Export failed.")

    def _export_excel(self):
        r = self.api.export_excel(**self._get_params())
        if r.status_code == 200:
            self._save_file(r.content, "transactions.xlsx", "Excel Files (*.xlsx)")
        else:
            QMessageBox.warning(self, "Error", "Export failed.")

    def _export_pdf(self):
        r = self.api.export_pdf(**self._get_params())
        if r.status_code == 200:
            self._save_file(r.content, "transactions.pdf", "PDF Files (*.pdf)")
        else:
            QMessageBox.warning(self, "Error", "Export failed.")
