from __future__ import annotations

import json
import os
import tempfile
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Note:
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    title: str = "New note"
    content: str = ""
    tab_color: str = "white"

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Note":
        color = value.get("tab_color", "white")
        return cls(
            id=str(value.get("id") or uuid.uuid4().hex),
            title=str(value.get("title") or "New note")[:80],
            content=str(value.get("content") or ""),
            tab_color=color if color in TAB_COLORS else "white",
        )


@dataclass
class Group:
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    name: str = "Notes"
    notes: list[Note] = field(default_factory=list)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Group":
        return cls(
            id=str(value.get("id") or uuid.uuid4().hex),
            name=str(value.get("name") or "Notes")[:60],
            notes=[Note.from_dict(item) for item in value.get("notes", []) if isinstance(item, dict)],
        )


@dataclass
class Preferences:
    font_size: int = 14
    font_family: str = "Sans Serif"
    background: str = "#fffdf8"
    width: int = 560
    height: int = 520

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Preferences":
        family = str(value.get("font_family", "Sans Serif"))
        if family not in FONT_FAMILIES:
            family = "Sans Serif"
        background = str(value.get("background", "#fffdf8"))
        if background not in BACKGROUNDS:
            background = "#fffdf8"
        return cls(
            font_size=max(9, min(32, int(value.get("font_size", 14)))),
            font_family=family,
            background=background,
            width=max(360, min(1800, int(value.get("width", 560)))),
            height=max(280, min(1200, int(value.get("height", 520)))),
        )


TAB_COLORS = {
    "white": "#f7f4ee",
    "purple": "#d8c7e8",
    "cyan": "#b9dde2",
    "red": "#e8b8b8",
    "blue": "#bfd2e8",
    "green": "#c5ddc5",
    "orange": "#eac7a8",
}
FONT_FAMILIES = ("Sans Serif", "Serif", "Monospace")
BACKGROUNDS = ("#fffdf8", "#ffffff", "#f3f4f6", "#fff7ed", "#ecfeff", "#f5f3ff", "#111827")
BACKGROUND_NAMES = {
    "#fffdf8": "Warm paper",
    "#ffffff": "Clean white",
    "#f3f4f6": "Soft gray",
    "#fff7ed": "Peach",
    "#ecfeff": "Ice blue",
    "#f5f3ff": "Lavender",
    "#111827": "Midnight",
}


@dataclass
class AppState:
    groups: list[Group]
    selected_group_id: str
    preferences: Preferences = field(default_factory=Preferences)

    @classmethod
    def default(cls) -> "AppState":
        group = Group(notes=[Note()])
        return cls(groups=[group], selected_group_id=group.id)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "AppState":
        groups = [Group.from_dict(item) for item in value.get("groups", []) if isinstance(item, dict)]
        if not groups:
            return cls.default()
        selected = str(value.get("selected_group_id") or groups[0].id)
        if selected not in {group.id for group in groups}:
            selected = groups[0].id
        return cls(groups, selected, Preferences.from_dict(value.get("preferences", {})))

    def selected_group(self) -> Group:
        return next((group for group in self.groups if group.id == self.selected_group_id), self.groups[0])


class StateStore:
    """Small, atomic JSON store with recovery from malformed state."""

    def __init__(self, path: Path):
        self.path = path

    def load(self) -> AppState:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return AppState.from_dict(data) if isinstance(data, dict) else AppState.default()
        except (OSError, ValueError, TypeError):
            return AppState.default()

    def save(self, state: AppState) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(asdict(state), ensure_ascii=False, indent=2)
        fd, temporary = tempfile.mkstemp(prefix=".top-notes-", suffix=".json", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
