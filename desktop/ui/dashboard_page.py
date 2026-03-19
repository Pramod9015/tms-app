"""
Dashboard Page — shows summary cards and 4 Matplotlib charts.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor
import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

DARK_BG = "#0F172A"
CARD_BG = "#1E293B"
ACCENT = "#2563EB"
TEXT = "#F1F5F9"
MUTED = "#94A3B8"
BORDER = "#334155"
CHART_COLORS = ["#2563EB", "#7C3AED", "#059669", "#D97706", "#EF4444", "#0891B2", "#DB2777"]


class SummaryCard(QFrame):
    def __init__(self, title: str, value: str, color: str = ACCENT):
        super().__init__()
        self.setObjectName("summary-card")
        self.setStyleSheet(f"""
            QFrame#summary-card {{
                background-color: {CARD_BG};
                border-radius: 12px;
                border: 1px solid {BORDER};
                min-width: 160px;
                padding: 8px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(6)

        self.value_lbl = QLabel(value)
        self.value_lbl.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: 700;")
        self.value_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet(f"color: {MUTED}; font-size: 12px;")
        self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)

        layout.addWidget(self.value_lbl)
        layout.addWidget(self.title_lbl)

    def update_value(self, value: str):
        self.value_lbl.setText(value)


class ChartWidget(FigureCanvas):
    def __init__(self, width=5, height=3.5):
        self.fig = Figure(figsize=(width, height), facecolor=CARD_BG, tight_layout=True)
        super().__init__(self.fig)
        self.ax = self.fig.add_subplot(111)
        self._style_ax()

    def _style_ax(self):
        self.ax.set_facecolor(CARD_BG)
        self.ax.tick_params(colors=MUTED, labelsize=8)
        for spine in self.ax.spines.values():
            spine.set_edgecolor(BORDER)
        self.ax.title.set_color(TEXT)
        self.fig.patch.set_alpha(0)

    def clear(self):
        self.ax.clear()
        self._style_ax()


class DashboardPage(QWidget):
    def __init__(self, api_client):
        super().__init__()
        self.api = api_client
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(f"QScrollArea {{ background: {DARK_BG}; border: none; }}")

        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)

        # Page title
        title = QLabel("📊 Dashboard")
        title.setStyleSheet(f"color: {TEXT}; font-size: 22px; font-weight: 700;")
        main_layout.addWidget(title)

        # Summary Cards Row
        cards_row = QHBoxLayout()
        cards_row.setSpacing(16)
        self.card_total = SummaryCard("Total Transactions", "—", ACCENT)
        self.card_withdraw = SummaryCard("Withdrawals", "—", "#7C3AED")
        self.card_transfer = SummaryCard("Transfers", "—", "#059669")
        self.card_today = SummaryCard("Today's Amount", "—₹", "#D97706")
        self.card_month = SummaryCard("This Month", "—₹", "#0891B2")
        for c in [self.card_total, self.card_withdraw, self.card_transfer, self.card_today, self.card_month]:
            cards_row.addWidget(c)
        main_layout.addLayout(cards_row)

        # Charts Row 1
        charts_row1 = QHBoxLayout()
        charts_row1.setSpacing(16)

        self.daily_chart = ChartWidget(5, 3)
        self.app_chart = ChartWidget(3.5, 3)
        for ch, label in [(self.daily_chart, "Daily Transactions (Last 30 Days)"),
                          (self.app_chart, "App Usage")]:
            frame = self._wrap_chart(ch, label)
            charts_row1.addWidget(frame, 1)

        main_layout.addLayout(charts_row1)

        # Charts Row 2
        charts_row2 = QHBoxLayout()
        charts_row2.setSpacing(16)

        self.bank_chart = ChartWidget(5, 3)
        self.monthly_chart = ChartWidget(5, 3)
        for ch, label in [(self.bank_chart, "Bank-wise Transactions"),
                          (self.monthly_chart, "Monthly Trend")]:
            frame = self._wrap_chart(ch, label)
            charts_row2.addWidget(frame, 1)

        main_layout.addLayout(charts_row2)

        # Recent Transactions Table
        recent_lbl = QLabel("Recent Transactions")
        recent_lbl.setStyleSheet(f"color: {TEXT}; font-size: 16px; font-weight: 600;")
        main_layout.addWidget(recent_lbl)

        self.recent_table = QTableWidget()
        self.recent_table.setColumnCount(7)
        self.recent_table.setHorizontalHeaderLabels(
            ["Date", "Type", "App", "Amount (₹)", "Bank", "Status", "Reference"]
        )
        self.recent_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.recent_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.recent_table.setAlternatingRowColors(True)
        self.recent_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {CARD_BG};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 8px;
                gridline-color: {BORDER};
                font-size: 13px;
            }}
            QHeaderView::section {{
                background-color: #0F172A;
                color: {MUTED};
                font-weight: 600;
                font-size: 12px;
                border: none;
                padding: 8px;
            }}
            QTableWidget::item:alternate {{
                background-color: #162032;
            }}
        """)
        self.recent_table.setMaximumHeight(300)
        main_layout.addWidget(self.recent_table)

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _wrap_chart(self, chart: ChartWidget, label: str) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {CARD_BG};
                border-radius: 12px;
                border: 1px solid {BORDER};
            }}
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {TEXT}; font-size: 13px; font-weight: 600; border: none;")
        layout.addWidget(lbl)
        layout.addWidget(chart)
        return frame

    def refresh(self):
        try:
            self._load_summary()
            self._load_daily_chart()
            self._load_app_usage()
            self._load_bank_wise()
            self._load_monthly_trend()
            self._load_recent()
        except Exception as e:
            print(f"Dashboard error: {e}")

    def _load_summary(self):
        r = self.api.get_summary()
        if r.status_code == 200:
            d = r.json()
            self.card_total.update_value(str(d.get("total_transactions", 0)))
            self.card_withdraw.update_value(str(d.get("total_withdrawals", 0)))
            self.card_transfer.update_value(str(d.get("total_transfers", 0)))
            self.card_today.update_value(f"₹{d.get('today_amount', 0):,.2f}")
            self.card_month.update_value(f"₹{d.get('month_amount', 0):,.2f}")

    def _load_daily_chart(self):
        r = self.api.get_daily_chart(30)
        if r.status_code == 200:
            data = r.json()
            dates = [d["date"][-5:] for d in data]  # MM-DD
            amounts = [d["amount"] for d in data]
            self.daily_chart.clear()
            self.daily_chart.ax.plot(dates, amounts, color=ACCENT, linewidth=2, marker="o", markersize=3)
            self.daily_chart.ax.fill_between(range(len(dates)), amounts, alpha=0.15, color=ACCENT)
            self.daily_chart.ax.set_xticks(range(0, len(dates), 5))
            self.daily_chart.ax.set_xticklabels([dates[i] for i in range(0, len(dates), 5)], rotation=30)
            self.daily_chart.draw()

    def _load_app_usage(self):
        r = self.api.get_app_usage()
        if r.status_code == 200:
            data = r.json()
            if data:
                labels = [d["app"] for d in data]
                counts = [d["count"] for d in data]
                self.app_chart.clear()
                self.app_chart.ax.pie(
                    counts, labels=labels, colors=CHART_COLORS[:len(labels)],
                    autopct="%1.1f%%", startangle=90,
                    textprops={"color": TEXT, "fontsize": 8},
                )
                self.app_chart.draw()

    def _load_bank_wise(self):
        r = self.api.get_bank_wise()
        if r.status_code == 200:
            data = r.json()
            if data:
                banks = [d["bank"] for d in data]
                amounts = [d["amount"] for d in data]
                self.bank_chart.clear()
                bars = self.bank_chart.ax.bar(banks, amounts, color=CHART_COLORS[:len(banks)])
                self.bank_chart.ax.set_xticklabels(banks, rotation=15, ha="right")
                self.bank_chart.draw()

    def _load_monthly_trend(self):
        r = self.api.get_monthly_trend()
        if r.status_code == 200:
            data = r.json()
            if data:
                months = [d["month"] for d in data]
                amounts = [d["amount"] for d in data]
                self.monthly_chart.clear()
                self.monthly_chart.ax.plot(months, amounts, color="#7C3AED", linewidth=2, marker="s", markersize=4)
                self.monthly_chart.ax.fill_between(range(len(months)), amounts, alpha=0.15, color="#7C3AED")
                self.monthly_chart.ax.set_xticks(range(len(months)))
                self.monthly_chart.ax.set_xticklabels(months, rotation=30, ha="right")
                self.monthly_chart.draw()

    def _load_recent(self):
        r = self.api.get_recent_transactions(10)
        if r.status_code == 200:
            data = r.json()
            self.recent_table.setRowCount(len(data))
            for row, t in enumerate(data):
                self.recent_table.setItem(row, 0, QTableWidgetItem(t["date"][:16]))
                self.recent_table.setItem(row, 1, QTableWidgetItem(t["transaction_type"].capitalize()))
                self.recent_table.setItem(row, 2, QTableWidgetItem(t["app_used"]))
                amount_item = QTableWidgetItem(f"₹{t['amount']:,.2f}")
                amount_item.setForeground(QColor("#22C55E"))
                self.recent_table.setItem(row, 3, amount_item)
                self.recent_table.setItem(row, 4, QTableWidgetItem(t.get("bank_name") or "—"))
                status = t.get("status", "")
                s_item = QTableWidgetItem(status.capitalize())
                s_item.setForeground(QColor("#22C55E" if status == "completed" else "#EF4444"))
                self.recent_table.setItem(row, 5, s_item)
                self.recent_table.setItem(row, 6, QTableWidgetItem(t.get("reference_number") or "—"))
