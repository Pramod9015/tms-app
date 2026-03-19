"""
Beneficiaries Page — remove Customer ID, IFSC optional, search bar.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QMessageBox, QAbstractItemView, QGridLayout
)
from PyQt6.QtCore import Qt

DARK_BG = "#0F172A";  CARD_BG = "#1E293B"; ACCENT = "#2563EB"
TEXT = "#F1F5F9"; MUTED = "#94A3B8"; BORDER = "#334155"; RED = "#EF4444"
_BTN = lambda bg, h="": f"""
    QPushButton {{background:{bg};color:white;border:none;border-radius:6px;
        padding:7px 16px;font-size:12px;font-weight:600;}}
    QPushButton:hover{{background:{h or bg};opacity:0.85;}}"""
_INPUT = f"""QLineEdit{{background:{DARK_BG};border:1.5px solid {BORDER};border-radius:6px;
    color:{TEXT};font-size:13px;padding:8px 12px;}}
    QLineEdit:focus{{border-color:{ACCENT};}}"""


class BeneficiariesPage(QWidget):
    def __init__(self, api_client):
        super().__init__()
        self.api = api_client
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        self.setStyleSheet(f"background:{DARK_BG};color:{TEXT};")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(14)

        lay.addWidget(QLabel("👤 Beneficiaries",
            styleSheet=f"color:{TEXT};font-size:22px;font-weight:700;"))

        # ── Form ──────────────────────────────────────────────────────────────
        card = QFrame()
        card.setStyleSheet(f"QFrame{{background:{CARD_BG};border-radius:10px;border:1px solid {BORDER};}}")
        grid = QGridLayout(card)
        grid.setContentsMargins(16, 14, 16, 14)
        grid.setSpacing(10)

        def lbl(t): return QLabel(t, styleSheet=f"color:{MUTED};font-size:12px;font-weight:600;border:none;")
        def inp(ph): e = QLineEdit(); e.setPlaceholderText(ph); e.setStyleSheet(_INPUT); return e

        grid.addWidget(lbl("FULL NAME *"),     0, 0)
        grid.addWidget(lbl("MOBILE NUMBER 🔒"), 0, 1)
        self.f_name   = inp("Beneficiary name"); grid.addWidget(self.f_name,   1, 0)
        self.f_mobile = inp("+91-XXXXXXXXXX");   grid.addWidget(self.f_mobile, 1, 1)

        grid.addWidget(lbl("BANK NAME"),         2, 0)
        grid.addWidget(lbl("ACCOUNT NUMBER 🔒"), 2, 1)
        self.f_bank   = inp("e.g. SBI");           grid.addWidget(self.f_bank,    3, 0)
        self.f_acc    = inp("Account (encrypted)"); grid.addWidget(self.f_acc,    3, 1)

        grid.addWidget(lbl("IFSC CODE (optional)"), 4, 0)
        self.f_ifsc = inp("SBIN0000XXX"); grid.addWidget(self.f_ifsc, 5, 0)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        add_btn = QPushButton("+ Add Beneficiary")
        add_btn.setStyleSheet(_BTN(ACCENT, "#1D4ED8"))
        add_btn.setMinimumHeight(38)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._add)
        btn_row.addWidget(add_btn)
        grid.addLayout(btn_row, 5, 1)
        lay.addWidget(card)

        # ── Search bar ────────────────────────────────────────────────────────
        search_row = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 Search by name, mobile, or bank…")
        self.search_box.setStyleSheet(_INPUT + f" QLineEdit{{max-width:400px;}}")
        self.search_box.textChanged.connect(self._filter_table)
        search_row.addWidget(self.search_box)
        self.count_lbl = QLabel("")
        self.count_lbl.setStyleSheet(f"color:{MUTED};font-size:12px;")
        search_row.addWidget(self.count_lbl)
        search_row.addStretch()
        lay.addLayout(search_row)

        # ── Table ─────────────────────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Mobile", "Bank", "Account", ""])
        hdr = self.table.horizontalHeader()
        for i, m in enumerate([QHeaderView.ResizeMode.ResizeToContents,
                                QHeaderView.ResizeMode.Stretch,
                                QHeaderView.ResizeMode.Stretch,
                                QHeaderView.ResizeMode.Stretch,
                                QHeaderView.ResizeMode.Stretch,
                                QHeaderView.ResizeMode.ResizeToContents]):
            hdr.setSectionResizeMode(i, m)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet(f"""
            QTableWidget{{background:{CARD_BG};color:{TEXT};border:1px solid {BORDER};
                border-radius:8px;gridline-color:{BORDER};font-size:13px;}}
            QHeaderView::section{{background:{DARK_BG};color:{MUTED};
                font-weight:600;font-size:11px;border:none;padding:8px;}}
            QTableWidget::item:alternate{{background:#162032;}}
            QTableWidget::item:selected{{background:{ACCENT};color:white;}}""")
        lay.addWidget(self.table)

        self._all_data = []

    # ── Data ──────────────────────────────────────────────────────────────────
    def refresh(self):
        r = self.api.list_beneficiaries()
        if r.status_code != 200: return
        self._all_data = r.json()
        self._populate(self._all_data)

    def _populate(self, data):
        self.table.setRowCount(len(data))
        for row, b in enumerate(data):
            for col, val in enumerate([
                str(b["id"]), b["name"],
                b.get("mobile_number") or "—",
                b.get("bank_name") or "—",
                b.get("account_number") or "—",
            ]):
                self.table.setItem(row, col, QTableWidgetItem(val))
            del_btn = QPushButton("🗑 Delete")
            del_btn.setStyleSheet(_BTN(RED, "#B91C1C"))
            del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            del_btn.clicked.connect(lambda _, bid=b["id"]: self._delete(bid))
            self.table.setCellWidget(row, 5, del_btn)
        self.count_lbl.setText(f"{len(data)} shown")

    def _filter_table(self, text):
        q = text.lower()
        filtered = [
            b for b in self._all_data
            if not q or
               q in b["name"].lower() or
               q in (b.get("mobile_number") or "").lower() or
               q in (b.get("bank_name") or "").lower()
        ]
        self._populate(filtered)

    # ── Actions ───────────────────────────────────────────────────────────────
    def _add(self):
        name = self.f_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation", "Name is required.")
            return
        payload = {
            "name": name,
            "mobile_number": self.f_mobile.text().strip() or None,
            "bank_name": self.f_bank.text().strip() or None,
            "account_number": self.f_acc.text().strip() or None,
            "ifsc_code": self.f_ifsc.text().strip() or None,
        }
        r = self.api.create_beneficiary(payload)
        if r.status_code == 201:
            for w in (self.f_name, self.f_mobile, self.f_bank, self.f_acc, self.f_ifsc):
                w.clear()
            self.refresh()
        else:
            QMessageBox.warning(self, "Error", r.text)

    def _delete(self, bid):
        if QMessageBox.question(self, "Confirm", "Delete this beneficiary?") == QMessageBox.StandardButton.Yes:
            self.api.delete_beneficiary(bid)
            self.refresh()
