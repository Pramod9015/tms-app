"""
Banks Page — bank name registry with:
  • Add / Inline-Edit / Delete
  • Import All (137 Indian banks)
  • Import from TXT file
  • Import from Excel file
"""
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QMessageBox, QAbstractItemView, QFileDialog,
    QMenu, QDialog, QListWidget, QListWidgetItem, QDialogButtonBox,
    QCheckBox
)
from PyQt6.QtCore import Qt

DARK_BG = "#0F172A"
CARD_BG = "#1E293B"
ACCENT = "#2563EB"
TEXT = "#F1F5F9"
MUTED = "#94A3B8"
BORDER = "#334155"
DANGER_COLOR = "#EF4444"
TEAL = "#0891B2"
GREEN = "#22C55E"

_BTN = lambda bg, hover="": f"""
    QPushButton {{
        background-color: {bg}; color: white; border: none;
        border-radius: 6px; padding: 7px 16px;
        font-size: 12px; font-weight: 600;
    }}
    QPushButton:hover {{ background-color: {hover or bg}; opacity: 0.85; }}
"""


# ── Default-bank picker dialog ────────────────────────────────────────────────

class DefaultBankPickerDialog(QDialog):
    """Lets user select which default banks to import."""

    def __init__(self, parent, bank_names: list[str]):
        super().__init__(parent)
        self.setWindowTitle("Select Banks to Import")
        self.setMinimumSize(500, 540)
        self.setStyleSheet(f"background-color: {DARK_BG}; color: {TEXT};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        layout.addWidget(QLabel(
            f"<b>{len(bank_names)}</b> Indian banks available — select which to import:",
            styleSheet=f"color: {TEXT}; font-size: 13px;"
        ))

        # Select All checkbox
        self._check_all = QCheckBox("Select All")
        self._check_all.setStyleSheet(f"color: {MUTED}; font-size: 12px;")
        self._check_all.setChecked(True)
        self._check_all.toggled.connect(self._toggle_all)
        layout.addWidget(self._check_all)

        self._list = QListWidget()
        self._list.setStyleSheet(f"""
            QListWidget {{
                background: {CARD_BG}; border: 1px solid {BORDER};
                border-radius: 8px; color: {TEXT}; font-size: 13px;
            }}
            QListWidget::item:selected {{ background: {ACCENT}; }}
            QListWidget::item:hover {{ background: #162032; }}
        """)
        self._list.setAlternatingRowColors(True)
        for name in bank_names:
            item = QListWidgetItem(name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            self._list.addItem(item)
        layout.addWidget(self._list)

        # Search
        self._search = QLineEdit()
        self._search.setPlaceholderText("Filter bank names…")
        self._search.setStyleSheet(f"""
            QLineEdit {{ background: {CARD_BG}; border: 1.5px solid {BORDER};
                border-radius: 6px; color: {TEXT}; font-size: 13px; padding: 8px; }}
            QLineEdit:focus {{ border-color: {ACCENT}; }}
        """)
        self._search.textChanged.connect(self._filter)
        layout.addWidget(self._search)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.setStyleSheet(f"""
            QPushButton {{ background: {ACCENT}; color: white; border: none;
                border-radius: 6px; padding: 8px 20px; font-weight: 600; }}
            QPushButton:hover {{ background: #1D4ED8; }}
        """)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _toggle_all(self, checked: bool):
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        for i in range(self._list.count()):
            if not self._list.item(i).isHidden():
                self._list.item(i).setCheckState(state)

    def _filter(self, text: str):
        for i in range(self._list.count()):
            item = self._list.item(i)
            item.setHidden(text.lower() not in item.text().lower())

    def selected_names(self) -> list[str]:
        return [
            self._list.item(i).text()
            for i in range(self._list.count())
            if self._list.item(i).checkState() == Qt.CheckState.Checked
        ]


# ── Main Banks Page ───────────────────────────────────────────────────────────

class BanksPage(QWidget):
    """Bank name registry — add, rename, delete and bulk import."""

    def __init__(self, api_client):
        super().__init__()
        self.api = api_client
        self._editing_id: int | None = None
        self._build_ui()
        self.refresh()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.setStyleSheet(f"background-color: {DARK_BG}; color: {TEXT};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("🏦 Bank Management")
        title.setStyleSheet(f"color: {TEXT}; font-size: 22px; font-weight: 700;")
        layout.addWidget(title)

        # ── Add / Edit form ───────────────────────────────────────────────────
        form_frame = QFrame()
        form_frame.setStyleSheet(
            f"QFrame {{ background: {CARD_BG}; border-radius: 10px; border: 1px solid {BORDER}; }}"
        )
        form_lay = QHBoxLayout(form_frame)
        form_lay.setContentsMargins(16, 14, 16, 14)
        form_lay.setSpacing(12)

        form_lay.addWidget(QLabel("Bank Name:", styleSheet=f"color: {MUTED}; font-size: 13px; font-weight: 600; border: none;"))

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. SBI, HDFC, Axis …")
        self.name_input.setStyleSheet(f"""
            QLineEdit {{ background: {DARK_BG}; border: 1.5px solid {BORDER};
                border-radius: 6px; color: {TEXT}; font-size: 13px;
                padding: 8px 12px; min-width: 240px;
            }}
            QLineEdit:focus {{ border-color: {ACCENT}; }}
        """)
        self.name_input.returnPressed.connect(self._submit)
        form_lay.addWidget(self.name_input)

        self.submit_btn = QPushButton("+ Add Bank")
        self.submit_btn.setStyleSheet(_BTN(ACCENT, "#1D4ED8"))
        self.submit_btn.setMinimumHeight(38)
        self.submit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.submit_btn.clicked.connect(self._submit)
        form_lay.addWidget(self.submit_btn)

        self.cancel_btn = QPushButton("✕ Cancel")
        self.cancel_btn.setStyleSheet(_BTN("#475569", "#334155"))
        self.cancel_btn.setMinimumHeight(38)
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.clicked.connect(self._cancel_edit)
        self.cancel_btn.hide()
        form_lay.addWidget(self.cancel_btn)

        form_lay.addStretch()

        # Import dropdown button
        import_btn = QPushButton("📥 Import ▾")
        import_btn.setStyleSheet(_BTN(TEAL, "#0E7490"))
        import_btn.setMinimumHeight(38)
        import_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        import_btn.clicked.connect(self._show_import_menu)
        form_lay.addWidget(import_btn)

        layout.addWidget(form_frame)

        # ── Table ─────────────────────────────────────────────────────────────
        count_row = QHBoxLayout()
        self.count_label = QLabel("0 banks")
        self.count_label.setStyleSheet(f"color: {MUTED}; font-size: 12px;")
        count_row.addWidget(self.count_label)
        count_row.addStretch()
        layout.addLayout(count_row)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Bank Name", "Actions"])
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {CARD_BG}; color: {TEXT};
                border: 1px solid {BORDER}; border-radius: 8px;
                gridline-color: {BORDER}; font-size: 13px;
            }}
            QHeaderView::section {{
                background: {DARK_BG}; color: {MUTED};
                font-weight: 600; font-size: 12px;
                border: none; padding: 8px;
            }}
            QTableWidget::item:alternate {{ background: #162032; }}
            QTableWidget::item:selected {{ background: {ACCENT}; color: white; }}
        """)
        layout.addWidget(self.table)

    # ── Data ──────────────────────────────────────────────────────────────────

    def refresh(self):
        r = self.api.list_banks()
        if r.status_code != 200:
            return
        banks = r.json()
        self.table.setRowCount(len(banks))
        for row, b in enumerate(banks):
            self.table.setItem(row, 0, QTableWidgetItem(str(b["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(b["bank_name"]))
            self._add_action_buttons(row, b["id"], b["bank_name"])
        self.count_label.setText(f"{len(banks)} bank{'s' if len(banks) != 1 else ''}")

    def _add_action_buttons(self, row: int, bank_id: int, bank_name: str):
        cell = QWidget()
        cell.setStyleSheet("background: transparent;")
        lay = QHBoxLayout(cell)
        lay.setContentsMargins(6, 3, 6, 3)
        lay.setSpacing(8)

        edit_btn = QPushButton("✏ Edit")
        edit_btn.setStyleSheet(_BTN(TEAL, "#0E7490"))
        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_btn.clicked.connect(lambda _, bid=bank_id, bn=bank_name: self._start_edit(bid, bn))

        del_btn = QPushButton("🗑 Delete")
        del_btn.setStyleSheet(_BTN(DANGER_COLOR, "#B91C1C"))
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.clicked.connect(lambda _, bid=bank_id: self._delete(bid))

        lay.addWidget(edit_btn)
        lay.addWidget(del_btn)
        self.table.setCellWidget(row, 2, cell)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _submit(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation", "Bank name is required.")
            return
        if self._editing_id is not None:
            r = self.api.update_bank(self._editing_id, {"bank_name": name})
            if r.status_code == 200:
                self._cancel_edit(); self.refresh()
            elif r.status_code == 409:
                QMessageBox.warning(self, "Duplicate", f"'{name}' already exists.")
            else:
                QMessageBox.warning(self, "Error", r.text)
        else:
            r = self.api.create_bank({"bank_name": name})
            if r.status_code == 201:
                self.name_input.clear(); self.refresh()
            elif r.status_code == 409:
                QMessageBox.warning(self, "Duplicate", f"'{name}' already exists.")
            else:
                QMessageBox.warning(self, "Error", r.text)

    def _start_edit(self, bank_id: int, bank_name: str):
        self._editing_id = bank_id
        self.name_input.setText(bank_name)
        self.name_input.setFocus()
        self.submit_btn.setText("💾 Save")
        self.cancel_btn.show()

    def _cancel_edit(self):
        self._editing_id = None
        self.name_input.clear()
        self.submit_btn.setText("+ Add Bank")
        self.cancel_btn.hide()

    def _delete(self, bank_id: int):
        if QMessageBox.question(
            self, "Confirm Delete", "Delete this bank?\nThis will also unlink any transactions."
        ) == QMessageBox.StandardButton.Yes:
            self.api.delete_bank(bank_id)
            if self._editing_id == bank_id:
                self._cancel_edit()
            self.refresh()

    # ── Import ────────────────────────────────────────────────────────────────

    def _show_import_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{ background: {CARD_BG}; color: {TEXT}; border: 1px solid {BORDER};
                border-radius: 8px; padding: 4px; font-size: 13px; }}
            QMenu::item {{ padding: 10px 20px; border-radius: 6px; }}
            QMenu::item:selected {{ background: {ACCENT}; }}
        """)
        menu.addAction("🏦  Import Indian Banks (137)", self._import_defaults)
        menu.addSeparator()
        menu.addAction("📄  Import from TXT File", self._import_txt)
        menu.addAction("📗  Import from Excel File", self._import_excel)
        # Show below the Import button
        btn = self.sender()
        menu.exec(btn.mapToGlobal(btn.rect().bottomLeft()))

    def _import_defaults(self):
        # Fetch list from server
        r = self.api.get_default_banks()
        if r.status_code != 200:
            QMessageBox.warning(self, "Error", "Could not fetch default bank list.")
            return
        bank_names = r.json()
        dlg = DefaultBankPickerDialog(self, bank_names)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        selected = dlg.selected_names()
        if not selected:
            QMessageBox.information(self, "Nothing Selected", "No banks selected.")
            return
        r2 = self.api.import_bank_list(selected)
        if r2.status_code == 200:
            result = r2.json()
            QMessageBox.information(
                self, "Import Complete",
                f"✅ Added: {result['added']}\n"
                f"⏭ Already existed (skipped): {result['skipped']}"
            )
            self.refresh()
        else:
            QMessageBox.warning(self, "Error", r2.text)

    def _import_txt(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open TXT File", "", "Text / CSV Files (*.txt *.csv)"
        )
        if not path:
            return
        with open(path, "rb") as f:
            file_bytes = f.read()
        filename = os.path.basename(path)
        r = self.api.import_banks_txt(file_bytes, filename)
        if r.status_code == 200:
            result = r.json()
            QMessageBox.information(
                self, "Import Complete",
                f"File: {filename}\n\n"
                f"✅ Added: {result['added']}\n"
                f"⏭ Skipped (already existed): {result['skipped']}"
            )
            self.refresh()
        else:
            QMessageBox.warning(self, "Import Error", r.text)

    def _import_excel(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Excel File", "", "Excel Files (*.xlsx *.xls)"
        )
        if not path:
            return
        with open(path, "rb") as f:
            file_bytes = f.read()
        filename = os.path.basename(path)
        r = self.api.import_banks_excel(file_bytes, filename)
        if r.status_code == 200:
            result = r.json()
            QMessageBox.information(
                self, "Import Complete",
                f"File: {filename}\n\n"
                f"✅ Added: {result['added']}\n"
                f"⏭ Skipped (already existed): {result['skipped']}"
            )
            self.refresh()
        else:
            QMessageBox.warning(self, "Import Error", r.text)
