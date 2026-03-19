"""
Main Window — QMainWindow with collapsible dark sidebar + stacked pages.
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QIcon

from ui.dashboard_page import DashboardPage
from ui.transactions_page import TransactionsPage
from ui.banks_page import BanksPage
from ui.beneficiaries_page import BeneficiariesPage
from ui.reports_page import ReportsPage

DARK_BG = "#0F172A"
SIDEBAR_BG = "#0D1526"
CARD_BG = "#1E293B"
ACCENT = "#2563EB"
TEXT = "#F1F5F9"
MUTED = "#64748B"
BORDER = "#1E293B"


class NavButton(QPushButton):
    def __init__(self, icon: str, label: str):
        super().__init__(f"  {icon}  {label}")
        self.setCheckable(True)
        self.setFont(QFont("Segoe UI", 11))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(46)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet(f"""
            QPushButton {{
                color: {MUTED};
                background-color: transparent;
                border: none;
                border-radius: 8px;
                padding: 6px 16px;
                text-align: left;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: #1A2845;
                color: {TEXT};
            }}
            QPushButton:checked {{
                background-color: {ACCENT};
                color: white;
                font-weight: 600;
            }}
        """)


class MainWindow(QMainWindow):
    def __init__(self, api_client):
        super().__init__()
        self.api = api_client
        self.setWindowTitle(f"🔐 TMS — {api_client.username} [{api_client.role.upper()}]")
        self.setMinimumSize(1200, 750)
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(f"QMainWindow {{ background-color: {DARK_BG}; }}")

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Sidebar ────────────────────────────────────────────────────────
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet(f"QFrame {{ background-color: {SIDEBAR_BG}; border-right: 1px solid {BORDER}; }}")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 20, 12, 16)
        sidebar_layout.setSpacing(4)

        # Logo
        logo = QLabel("🔐 TMS")
        logo.setStyleSheet(f"color: {TEXT}; font-size: 22px; font-weight: 700; padding-left: 8px;")
        logo.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        subtitle = QLabel("Transaction Manager")
        subtitle.setStyleSheet(f"color: {MUTED}; font-size: 11px; padding-left: 10px;")
        sidebar_layout.addWidget(logo)
        sidebar_layout.addWidget(subtitle)
        sidebar_layout.addSpacing(24)

        # Nav buttons
        self.nav_dashboard = NavButton("📊", "Dashboard")
        self.nav_transactions = NavButton("💳", "Transactions")
        self.nav_banks = NavButton("🏦", "Banks")
        self.nav_beneficiaries = NavButton("👤", "Beneficiaries")
        self.nav_reports = NavButton("📄", "Reports")

        self.nav_buttons = [
            self.nav_dashboard, self.nav_transactions,
            self.nav_banks, self.nav_beneficiaries, self.nav_reports,
        ]

        if self.api.is_admin():
            self.nav_admin = NavButton("⚙️", "Admin")
            self.nav_audit = NavButton("📋", "Audit Logs")
            self.nav_buttons += [self.nav_admin, self.nav_audit]

        for btn in self.nav_buttons:
            sidebar_layout.addWidget(btn)
            btn.clicked.connect(lambda checked, b=btn: self._nav_clicked(b))

        sidebar_layout.addStretch()

        # User info
        user_frame = QFrame()
        user_frame.setStyleSheet(f"QFrame {{ background-color: #162032; border-radius: 8px; border: 1px solid {BORDER}; }}")
        user_lay = QVBoxLayout(user_frame)
        user_lay.setContentsMargins(12, 10, 12, 10)
        user_lay.setSpacing(2)
        user_lay.addWidget(QLabel(f"👤 {self.api.username}", styleSheet=f"color: {TEXT}; font-size: 13px; font-weight: 600;"))
        user_lay.addWidget(QLabel(self.api.role.upper(), styleSheet=f"color: {ACCENT}; font-size: 11px; font-weight: 700;"))
        sidebar_layout.addWidget(user_frame)

        logout_btn = QPushButton("🚪  Logout")
        logout_btn.setStyleSheet(f"QPushButton {{ color: #EF4444; background: transparent; border: 1px solid #EF4444; border-radius: 6px; padding: 8px; font-size: 12px; }} QPushButton:hover {{ background: #EF44441A; }}")
        logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_btn.clicked.connect(self._logout)
        sidebar_layout.addWidget(logout_btn)

        # ── Stacked pages ─────────────────────────────────────────────────
        self.pages = QStackedWidget()
        self.page_dashboard = DashboardPage(self.api)
        self.page_transactions = TransactionsPage(self.api)
        self.page_banks = BanksPage(self.api)
        self.page_beneficiaries = BeneficiariesPage(self.api)
        self.page_reports = ReportsPage(self.api)

        self.pages.addWidget(self.page_dashboard)       # 0
        self.pages.addWidget(self.page_transactions)    # 1
        self.pages.addWidget(self.page_banks)           # 2
        self.pages.addWidget(self.page_beneficiaries)   # 3
        self.pages.addWidget(self.page_reports)         # 4

        if self.api.is_admin():
            from ui.admin_page import AdminPage
            from ui.audit_page import AuditPage
            self.page_admin = AdminPage(self.api)
            self.page_audit = AuditPage(self.api)
            self.pages.addWidget(self.page_admin)       # 5
            self.pages.addWidget(self.page_audit)       # 6

        root.addWidget(sidebar)
        root.addWidget(self.pages, 1)

        # Select dashboard by default
        self.nav_dashboard.setChecked(True)
        self.pages.setCurrentIndex(0)

    def _nav_clicked(self, clicked_btn: NavButton):
        for btn in self.nav_buttons:
            btn.setChecked(btn is clicked_btn)

        idx_map = {
            self.nav_dashboard: 0,
            self.nav_transactions: 1,
            self.nav_banks: 2,
            self.nav_beneficiaries: 3,
            self.nav_reports: 4,
        }
        if self.api.is_admin():
            idx_map[self.nav_admin] = 5
            idx_map[self.nav_audit] = 6

        self.pages.setCurrentIndex(idx_map.get(clicked_btn, 0))

    def _logout(self):
        self.api.logout()
        self.close()
