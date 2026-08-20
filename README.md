<p align="center">
  <img src="src/top_notes/resources/top-notes.svg" width="104" alt="top-notes icon">
</p>

<h1 align="center">top-notes</h1>

<p align="center">
  <strong>A calm, beautiful notes app that lives in your Linux system tray.</strong><br>
  Keep ideas close, organised, and out of the way until you need them.
</p>

<p align="center">
  <img alt="Python 3.10 or newer" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white">
  <img alt="Linux" src="https://img.shields.io/badge/Platform-Linux-FCC624?logo=linux&logoColor=black">
  <img alt="License MIT" src="https://img.shields.io/badge/License-MIT-2ea44f">
  <img alt="Version 1.0" src="https://img.shields.io/badge/Version-1.0-8250df">
</p>

---

## Your thoughts, one click away

top-notes is a lightweight rich-text editor designed for quick notes throughout
the day. It stays tucked into the system tray, then appears in the upper-right
corner of your desktop whenever inspiration strikes.

There are no accounts to create, no sync service to configure, and no network
connection required. Your notes remain on your computer.

## Highlights

| | Feature | What it gives you |
| :--: | :-- | :-- |
| 🗂️ | **Groups & tabs** | Keep separate collections for work, home, ideas, or anything else. Tabs can be renamed, reordered, and closed. |
| ✨ | **Rich text** | Format selections with bold, italic, underline, strikethrough, text colours, font families, and sizes. |
| 🎨 | **Made to feel like yours** | Choose from seven tab accents and a selection of editor backgrounds. |
| 📌 | **Always within reach** | Show or hide the editor with a click on the tray icon. It stays neatly anchored at the top-right of your desktop. |
| 💾 | **Private local saving** | Notes and preferences are stored locally, with atomic saves to help protect against interrupted writes. |
| ⚡ | **Delightfully small** | A focused desktop app with one runtime dependency and no browser engine, telemetry, plugins, or network activity. |

## Install

### From a GitHub release

Download the `top_notes-1.0-py3-none-any.whl` file from this repository’s
latest release, then install it with Python:

```bash
python3 -m pip install ./top_notes-1.0-py3-none-any.whl
```

### From PyPI

Once the package is published on PyPI, installation is even simpler:

```bash
python3 -m pip install top-notes
```

## Run

Launch top-notes from your application menu, or run:

```bash
top-notes
```

Python 3.10 or newer and a Linux desktop environment with a system tray are
required. If your desktop does not show tray icons by default, enable its
compatible system-tray or AppIndicator extension.

## How it works

- **Click** the tray icon to show or hide your notes.
- **Right-click** the tray icon to switch or create groups, open settings, or quit.
- Use the **+** button beside the tabs to add a note.
- **Right-click a tab** to rename it or choose its accent colour.
- Select text to reveal familiar formatting controls.
- Resize the editor using the subtle grip in its lower-left corner.

Your window size, appearance, groups, and notes are remembered automatically.

## Privacy

top-notes is built around a simple promise: your notes are yours.

- No account or sign-in
- No telemetry or analytics
- No cloud sync
- No network requests
- No third-party plugins

All content stays in your operating system’s standard local application-data
location.

## License

top-notes is released under the [MIT License](LICENSE). © 2026 spaceshit.
