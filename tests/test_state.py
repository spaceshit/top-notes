import tempfile
import unittest
from pathlib import Path

from top_notes.state import AppState, Group, Note, StateStore


class StateTests(unittest.TestCase):
    def test_default_state_has_a_group_and_note(self):
        state = AppState.default()
        self.assertEqual(len(state.groups), 1)
        self.assertEqual(len(state.selected_group().notes), 1)

    def test_round_trip_preserves_groups_notes_and_preferences(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            state = AppState.default()
            state.groups.append(Group(name="Work", notes=[Note(title="Plan", tab_color="cyan")]))
            state.selected_group_id = state.groups[-1].id
            state.preferences.width = 777
            StateStore(path).save(state)

            loaded = StateStore(path).load()
            self.assertEqual(loaded.selected_group().name, "Work")
            self.assertEqual(loaded.selected_group().notes[0].title, "Plan")
            self.assertEqual(loaded.selected_group().notes[0].tab_color, "cyan")
            self.assertEqual(loaded.preferences.width, 777)

    def test_malformed_state_recovers_to_defaults(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            path.write_text("not json", encoding="utf-8")
            state = StateStore(path).load()
            self.assertTrue(state.groups)

    def test_untrusted_values_are_bounded(self):
        state = AppState.from_dict(
            {
                "groups": [
                    {
                        "name": "x",
                        "notes": [{"mode": "markdown", "content": "<b>kept</b>", "tab_color": "pink"}],
                    }
                ],
                "preferences": {"font_size": 999, "width": -4, "height": 99999, "background": "url(x)"},
            }
        )
        self.assertEqual(state.selected_group().notes[0].tab_color, "white")
        self.assertEqual(state.selected_group().notes[0].content, "<b>kept</b>")
        self.assertEqual(state.preferences.font_size, 32)
        self.assertEqual(state.preferences.width, 360)
        self.assertEqual(state.preferences.height, 1200)


if __name__ == "__main__":
    unittest.main()
