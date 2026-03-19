"""
Transactions Page — with mobile auto-fill, account number field, search bar.
"""
import re
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QMessageBox, QAbstractItemView, QComboBox,
    QDialog, QDialogButtonBox, QDateEdit, QTextEdit, QDoubleSpinBox,
    QGridLayout, QListWidget, QListWidgetItem, QScrollArea, QFileDialog
)
from PyQt6.QtCore import Qt, QTimer, QDate
from PyQt6.QtGui import QPixmap

DARK_BG = "#0F172A"; CARD_BG = "#1E293B"; ACCENT = "#2563EB"
TEXT = "#F1F5F9"; MUTED = "#94A3B8"; BORDER = "#334155"; RED = "#EF4444"; TEAL = "#0891B2"
_BTN = lambda bg, h="": f"""QPushButton{{background:{bg};color:white;border:none;border-radius:6px;
    padding:7px 14px;font-size:12px;font-weight:600;}}QPushButton:hover{{background:{h or bg};}}"""
_INPUT = f"""QLineEdit{{background:{DARK_BG};border:1.5px solid {BORDER};border-radius:6px;
    color:{TEXT};font-size:13px;padding:8px 12px;}}QLineEdit:focus{{border-color:{ACCENT};}}"""
_COMBO = f"""QComboBox{{background:{DARK_BG};border:1.5px solid {BORDER};border-radius:6px;
    color:{TEXT};font-size:13px;padding:7px 12px;}}
    QComboBox::drop-down{{border:none;}}QComboBox QAbstractItemView{{background:{CARD_BG};color:{TEXT};}}"""
TYPES    = ['withdrawal','transfer','phonepe','paytm','paynear','bank_app','atm','upi','other']
APPS     = ['phonepe','paytm','paynear','bank_app','atm','upi','other']
STATUSES = ['completed','pending','failed','reversed']


class AddTransactionDialog(QDialog):
    def __init__(self, parent, api):
        super().__init__(parent)
        self.api = api
        self.setWindowTitle("+ Add Transaction")
        self.setMinimumWidth(680)
        self.setStyleSheet(f"background:{DARK_BG};color:{TEXT};")
        self._banks = []
        self._bens  = []
        self._mobile_bens = []
        self._mobile_timer = QTimer()
        self._mobile_timer.setSingleShot(True)
        self._mobile_timer.timeout.connect(self._lookup_mobile)
        self._build_ui()
        self._load_lookups()

    # ── Build form ────────────────────────────────────────────────────────────
    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(12)

        lay.addWidget(QLabel("+ Add Transaction", styleSheet=f"color:{TEXT};font-size:18px;font-weight:700;"))

        # ── Scan Slip panel ───────────────────────────────────────────────
        slip_frame = QFrame()
        slip_frame.setStyleSheet(f"QFrame{{background:#1e3a5f22;border:1px solid #2563eb44;border-radius:8px;}}")
        slip_lay = QHBoxLayout(slip_frame)
        slip_lay.setContentsMargins(12, 10, 12, 10)
        slip_lay.setSpacing(12)
        # Image preview
        self.slip_preview = QLabel("📄")
        self.slip_preview.setFixedSize(72, 72)
        self.slip_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.slip_preview.setStyleSheet(f"font-size:28px;background:{DARK_BG};border:2px dashed {BORDER};border-radius:6px;")
        slip_lay.addWidget(self.slip_preview)
        # Info column
        info_col = QVBoxLayout()
        info_col.setSpacing(4)
        info_col.addWidget(QLabel("📷 Scan Transaction Slip", styleSheet=f"color:{TEXT};font-size:13px;font-weight:700;border:none;"))
        info_col.addWidget(QLabel("Upload a photo or scan of your slip — fields auto-filled (Hindi & English)",
            styleSheet=f"color:{MUTED};font-size:11px;border:none;"))
        self.slip_status = QLabel("")
        self.slip_status.setStyleSheet(f"color:{MUTED};font-size:11px;border:none;")
        self.slip_status.setWordWrap(True)
        info_col.addWidget(self.slip_status)
        slip_lay.addLayout(info_col, 1)
        # Scan button
        scan_btn = QPushButton("📷 Upload Slip")
        scan_btn.setStyleSheet(_BTN("#7C3AED", "#6D28D9"))
        scan_btn.setMinimumHeight(38)
        scan_btn.setMinimumWidth(120)
        scan_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        scan_btn.clicked.connect(self._scan_slip)
        slip_lay.addWidget(scan_btn)
        lay.addWidget(slip_frame)

        # ── Mobile lookup panel ───────────────────────────────────────────────
        mob_frame = QFrame()
        mob_frame.setStyleSheet(f"QFrame{{background:{CARD_BG};border:1px solid {ACCENT};border-radius:8px;}}")
        mob_lay = QVBoxLayout(mob_frame)
        mob_lay.setContentsMargins(14, 10, 14, 10)
        mob_lay.addWidget(QLabel("📱 Mobile Number (auto-fill beneficiary)", styleSheet=f"color:{MUTED};font-size:12px;font-weight:600;border:none;"))
        self.mobile_input = QLineEdit()
        self.mobile_input.setPlaceholderText("Enter 10-digit mobile…")
        self.mobile_input.setStyleSheet(_INPUT)
        self.mobile_input.textChanged.connect(self._on_mobile_change)
        mob_lay.addWidget(self.mobile_input)
        self.mobile_status = QLabel("")
        self.mobile_status.setStyleSheet(f"color:{MUTED};font-size:11px;border:none;")
        mob_lay.addWidget(self.mobile_status)
        # Multi-match picker (hidden initially)
        self.ben_picker = QListWidget()
        self.ben_picker.setStyleSheet(f"QListWidget{{background:{DARK_BG};color:{TEXT};border:1px solid {BORDER};border-radius:6px;font-size:12px;max-height:100px;}}QListWidget::item:selected{{background:{ACCENT};}}")
        self.ben_picker.itemClicked.connect(self._pick_beneficiary)
        self.ben_picker.hide()
        mob_lay.addWidget(self.ben_picker)
        lay.addWidget(mob_frame)

        # ── Grid of fields ────────────────────────────────────────────────────
        grid = QGridLayout()
        grid.setSpacing(10)

        def lbl(t): return QLabel(t, styleSheet=f"color:{MUTED};font-size:11px;font-weight:600;border:none;")
        def inp(ph): e = QLineEdit(); e.setPlaceholderText(ph); e.setStyleSheet(_INPUT); return e

        # Amount + Date
        grid.addWidget(lbl("AMOUNT (₹) *"), 0, 0)
        grid.addWidget(lbl("DATE"), 0, 1)
        self.amount_inp = QDoubleSpinBox()
        self.amount_inp.setMaximum(9_999_999)
        self.amount_inp.setDecimals(2)
        self.amount_inp.setStyleSheet(f"QDoubleSpinBox{{background:{DARK_BG};border:1.5px solid {BORDER};border-radius:6px;color:{TEXT};font-size:13px;padding:7px 12px;}}")
        grid.addWidget(self.amount_inp, 1, 0)
        self.date_inp = QDateEdit(QDate.currentDate())
        self.date_inp.setCalendarPopup(True)
        self.date_inp.setStyleSheet(f"QDateEdit{{background:{DARK_BG};border:1.5px solid {BORDER};border-radius:6px;color:{TEXT};font-size:13px;padding:7px 12px;}}")
        grid.addWidget(self.date_inp, 1, 1)

        # Type + App
        grid.addWidget(lbl("TYPE"), 2, 0)
        grid.addWidget(lbl("APP / CHANNEL"), 2, 1)
        self.type_cb = QComboBox(); self.type_cb.addItems(TYPES)
        self.type_cb.setStyleSheet(_COMBO)
        grid.addWidget(self.type_cb, 3, 0)
        self.app_cb = QComboBox(); self.app_cb.addItems(APPS)
        self.app_cb.setStyleSheet(_COMBO)
        grid.addWidget(self.app_cb, 3, 1)

        # Bank + Beneficiary
        grid.addWidget(lbl("BANK"), 4, 0)
        grid.addWidget(lbl("BENEFICIARY"), 4, 1)
        self.bank_cb = QComboBox(); self.bank_cb.addItem("— Select Bank —", None)
        self.bank_cb.setStyleSheet(_COMBO)
        grid.addWidget(self.bank_cb, 5, 0)
        self.ben_cb = QComboBox(); self.ben_cb.addItem("— Select Beneficiary —", None)
        self.ben_cb.setStyleSheet(_COMBO)
        self.ben_cb.currentIndexChanged.connect(self._on_ben_selected)
        grid.addWidget(self.ben_cb, 5, 1)

        # Account Number + Status
        grid.addWidget(lbl("ACCOUNT NUMBER"), 6, 0)
        grid.addWidget(lbl("STATUS"), 6, 1)
        self.acc_inp = inp("Auto-filled or enter manually")
        grid.addWidget(self.acc_inp, 7, 0)
        self.status_cb = QComboBox(); self.status_cb.addItems(STATUSES)
        self.status_cb.setStyleSheet(_COMBO)
        grid.addWidget(self.status_cb, 7, 1)

        # Reference (full width)
        grid.addWidget(lbl("REFERENCE / UTR"), 8, 0, 1, 2)
        self.ref_inp = inp("Reference number"); grid.addWidget(self.ref_inp, 9, 0, 1, 2)

        # Notes
        grid.addWidget(lbl("NOTES 🔒 (ENCRYPTED)"), 10, 0, 1, 2)
        self.notes_inp = QTextEdit()
        self.notes_inp.setPlaceholderText("Optional notes…")
        self.notes_inp.setMaximumHeight(80)
        self.notes_inp.setStyleSheet(f"QTextEdit{{background:{DARK_BG};border:1.5px solid {BORDER};border-radius:6px;color:{TEXT};font-size:13px;padding:8px;}}")
        grid.addWidget(self.notes_inp, 11, 0, 1, 2)

        lay.addLayout(grid)

        # Buttons
        btn_box = QDialogButtonBox()
        save_btn = QPushButton("💾 Save Transaction")
        save_btn.setStyleSheet(_BTN(ACCENT, "#1D4ED8"))
        save_btn.setMinimumHeight(40)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(_BTN("#475569", "#334155"))
        cancel_btn.setMinimumHeight(40)
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        lay.addLayout(btn_row)

    # ── Scan Slip ────────────────────────────────────────────────────────────────
    def _scan_slip(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Slip Image", "", "Images (*.jpg *.jpeg *.png *.webp *.bmp)"
        )
        if not path:
            return
        # Show preview
        pix = QPixmap(path).scaled(72, 72, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
        self.slip_preview.setPixmap(pix)
        self.slip_preview.setStyleSheet("border:2px solid #2563EB;border-radius:6px;")
        self.slip_status.setText("⏳ Scanning…")
        # Send to backend
        with open(path, "rb") as f:
            file_bytes = f.read()
        filename = os.path.basename(path)
        ext = filename.rsplit(".", 1)[-1].lower()
        mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}.get(ext, "image/jpeg")
        r = self.api.session.post(
            f"{self.api.base_url}/api/transactions/parse-slip",
            files={"file": (filename, file_bytes, mime)},
            headers={"Authorization": f"Bearer {self.api.access_token}"},
        )
        if r.status_code != 200:
            self.slip_status.setText(f"⚠️ {r.json().get('detail', 'Scan failed')}")
            return
        d = r.json()
        if d.get("error"):
            self.slip_status.setText(f"⚠️ {d['error']}")
            return
        # Auto-fill fields
        if d.get("amount"):
            try: self.amount_inp.setValue(float(d["amount"]))
            except: pass
        if d.get("date"):
            from PyQt6.QtCore import QDate
            try: self.date_inp.setDate(QDate.fromString(d["date"], "yyyy-MM-dd"))
            except: pass
        if d.get("reference_number"):
            self.ref_inp.setText(d["reference_number"])
        if d.get("account_number"):
            self.acc_inp.setText(d["account_number"])
        if d.get("bank_name"):
            for i in range(self.bank_cb.count()):
                if d["bank_name"].lower() in self.bank_cb.itemText(i).lower():
                    self.bank_cb.setCurrentIndex(i); break
        if d.get("beneficiary_name"):
            for i in range(self.ben_cb.count()):
                if d["beneficiary_name"].lower() in self.ben_cb.itemText(i).lower():
                    self.ben_cb.setCurrentIndex(i); break
        if d.get("mobile_number"):
            self.mobile_input.setText(d["mobile_number"])
            self._lookup_mobile()
        # Build status summary
        filled = [d.get(k) for k in ["amount","date","mobile_number","bank_name","account_number","beneficiary_name","reference_number"]]
        count = sum(1 for v in filled if v)
        conf = d.get("confidence", "low")
        self.slip_status.setText(f"✅ {count} fields extracted ({conf} confidence)")

    # ── Lookups ───────────────────────────────────────────────────────────────
    def _load_lookups(self):
        br = self.api.list_banks()
        if br.status_code == 200:
            self._banks = br.json()
            for b in self._banks:
                self.bank_cb.addItem(b["bank_name"], b["id"])
        wr = self.api.list_beneficiaries()
        if wr.status_code == 200:
            self._bens = wr.json()
            for b in self._bens:
                self.ben_cb.addItem(b["name"], b["id"])

    # ── Mobile lookup ─────────────────────────────────────────────────────────
    def _on_mobile_change(self, text):
        self.mobile_status.setText("")
        self.ben_picker.hide()
        # Reset auto-filled fields
        self.acc_inp.clear()
        self._mobile_timer.stop()
        digits = re.sub(r'\D', '', text)
        if len(digits) >= 10:
            self.mobile_status.setText("Looking up…")
            self._mobile_timer.start(600)

    def _lookup_mobile(self):
        mobile = self.mobile_input.text().strip()
        r = self.api.get_beneficiaries_by_mobile(mobile)
        if r.status_code != 200:
            self.mobile_status.setText("Lookup failed")
            return
        matched = r.json()
        if not matched:
            self.mobile_status.setText("No beneficiary found for this number")
        elif len(matched) == 1:
            self._apply_beneficiary(matched[0])
            self.mobile_status.setText(f"✅ Auto-filled: {matched[0]['name']}")
        else:
            self.mobile_status.setText(f"👥 {len(matched)} beneficiaries found — select one:")
            self._mobile_bens = matched
            self.ben_picker.clear()
            for b in matched:
                acc = b.get('account_number') or ''
                label = f"{b['name']}  —  {b.get('bank_name') or 'No bank'}{' | ***' + acc[-4:] if acc else ''}"
                item = QListWidgetItem(label)
                item.setData(Qt.ItemDataRole.UserRole, b)
                self.ben_picker.addItem(item)
            self.ben_picker.show()

    def _pick_beneficiary(self, item):
        b = item.data(Qt.ItemDataRole.UserRole)
        self._apply_beneficiary(b)
        self.mobile_status.setText(f"✅ Selected: {b['name']}")
        self.ben_picker.hide()

    def _apply_beneficiary(self, b):
        # Set beneficiary combobox
        for i in range(self.ben_cb.count()):
            if self.ben_cb.itemData(i) == b["id"]:
                self.ben_cb.setCurrentIndex(i)
                break
        # Auto-fill account number
        self.acc_inp.setText(b.get("account_number") or "")
        # Auto-fill bank if found
        if b.get("bank_name"):
            for i in range(self.bank_cb.count()):
                if self.bank_cb.itemText(i) == b["bank_name"]:
                    self.bank_cb.setCurrentIndex(i)
                    break

    def _on_ben_selected(self):
        idx = self.ben_cb.currentIndex()
        if idx <= 0: return
        ben_id = self.ben_cb.currentData()
        b = next((x for x in self._bens if x["id"] == ben_id), None)
        if b:
            self.acc_inp.setText(b.get("account_number") or "")

    # ── Result ────────────────────────────────────────────────────────────────
    def get_data(self):
        return {
            "amount": self.amount_inp.value(),
            "transaction_type": self.type_cb.currentText(),
            "app_used": self.app_cb.currentText(),
            "status": self.status_cb.currentText(),
            "transaction_date": self.date_inp.date().toString("yyyy-MM-dd"),
            "reference_number": self.ref_inp.text().strip() or None,
            "notes": self.notes_inp.toPlainText().strip() or None,
            "bank_id": self.bank_cb.currentData(),
            "beneficiary_id": self.ben_cb.currentData(),
        }


class TransactionsPage(QWidget):
    def __init__(self, api_client):
        super().__init__()
        self.api = api_client
        self._all_txns = []
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        self.setStyleSheet(f"background:{DARK_BG};color:{TEXT};")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(12)

        # Header row
        hdr = QHBoxLayout()
        hdr.addWidget(QLabel("💸 Transactions", styleSheet=f"color:{TEXT};font-size:22px;font-weight:700;"))
        hdr.addStretch()
        add_btn = QPushButton("+ Add Transaction")
        add_btn.setStyleSheet(_BTN(ACCENT, "#1D4ED8"))
        add_btn.setMinimumHeight(38)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._add_transaction)
        hdr.addWidget(add_btn)
        lay.addLayout(hdr)

        # ── Filter + Search bar ───────────────────────────────────────────────
        filter_row = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 Search amount, bank, beneficiary, ref…")
        self.search_box.setStyleSheet(_INPUT)
        self.search_box.textChanged.connect(self._filter_table)
        filter_row.addWidget(self.search_box, 2)

        self.type_filter = QComboBox()
        self.type_filter.addItem("All Types", "")
        for t in TYPES: self.type_filter.addItem(t, t)
        self.type_filter.setStyleSheet(_COMBO)
        self.type_filter.currentIndexChanged.connect(self._filter_table)
        filter_row.addWidget(self.type_filter, 1)

        self.count_lbl = QLabel("")
        self.count_lbl.setStyleSheet(f"color:{MUTED};font-size:12px;")
        filter_row.addWidget(self.count_lbl)
        lay.addLayout(filter_row)

        # ── Table ─────────────────────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["Date", "Amount ₹", "Type", "Channel", "Bank", "Beneficiary", "Status", ""])
        hdr_view = self.table.horizontalHeader()
        hdr_view.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr_view.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        for c in [0, 2, 3, 6]:
            hdr_view.setSectionResizeMode(c, QHeaderView.ResizeMode.ResizeToContents)
        hdr_view.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        hdr_view.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet(f"""
            QTableWidget{{background:{CARD_BG};color:{TEXT};border:1px solid {BORDER};
                border-radius:8px;gridline-color:{BORDER};font-size:13px;}}
            QHeaderView::section{{background:{DARK_BG};color:{MUTED};font-weight:600;
                font-size:11px;border:none;padding:8px;}}
            QTableWidget::item:alternate{{background:#162032;}}
            QTableWidget::item:selected{{background:{ACCENT};color:white;}}""")
        lay.addWidget(self.table)

    def refresh(self):
        r = self.api.list_transactions()
        if r.status_code != 200: return
        self._all_txns = r.json()
        self._filter_table()

    def _populate(self, data):
        self.table.setRowCount(len(data))
        for row, t in enumerate(data):
            amt = f"₹{float(t['amount']):,.2f}"
            for col, val in enumerate([
                t.get("transaction_date","")[:10],
                amt,
                t.get("transaction_type",""),
                t.get("app_used",""),
                t.get("bank_name") or "—",
                t.get("beneficiary_name") or "—",
                t.get("status",""),
            ]):
                self.table.setItem(row, col, QTableWidgetItem(val))
            del_btn = QPushButton("🗑")
            del_btn.setStyleSheet(_BTN(RED, "#B91C1C"))
            del_btn.setMaximumWidth(40)
            del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            del_btn.clicked.connect(lambda _, tid=t["id"]: self._delete(tid))
            self.table.setCellWidget(row, 7, del_btn)
        self.count_lbl.setText(f"{len(data)} transaction{'s' if len(data)!=1 else ''}")

    def _filter_table(self):
        txt = self.search_box.text().lower()
        typ = self.type_filter.currentData()
        filtered = []
        for t in self._all_txns:
            if typ and t.get("transaction_type") != typ:
                continue
            if txt:
                haystack = " ".join([
                    str(t.get("amount","")),
                    t.get("bank_name","") or "",
                    t.get("beneficiary_name","") or "",
                    t.get("transaction_type",""),
                    t.get("reference_number","") or "",
                ]).lower()
                if txt not in haystack:
                    continue
            filtered.append(t)
        self._populate(filtered)

    def _add_transaction(self):
        dlg = AddTransactionDialog(self, self.api)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            if data["amount"] <= 0:
                QMessageBox.warning(self, "Validation", "Amount must be > 0")
                return
            r = self.api.create_transaction(data)
            if r.status_code == 201:
                self.refresh()
            else:
                QMessageBox.warning(self, "Error", r.text)

    def _delete(self, tid):
        if QMessageBox.question(self, "Confirm", "Delete this transaction?") == QMessageBox.StandardButton.Yes:
            self.api.delete_transaction(tid)
            self.refresh()
