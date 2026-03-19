"""
Desktop Application Entry Point.
"""
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from api_client import api
from ui.login_window import LoginWindow
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("TMS — Secure Transaction Management")
    app.setStyle("Fusion")

    main_window_ref = [None]

    def on_login_success():
        window = MainWindow(api)
        main_window_ref[0] = window
        window.showMaximized()

    login = LoginWindow(api, on_login_success)
    if login.exec() != login.DialogCode.Accepted:
        sys.exit(0)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
