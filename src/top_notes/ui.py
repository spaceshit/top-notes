from __future__ import annotations

from PySide6.QtCore import QPoint, QSize, Qt, QTimer, Signal
from PySide6.QtGui import (
    QActionGroup,
    QColor,
    QFont,
    QIcon,
    QPainter,
    QPen,
    QPixmap,
    QResizeEvent,
    QTextCharFormat,
    QTextCursor,
)
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QColorDialog,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QSizeGrip,
    QSpinBox,
    QStyle,
    QStyleOptionTab,
    QSystemTrayIcon,
    QTabBar,
    QTabWidget,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from . import __version__
from .state import BACKGROUNDS, BACKGROUND_NAMES, FONT_FAMILIES, TAB_COLORS, AppState, Group, Note, StateStore


APP_STYLE = """
QMainWindow { background: #f3c9aa; }
QDialog { background: #e8edf3; }
QLabel#settingsTitle { font-size: 16px; font-weight: 700; padding: 2px 0 7px 0; }
QWidget { color: #172033; font-size: 13px; }
QToolButton, QPushButton, QComboBox, QSpinBox {
  background: #ffffff; border: 1px solid #cbd5e1; border-radius: 7px; padding: 5px 9px;
}
QToolButton:hover, QPushButton:hover, QComboBox:hover { border-color: #14b8a6; background: #f0fdfa; }
QToolButton:checked, QPushButton:checked { color: white; background: #0f766e; border-color: #0f766e; }
QToolButton#formatButton {
  min-width: 0; padding: 0; border-radius: 5px;
}
QToolButton#newNoteButton {
  color: #713a20; background: #dfa77f; border: 0; border-radius: 12px;
  padding: 0; font-size: 17px; font-weight: 600;
}
QToolButton#newNoteButton:hover { background: #d89b70; }
QToolButton#newNoteButton:pressed { background: #cf8d60; }
QToolButton#tabCloseButton {
  min-width: 0; color: #334155; background: transparent; border: 0;
  border-radius: 7px; padding: 0; font-size: 14px; font-weight: 700;
}
QToolButton#tabCloseButton:hover { color: #991b1b; background: rgba(255, 255, 255, 145); }
QWidget#formattingBar {
  background: #dfa77f; border: 0; border-radius: 9px;
}
QLabel#saveStatusLabel {
  color: #713a20; font-size: 11px; font-weight: 600; padding: 0 3px;
}
QTabWidget::pane { border: 0; background: transparent; top: 6px; }
QTabBar { qproperty-drawBase: 0; }
QTabBar::tab {
  background: transparent; border: 0; margin-right: 0;
  padding: 5px 3px 5px 8px; min-width: 0;
}
QTextEdit {
  border: 1px solid #ead8cc; border-radius: 10px; padding: 12px;
  selection-background-color: #99f6e4;
}
QTextEdit QScrollBar:vertical {
  background: transparent; width: 8px; margin: 4px 1px 4px 1px;
}
QTextEdit QScrollBar::handle:vertical {
  background: #cbd5e1; border: 0; border-radius: 3px; min-height: 28px;
}
QTextEdit QScrollBar::handle:vertical:hover { background: #d58b5e; }
QTextEdit QScrollBar::add-line:vertical, QTextEdit QScrollBar::sub-line:vertical { height: 0; }
QTextEdit QScrollBar::add-page:vertical, QTextEdit QScrollBar::sub-page:vertical { background: transparent; }
QTextEdit QScrollBar:horizontal {
  background: transparent; height: 8px; margin: 1px 4px 1px 4px;
}
QTextEdit QScrollBar::handle:horizontal {
  background: #cbd5e1; border: 0; border-radius: 3px; min-width: 28px;
}
QTextEdit QScrollBar::handle:horizontal:hover { background: #d58b5e; }
QTextEdit QScrollBar::add-line:horizontal, QTextEdit QScrollBar::sub-line:horizontal { width: 0; }
QTextEdit QScrollBar::add-page:horizontal, QTextEdit QScrollBar::sub-page:horizontal { background: transparent; }
QMenu { background: white; border: 1px solid #cbd5e1; padding: 5px; }
QMenu::item { padding: 7px 28px 7px 10px; border-radius: 5px; }
QMenu::item:selected { background: #ccfbf1; color: #134e4a; }
"""


def color_swatch_icon(color: str) -> QIcon:
    pixmap = QPixmap(24, 16)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QPen(QColor("#94a3b8"), 1))
    painter.setBrush(QColor(color))
    painter.drawRoundedRect(1, 1, 22, 14, 4, 4)
    painter.end()
    return QIcon(pixmap)


class ColorTabBar(QTabBar):
    context_requested = Signal(int, QPoint)
    close_requested = Signal(int)

    def tabSizeHint(self, index: int) -> QSize:
        text_width = self.fontMetrics().horizontalAdvance(self.tabText(index))
        return QSize(text_width + 53, 28)

    def minimumTabSizeHint(self, index: int) -> QSize:
        return self.tabSizeHint(index)

    def add_close_button(self, index: int) -> None:
        button = QToolButton(self)
        button.setObjectName("tabCloseButton")
        button.setText("×")
        button.setToolTip("Close note")
        button.setFixedSize(16, 16)
        button.clicked.connect(lambda: self.request_close(button))
        self.setTabButton(index, QTabBar.ButtonPosition.RightSide, button)

    def request_close(self, button: QToolButton) -> None:
        for index in range(self.count()):
            if self.tabButton(index, QTabBar.ButtonPosition.RightSide) is button:
                self.close_requested.emit(index)
                return

    def mousePressEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        if event.button() == Qt.MouseButton.RightButton:
            index = self.tabAt(event.position().toPoint())
            if index >= 0:
                self.context_requested.emit(index, event.globalPosition().toPoint())
                return
        super().mousePressEvent(event)

    def paintEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        for index in range(self.count()):
            option = QStyleOptionTab()
            self.initStyleOption(option, index)
            color_name = self.tabData(index) or "white"
            color = QColor(TAB_COLORS.get(str(color_name), TAB_COLORS["white"]))
            if option.state & QStyle.StateFlag.State_MouseOver:
                color = color.lighter(106)

            # Adjacent tab rects touch; a 5px right inset plus the next tab's
            # 1px left inset creates the same 6px gap used above the editor.
            pill = option.rect.adjusted(1, 1, -5, -1)
            selected = bool(option.state & QStyle.StateFlag.State_Selected)
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(pill, 10, 10)

            close_button = self.tabButton(index, QTabBar.ButtonPosition.RightSide)
            if close_button:
                close_x = pill.right() - 9 - close_button.width() + 1
                close_y = pill.top() + (pill.height() - close_button.height()) // 2
                close_button.move(close_x, close_y)
            close_inset = 9 + close_button.width() + 5 if close_button else 9
            text_rect = pill.adjusted(9, 0, -close_inset, 0)
            font = painter.font()
            font.setBold(selected)
            painter.setFont(font)
            painter.setPen(QColor("#172033"))
            text = painter.fontMetrics().elidedText(option.text, Qt.TextElideMode.ElideRight, text_rect.width())
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, text)


class CornerSizeGrip(QSizeGrip):
    """Small functional bottom-left grip drawn as a bold angle."""

    def paintEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor("#8f5637"), 3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.drawLine(3, 3, 3, self.height() - 3)
        painter.drawLine(3, self.height() - 3, self.width() - 3, self.height() - 3)
        painter.end()
        event.accept()


class NoteEditor(QWidget):
    changed = Signal()

    def __init__(self, note: Note, state: AppState):
        super().__init__()
        self.note = note
        self.state = state

        self.editor = QTextEdit()
        self.editor.setAcceptRichText(True)
        self.editor.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.editor.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.editor.setPlaceholderText("Write something worth remembering…")
        if note.content:
            self.editor.setHtml(note.content)

        self.bold_button = self.format_button("B", "Bold", self.set_bold)
        bold_font = self.bold_button.font()
        bold_font.setBold(True)
        self.bold_button.setFont(bold_font)

        self.italic_button = self.format_button("I", "Italic", self.set_italic)
        italic_font = self.italic_button.font()
        italic_font.setItalic(True)
        self.italic_button.setFont(italic_font)

        self.underline_button = self.format_button("U", "Underline", self.set_underline)
        underline_font = self.underline_button.font()
        underline_font.setUnderline(True)
        self.underline_button.setFont(underline_font)

        self.strike_button = self.format_button("S", "Strikethrough", self.set_strikethrough)
        strike_font = self.strike_button.font()
        strike_font.setStrikeOut(True)
        self.strike_button.setFont(strike_font)

        color_button = QToolButton()
        color_button.setObjectName("formatButton")
        color_button.setIcon(self.color_picker_icon())
        color_button.setIconSize(QSize(17, 17))
        color_button.setFixedSize(24, 24)
        color_button.setToolTip("Color selected text or future typing")
        color_button.clicked.connect(self.choose_text_color)

        clear_button = QToolButton()
        clear_button.setObjectName("formatButton")
        clear_button.setIcon(self.eraser_icon())
        clear_button.setIconSize(QSize(17, 17))
        clear_button.setFixedSize(24, 24)
        clear_button.setToolTip("Remove formatting from selected text")
        clear_button.clicked.connect(self.clear_formatting)

        self.formatting_bar = QWidget()
        self.formatting_bar.setObjectName("formattingBar")
        toolbar = QHBoxLayout(self.formatting_bar)
        toolbar.setContentsMargins(7, 4, 7, 4)
        toolbar.setSpacing(5)
        toolbar.addWidget(self.bold_button)
        toolbar.addWidget(self.italic_button)
        toolbar.addWidget(self.underline_button)
        toolbar.addWidget(self.strike_button)
        toolbar.addWidget(color_button)
        toolbar.addWidget(clear_button)
        toolbar.addStretch()
        self.save_status_label = QLabel("saved.")
        self.save_status_label.setObjectName("saveStatusLabel")
        self.save_status_label.setMinimumWidth(54)
        self.save_status_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        toolbar.addWidget(self.save_status_label)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.editor)
        layout.addWidget(self.formatting_bar)

        self.editor.textChanged.connect(self.content_changed)
        self.editor.currentCharFormatChanged.connect(self.sync_format_buttons)
        self.apply_preferences()

    def set_save_status(self, status: str) -> None:
        self.save_status_label.setText(status)

    @staticmethod
    def format_button(text: str, tooltip: str, callback) -> QToolButton:  # type: ignore[no-untyped-def]
        button = QToolButton()
        button.setObjectName("formatButton")
        button.setText(text)
        button.setToolTip(tooltip)
        button.setCheckable(True)
        button.setFixedSize(24, 24)
        button.clicked.connect(callback)
        return button

    @staticmethod
    def color_picker_icon() -> QIcon:
        pixmap = QPixmap(20, 20)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor("#475569"), 1.2))
        painter.setBrush(QColor("#ffffff"))
        painter.drawEllipse(1, 1, 18, 18)
        for x, y, color in (
            (5, 4, "#ef4444"),
            (11, 4, "#3b82f6"),
            (5, 10, "#f59e0b"),
            (11, 10, "#22c55e"),
        ):
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(color))
            painter.drawEllipse(x, y, 5, 5)
        painter.end()
        return QIcon(pixmap)

    @staticmethod
    def eraser_icon() -> QIcon:
        pixmap = QPixmap(20, 20)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor("#475569"), 1.2))
        painter.setBrush(QColor("#fb7185"))
        painter.drawPolygon([QPoint(4, 13), QPoint(11, 4), QPoint(17, 10), QPoint(9, 17)])
        painter.setBrush(QColor("#f8fafc"))
        painter.drawPolygon([QPoint(4, 13), QPoint(7, 9), QPoint(12, 14), QPoint(9, 17)])
        painter.drawLine(QPoint(7, 9), QPoint(12, 14))
        painter.end()
        return QIcon(pixmap)

    def apply_preferences(self) -> None:
        prefs = self.state.preferences
        font = QFont(prefs.font_family, prefs.font_size)
        foreground = "#e5e7eb" if prefs.background == "#111827" else "#172033"
        self.editor.document().setDefaultFont(font)
        self.editor.setFont(font)
        self.editor.setStyleSheet(f"background-color: {prefs.background}; color: {foreground};")

        # QTextEdit.setFont() only affects future input when loaded HTML has
        # explicit font attributes. Merge only the global family and size into
        # existing text, leaving emphasis and user-selected colors untouched.
        cursor = QTextCursor(self.editor.document())
        cursor.select(QTextCursor.SelectionType.Document)
        if cursor.hasSelection():
            char_format = QTextCharFormat()
            char_format.setFontFamilies([prefs.font_family])
            char_format.setFontPointSize(prefs.font_size)
            cursor.mergeCharFormat(char_format)

    def content_changed(self) -> None:
        self.note.content = self.editor.toHtml()
        self.changed.emit()

    def set_bold(self, enabled: bool) -> None:
        self.editor.setFontWeight(QFont.Weight.Bold if enabled else QFont.Weight.Normal)
        self.editor.setFocus()

    def set_italic(self, enabled: bool) -> None:
        self.editor.setFontItalic(enabled)
        self.editor.setFocus()

    def set_underline(self, enabled: bool) -> None:
        self.editor.setFontUnderline(enabled)
        self.editor.setFocus()

    def set_strikethrough(self, enabled: bool) -> None:
        char_format = QTextCharFormat()
        char_format.setFontStrikeOut(enabled)
        self.editor.mergeCurrentCharFormat(char_format)
        self.editor.setFocus()

    def sync_format_buttons(self, char_format: QTextCharFormat) -> None:
        states = (
            (self.bold_button, char_format.font().bold()),
            (self.italic_button, char_format.fontItalic()),
            (self.underline_button, char_format.fontUnderline()),
            (self.strike_button, char_format.fontStrikeOut()),
        )
        for button, enabled in states:
            button.blockSignals(True)
            button.setChecked(enabled)
            button.blockSignals(False)

    def clear_formatting(self) -> None:
        cursor = self.editor.textCursor()
        clean = QTextCharFormat()
        if cursor.hasSelection():
            cursor.setCharFormat(clean)
        self.editor.setCurrentCharFormat(clean)
        self.editor.setFocus()

    def choose_text_color(self) -> None:
        color = QColorDialog.getColor(self.editor.textColor(), self, "Choose text color")
        if color.isValid():
            self.editor.setTextColor(color)
            self.editor.setFocus()


class SettingsDialog(QDialog):
    def __init__(self, state: AppState, parent: QWidget | None = None):
        super().__init__(parent)
        self.state = state
        self.setWindowTitle("top-notes settings")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setObjectName("settingsDialog")
        self.setMinimumWidth(360)

        self.font_size = QSpinBox()
        self.font_size.setRange(9, 32)
        self.font_size.setValue(state.preferences.font_size)
        self.font_family = QComboBox()
        for family in FONT_FAMILIES:
            self.font_family.addItem(family)
            self.font_family.setItemData(
                self.font_family.count() - 1,
                QFont(family, 13),
                Qt.ItemDataRole.FontRole,
            )
        self.font_family.setCurrentText(state.preferences.font_family)
        self.background = QComboBox()
        for color in BACKGROUNDS:
            self.background.addItem(color_swatch_icon(color), BACKGROUND_NAMES[color], color)
        self.background.setIconSize(QSize(24, 16))
        selected_background = self.background.findData(state.preferences.background)
        self.background.setCurrentIndex(max(0, selected_background))
        self.background.currentIndexChanged.connect(self.update_background_preview)
        self.update_background_preview()

        form = QFormLayout()
        form.addRow("Font size", self.font_size)
        form.addRow("Font", self.font_family)
        form.addRow("Editor background", self.background)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Save)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        title = QLabel("top-notes settings")
        title.setObjectName("settingsTitle")
        layout.addWidget(title)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def accept(self) -> None:
        prefs = self.state.preferences
        prefs.font_size = self.font_size.value()
        prefs.font_family = self.font_family.currentText()
        prefs.background = str(self.background.currentData())
        super().accept()

    def update_background_preview(self) -> None:
        color = str(self.background.currentData())
        foreground = "#f8fafc" if color == "#111827" else "#172033"
        self.background.setStyleSheet(
            f"QComboBox {{ background-color: {color}; color: {foreground}; font-weight: 600; }}"
        )


class NewGroupDialog(QDialog):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("top-notes new group")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setMinimumWidth(340)

        title = QLabel("top-notes new group")
        title.setObjectName("settingsTitle")
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Group name")
        self.name_edit.setMaxLength(60)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok
        )
        create_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        if create_button:
            create_button.setText("Create")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(self.name_edit)
        layout.addWidget(buttons)
        self.name_edit.setFocus()

    def group_name(self) -> str:
        return self.name_edit.text().strip()

    def accept(self) -> None:
        if self.group_name():
            super().accept()


class NotesWindow(QMainWindow):
    save_status_changed = Signal(str)

    def __init__(self, state: AppState, store: StateStore, icon: QIcon):
        super().__init__()
        self.state = state
        self.store = store
        self._quitting = False
        self._restoring = True
        self._anchoring = False
        self._save_status = "saved."
        self.setWindowTitle("top-notes")
        self.setWindowIcon(icon)
        self.setMinimumSize(360, 280)
        # Apply the native flags in one operation so the window manager never
        # sees an intermediate, decorated Tool window.
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.resize(state.preferences.width, state.preferences.height)

        self.save_timer = QTimer(self)
        self.save_timer.setSingleShot(True)
        self.save_timer.setInterval(300)
        self.save_timer.timeout.connect(self.save_state)

        self.tabs = QTabWidget()
        tab_bar = ColorTabBar()
        tab_bar.context_requested.connect(self.show_tab_menu)
        tab_bar.close_requested.connect(self.close_note)
        tab_bar.tabBarDoubleClicked.connect(self.rename_note)
        tab_bar.setDrawBase(False)
        self.tabs.setTabBar(tab_bar)
        self.tabs.setTabsClosable(False)
        self.tabs.setMovable(True)
        self.tabs.setDocumentMode(True)
        self.tabs.tabBar().tabMoved.connect(self.reorder_note)

        add_button = QToolButton()
        add_button.setObjectName("newNoteButton")
        add_button.setText("+")
        add_button.setFixedSize(24, 24)
        add_button.setToolTip("Create a note in the current group")
        add_button.clicked.connect(self.add_note)
        tab_corner = QWidget()
        corner_layout = QHBoxLayout(tab_corner)
        corner_layout.setContentsMargins(5, 0, 5, 0)
        corner_layout.addWidget(add_button)
        self.tabs.setCornerWidget(tab_corner, Qt.Corner.TopRightCorner)

        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        layout.addWidget(self.tabs)
        self.resize_grip = CornerSizeGrip(root)
        self.resize_grip.setFixedSize(14, 14)
        self.resize_grip.setToolTip("Drag the lower-left corner to resize")
        self.resize_grip.raise_()
        self.setCentralWidget(root)
        self.position_resize_grip()
        self.load_group()
        self._restoring = False

    def schedule_save(self) -> None:
        self._save_status = "saving..."
        self.save_status_changed.emit(self._save_status)
        self.save_timer.setInterval(300)
        self.save_timer.start()

    def save_state(self) -> None:
        try:
            self.store.save(self.state)
        except OSError:
            # Keep the unsaved state visible and retry without interrupting the
            # editor. A later edit restores the normal 300 ms debounce.
            self._save_status = "saving..."
            self.save_status_changed.emit(self._save_status)
            self.save_timer.setInterval(2000)
            self.save_timer.start()
            return
        self._save_status = "saved."
        self.save_status_changed.emit(self._save_status)

    def load_group(self) -> None:
        self.tabs.clear()
        group = self.state.selected_group()
        if not group.notes:
            group.notes.append(Note())
            self.schedule_save()
        for note in group.notes:
            self.append_note_editor(note)

    def append_note_editor(self, note: Note) -> None:
        editor = NoteEditor(note, self.state)
        editor.changed.connect(self.schedule_save)
        editor.set_save_status(self._save_status)
        self.save_status_changed.connect(editor.set_save_status)
        index = self.tabs.addTab(editor, note.title)
        self.tabs.tabBar().setTabData(index, note.tab_color)
        if isinstance(self.tabs.tabBar(), ColorTabBar):
            self.tabs.tabBar().add_close_button(index)
        self.tabs.setCurrentIndex(index)

    def add_note(self) -> None:
        note = Note()
        self.state.selected_group().notes.append(note)
        self.append_note_editor(note)
        self.schedule_save()

    def close_note(self, index: int) -> None:
        group = self.state.selected_group()
        if 0 <= index < len(group.notes):
            note = group.notes[index]
            answer = QMessageBox.question(
                self,
                "Close note",
                f'Close "{note.title}"?\n\nThis note will be deleted.',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
            group.notes.pop(index)
            self.tabs.removeTab(index)
            if not group.notes:
                note = Note()
                group.notes.append(note)
                self.append_note_editor(note)
            self.schedule_save()

    def reorder_note(self, old: int, new: int) -> None:
        group = self.state.selected_group()
        if old != new and 0 <= old < len(group.notes) and 0 <= new < len(group.notes):
            group.notes.insert(new, group.notes.pop(old))
            self.schedule_save()

    def show_tab_menu(self, index: int, global_position: QPoint) -> None:
        group = self.state.selected_group()
        if not 0 <= index < len(group.notes):
            return
        note = group.notes[index]
        menu = QMenu(self)
        rename = menu.addAction("Rename tab…")
        rename.triggered.connect(lambda: self.rename_note(index))
        color_menu = menu.addMenu("Tab color")
        color_actions = QActionGroup(color_menu)
        for name, color in TAB_COLORS.items():
            action = color_menu.addAction(name.capitalize())
            action.setCheckable(True)
            action.setChecked(name == note.tab_color)
            action.setIcon(self.color_icon(color))
            color_actions.addAction(action)
            action.triggered.connect(lambda checked=False, value=name: self.set_tab_color(index, value))
        menu.exec(global_position)

    @staticmethod
    def color_icon(color: str) -> QIcon:
        from PySide6.QtGui import QPixmap

        pixmap = QPixmap(14, 14)
        pixmap.fill(QColor(color))
        return QIcon(pixmap)

    def rename_note(self, index: int) -> None:
        if not 0 <= index < len(self.state.selected_group().notes):
            return
        note = self.state.selected_group().notes[index]
        title, accepted = QInputDialog.getText(self, "Rename note", "Tab title", text=note.title)
        if accepted and title.strip():
            note.title = title.strip()[:80]
            self.tabs.setTabText(index, note.title)
            self.schedule_save()

    def set_tab_color(self, index: int, color: str) -> None:
        note = self.state.selected_group().notes[index]
        note.tab_color = color
        self.tabs.tabBar().setTabData(index, color)
        self.tabs.tabBar().update()
        self.schedule_save()

    def switch_group(self, group_id: str) -> None:
        if group_id == self.state.selected_group_id:
            return
        self.state.selected_group_id = group_id
        self.load_group()
        self.schedule_save()

    def create_group(self) -> None:
        dialog = NewGroupDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            group = Group(name=dialog.group_name()[:60], notes=[Note()])
            self.state.groups.append(group)
            self.state.selected_group_id = group.id
            self.load_group()
            self.schedule_save()

    def delete_current_group(self) -> None:
        group = self.state.selected_group()
        answer = QMessageBox.question(
            self,
            "Delete group",
            f'Delete the entire group "{group.name}" and all of its notes?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        index = self.state.groups.index(group)
        self.state.groups.pop(index)
        if not self.state.groups:
            replacement = Group(notes=[Note()])
            self.state.groups.append(replacement)
        selected_index = min(index, len(self.state.groups) - 1)
        self.state.selected_group_id = self.state.groups[selected_index].id
        self.load_group()
        self.schedule_save()

    def open_settings(self) -> None:
        dialog = SettingsDialog(self.state, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            for index in range(self.tabs.count()):
                editor = self.tabs.widget(index)
                if isinstance(editor, NoteEditor):
                    editor.apply_preferences()
            self.schedule_save()

    def toggle_visible(self) -> None:
        if self.isVisible() and not self.isMinimized():
            self.hide()
        else:
            self.anchor_top_right()
            self.showNormal()
            self.raise_()
            self.activateWindow()

    def anchor_top_right(self) -> None:
        screen = QApplication.screenAt(self.frameGeometry().center()) or QApplication.primaryScreen()
        if screen:
            area = screen.availableGeometry()
            self._anchoring = True
            bounded = QSize(min(self.width(), area.width()), min(self.height(), area.height()))
            if bounded != self.size():
                self.resize(bounded)
            self.move(area.x() + area.width() - self.width(), area.y())
            self._anchoring = False

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.position_resize_grip()
        if not self._restoring and not self.isMaximized():
            self.state.preferences.width = event.size().width()
            self.state.preferences.height = event.size().height()
            self.schedule_save()
            if not self._anchoring:
                QTimer.singleShot(0, self.anchor_top_right)

    def position_resize_grip(self) -> None:
        if hasattr(self, "resize_grip") and self.centralWidget():
            self.resize_grip.move(0, max(0, self.centralWidget().height() - self.resize_grip.height()))
            self.resize_grip.raise_()

    def closeEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        if self._quitting:
            self.store.save(self.state)
            event.accept()
        else:
            event.ignore()

    def quit(self) -> None:
        self._quitting = True
        self.store.save(self.state)
        QApplication.quit()


class TrayController:
    def __init__(self, window: NotesWindow, icon: QIcon):
        self.window = window
        self.tray = QSystemTrayIcon(icon, window)
        self.tray.setToolTip(f"top-notes {__version__} — click to show or hide")
        self.menu = QMenu()
        self.menu.aboutToShow.connect(self.rebuild_menu)
        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self.activated)
        self.tray.show()

    def activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
            QSystemTrayIcon.ActivationReason.Unknown,
        ):
            self.window.toggle_visible()

    def rebuild_menu(self) -> None:
        self.menu.clear()
        toggle = self.menu.addAction("Hide editor" if self.window.isVisible() else "Show editor")
        toggle.triggered.connect(self.window.toggle_visible)
        self.menu.setDefaultAction(toggle)
        self.menu.addSeparator()
        heading = self.menu.addAction("Groups")
        heading.setEnabled(False)
        group_actions = QActionGroup(self.menu)
        group_actions.setExclusive(True)
        for group in self.window.state.groups:
            action = self.menu.addAction(group.name)
            action.setCheckable(True)
            action.setChecked(group.id == self.window.state.selected_group_id)
            group_actions.addAction(action)
            action.triggered.connect(lambda checked=False, value=group.id: self.window.switch_group(value))
        self.menu.addSeparator()
        self.menu.addAction("New group…", self.window.create_group)
        self.menu.addAction("Delete current group…", self.window.delete_current_group)
        self.menu.addAction("Settings…", self.window.open_settings)
        self.menu.addSeparator()
        self.menu.addAction("Quit", self.window.quit)
