from __future__ import annotations

import os
import sys
from importlib.resources import as_file, files
from pathlib import Path

# GNOME Wayland deliberately prevents applications from choosing an absolute
# global window position. XWayland, when available, lets top-notes honor its
# defining top-right anchor while retaining normal GNOME tray integration.
# An explicit user-selected QT_QPA_PLATFORM always wins.
if (
    sys.platform.startswith("linux")
    and os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"
    and "gnome" in os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    and os.environ.get("DISPLAY")
):
    os.environ.setdefault("QT_QPA_PLATFORM", "xcb")

from PySide6.QtCore import QStandardPaths
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon

from .state import StateStore
from .ui import APP_STYLE, NotesWindow, TrayController


def state_path() -> Path:
    root = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    return Path(root) / "state.json"


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("top-notes")
    app.setApplicationDisplayName("top-notes")
    app.setOrganizationName("top-notes")
    app.setQuitOnLastWindowClosed(False)
    app.setStyle("Fusion")
    app.setStyleSheet(APP_STYLE)

    icon_resource = files("top_notes.resources").joinpath("top-notes.svg")
    with as_file(icon_resource) as icon_path:
        icon = QIcon(str(icon_path))
    app.setWindowIcon(icon)

    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(
            None,
            "System tray unavailable",
            "top-notes needs a desktop system tray. Enable a tray extension or notification area and try again.",
        )
        return 1

    store = StateStore(state_path())
    window = NotesWindow(store.load(), store, icon)
    controller = TrayController(window, icon)
    app._top_notes = (window, controller)  # Keep the tray controller alive.
    return app.exec()
