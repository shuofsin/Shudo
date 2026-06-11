# ShuDo — Interactive Terminal (TUI) Productivity Tool

## Core Idea
A persistent terminal app (like `htop`/`vim`) with three integrated features, built with **Python `curses`**:
1. **Notes** — quick scratchpad / sticky notes, searchable
2. **Todo list** — tasks with priority (high/medium/low), mark done
3. **Pomodoro** — timer with session logging

You run `python shudo.py` (or eventually `shudo`) and the app stays open, ready to use in its own terminal pane.

## Tech
- Python 3 + SQLite + `curses` (all stdlib, zero external deps)

## Database (3 tables)
- `notes` (id, title, content, created_at)
- `todos` (id, task, priority, status, created_at)
- `pomo_sessions` (id, task_id, duration_minutes, completed_at)

## Interactive UI (curses-based)

| Key        | Action                    |
|------------|---------------------------|
| `Tab`      | Switch view (Notes/Tasks/Pomo) |
| `n`        | New item in current view   |
| `d`        | Delete selected item       |
| `Enter`    | Open / toggle done         |
| `s`        | Search notes               |
| `p`        | Start pomodoro timer       |
| `q` / `Esc`| Quit app                   |

### Views
- **Notes** — scrollable list of notes, inline detail view
- **Tasks** — scrollable list with priority colors, toggle done
- **Pomo** — countdown timer, stats summary, session history

## What to Build Next (Pick Order)

- [ ] Notes CRUD (add, list, search, delete, edit)
- [ ] Todos CRUD (add, list, mark done, delete, edit)
- [ ] Pomodoro timer with countdown (no threads, use `time`)
- [ ] Tab-based navigation between views
- [ ] `today` summary view
- [ ] Pomodoro -> todo linking
- [ ] Desktop notification on timer end
- [ ] Export to JSON/CSV
- [ ] Make it installable with `pip` / command alias

## Project Structure

```
shudo/
├── shudo.py          ← Entry point (curses main loop)
├── db.py             ← Database setup + queries
├── views/            ← Screen renderers
│   ├── notes_view.py
│   ├── tasks_view.py
│   └── pomo_view.py
└── docs/
    └── shudo-project-spec.md
```

## Current Focus
*(Update this line before coding each session)*

> Working on: Planning the build — just finished renaming from 'MyDay' to 'ShuDo'