"""Tasks view for ShuDo — kanban board with three columns."""

import curses
import json


class TasksView:
    """Display tasks in a kanban board (Ready | Ongoing | Done)."""

    COLUMNS = ["Ready", "Ongoing", "Done"]
    COL_STATUS = ["ready", "ongoing", "done"]

    def __init__(self, app):
        self.app = app
        self.col_index = 0       # which column (0=Ready, 1=Ongoing, 2=Done)
        self.row_index = 0       # which row within that column
        self.tasks = []          # all tasks
        self.col_tasks = [[], [], []]  # tasks split by column

    def refresh_data(self):
        self.tasks = self.app.db.get_tasks()
        # split into columns
        self.col_tasks = [[], [], []]
        for t in self.tasks:
            if t["status"] == "ready":
                self.col_tasks[0].append(t)
            elif t["status"] == "ongoing":
                self.col_tasks[1].append(t)
            elif t["status"] == "done":
                self.col_tasks[2].append(t)
        # clamp row index
        current = self.col_tasks[self.col_index]
        if self.row_index >= len(current):
            self.row_index = max(0, len(current) - 1)

    def render(self, stdscr, y_start, y_end):
        self.refresh_data()
        h = self.app.height
        w = self.app.width

        # ── column headers ───────────────────────────────────────
        col_w = w // 3
        for ci, name in enumerate(self.COLUMNS):
            x = ci * col_w
            attr = curses.color_pair(1) | curses.A_BOLD if ci == self.col_index else curses.A_DIM
            stdscr.addstr(y_start, x + 2, f" {name} ", attr)

        # ── empty state ──────────────────────────────────────────
        if not self.tasks:
            msg = "No tasks. Hooray!"
            x = w // 2 - len(msg) // 2
            stdscr.addstr(h // 2, x, msg, curses.color_pair(1))
            stdscr.hline(h - 3, 0, ' ', w)
            stdscr.addstr(h - 3, 1, self.shortcut_hints(), curses.color_pair(1) | curses.A_DIM)
            return

        # ── task rows ────────────────────────────────────────────
        content_y = y_start + 2
        max_y = h - 3

        for ci in range(3):
            tasks_in_col = self.col_tasks[ci]
            x = ci * col_w + 2
            max_task_w = col_w - 4

            for ri, task in enumerate(tasks_in_col):
                y = content_y + ri
                if y >= max_y:
                    break

                is_selected = (ci == self.col_index and ri == self.row_index)

                # prefix
                if is_selected:
                    prefix = "▸ "
                else:
                    prefix = "  "

                # priority marker
                p_map = {"high": "H", "medium": "M", "low": "L"}
                p_marker = p_map.get(task["priority"], "M")

                # status icon
                if task["status"] == "ready":
                    status_icon = "-"
                elif task["status"] == "ongoing":
                    status_icon = "~"
                else:
                    status_icon = "✓"

                attr = curses.A_BOLD if is_selected else curses.A_NORMAL

                # task text
                task_text = task["task"]
                if len(task_text) > max_task_w - 4:
                    task_text = task_text[:max_task_w - 7] + "..."

                # subtask count
                subtasks = json.loads(task["subtasks"]) if task["subtasks"] else []
                done_count = sum(1 for s in subtasks if s.get("done"))
                sub_info = f" [{done_count}/{len(subtasks)}]" if subtasks else ""

                line = f"{prefix}{status_icon} [{p_marker}] {task_text}{sub_info}"
                if len(line) > max_task_w:
                    line = line[:max_task_w - 3] + "..."

                try:
                    if is_selected:
                        stdscr.addstr(y, x, "▸ ", curses.color_pair(1) | curses.A_BOLD)
                        stdscr.addstr(y, x + 2, line[2:], attr)
                    else:
                        stdscr.addstr(y, x, line, attr)
                except:
                    pass

        # ── hints ────────────────────────────────────────────────
        stdscr.hline(h - 3, 0, ' ', w)
        stdscr.addstr(h - 3, 1, self.shortcut_hints(), curses.color_pair(1) | curses.A_DIM)

    def handle_key(self, key):
        if key == ord('n'):
            self.add_task()
        elif key == ord('d'):
            self.delete_task()
        elif key == ord('\n') and self.col_tasks[self.col_index]:
            self.open_task_editor()
        elif key == curses.KEY_LEFT and self.col_index > 0:
            self.col_index -= 1
            self.row_index = 0
        elif key == curses.KEY_RIGHT and self.col_index < 2:
            self.col_index += 1
            self.row_index = 0
        elif key == curses.KEY_SLEFT and self.col_index > 0:
            self._move_selected_task(self.col_index - 1)
        elif key == curses.KEY_SRIGHT and self.col_index < 2:
            self._move_selected_task(self.col_index + 1)
        elif key == curses.KEY_UP:
            if self.row_index > 0:
                self.row_index -= 1
        elif key == curses.KEY_DOWN:
            current = self.col_tasks[self.col_index]
            if self.row_index < len(current) - 1:
                self.row_index += 1

    def shortcut_hints(self):
        return "[n] New  [d] Delete  [Enter] Edit  [shift + ←→] Move task"

    # ── add task ─────────────────────────────────────────────────

    def add_task(self):
        task_name = self.app.prompt("Task: ")
        if not task_name:
            return
        priority = self.app.prompt("Priority (h/m/l): ", "m")
        p_map = {"h": "high", "m": "medium", "l": "low"}
        priority = p_map.get(priority, "medium")
        self.app.db.add_task(task_name, priority)
        self.app.set_toast_message("Task added!")
        self.refresh_data()

    # ── delete task ──────────────────────────────────────────────

    def delete_task(self):
        current = self.col_tasks[self.col_index]
        if not current:
            return
        task_id = current[self.row_index]["id"]
        self.app.db.delete_task(task_id)
        self.app.set_toast_message("Task deleted!")
        self.refresh_data()

    def _move_selected_task(self, target_col):
        """Move the selected task to another column."""
        current = self.col_tasks[self.col_index]
        if not current:
            return
        task = current[self.row_index]
        new_status = self.COL_STATUS[target_col]
        self.app.db.update_task_status(task["id"], new_status)
        self.app.set_toast_message(f"Moved to {self.COLUMNS[target_col]}")
        self.col_index = target_col
        self.row_index = 0
        self.refresh_data()

    # ── task editor ──────────────────────────────────────────────

    def open_task_editor(self):
        """Open the task editor (view mode with subtask toggle)."""
        task = self.col_tasks[self.col_index][self.row_index]
        app = self.app
        stdscr = app.stdscr
        stdscr.nodelay(False)

        task_id = task["id"]
        task_name = task["task"]
        task_priority = task["priority"]
        task_status = task["status"]
        subtasks = json.loads(task["subtasks"]) if task["subtasks"] else []
        editing = True
        mode = "view"  # "view" or "edit"
        cursor_pos = 0  # which line the cursor is on (0 = task name, 1+ = subtasks)

        while editing:
            stdscr.erase()

            # ── header ────────────────────────────────────────────
            mode_label = "Edit Task" if mode == "edit" else "View Task"
            h = stdscr
            x = 1
            for ch in f" ShuDo  |  {mode_label} ":
                h.addch(0, x, ch, curses.color_pair(1) | curses.A_BOLD)
                x += 1
            h.hline(0, x, ' ', app.width - x)

            # ── task name line ────────────────────────────────────
            stdscr.hline(1, 0, '-', app.width)
            attr = curses.A_BOLD if (mode == "edit" and cursor_pos == 0) else curses.A_NORMAL
            stdscr.addstr(2, 2, task_name, attr)
            stdscr.hline(3, 0, '-', app.width)

            # ── status/priority subbar ────────────────────────────
            p_label = task_priority.capitalize()
            s_label = task_status.capitalize()
            stdscr.addstr(4, 2, f"[{p_label}] [{s_label}]", curses.A_DIM)
            stdscr.hline(5, 0, '-', app.width)

            # ── subtask list ──────────────────────────────────────
            for i, sub in enumerate(subtasks):
                y = 6 + i
                if y >= app.height - 3:
                    break
                check = "[x]" if sub.get("done") else "[ ]"
                text = sub.get("text", "")
                sub_cursor = i + 1
                attr = curses.A_BOLD if ((mode == "edit" and cursor_pos == sub_cursor) or (mode == "view" and cursor_pos == i)) else curses.A_NORMAL
                stdscr.addstr(y, 4, f"{check} {text}", attr)

            # ── command hints ─────────────────────────────────────
            cmd_y = app.height - 2
            stdscr.hline(cmd_y, 0, ' ', app.width)
            if mode == "view":
                stdscr.addstr(cmd_y, 1, "[e] Edit  [q] Back", curses.color_pair(1) | curses.A_DIM)
            else:

                stdscr.addstr(cmd_y, 1, "[ctrl+d] Save  [ctrl+x] Back  [ctrl+v] Priority  [ctrl+b] Status", curses.color_pair(1) | curses.A_DIM)

            # ── toast ─────────────────────────────────────────────
            app.draw_toast_message()

            # ── cursor ────────────────────────────────────────────
            if mode == "edit":
                curses.curs_set(1)
                if cursor_pos == 0:
                    stdscr.move(2, 2 + len(task_name))  # after task name
                else:
                    sub_idx = cursor_pos - 1
                    sub_text = subtasks[sub_idx].get("text", "")
                    stdscr.move(6 + sub_idx, 8 + len(sub_text))
            else:
                curses.curs_set(0)

            stdscr.refresh()

            # ── input ─────────────────────────────────────────────
            key = stdscr.getch()

            if mode == "view":
                if key == ord('q'):
                    editing = False
                elif key == ord('e'):
                    mode = "edit"
                    cursor_pos = 0

            elif mode == "edit":
                if key == 24:  # ctrl+x — back to view mode
                    # check for unsaved changes
                    original_subtasks = json.loads(task["subtasks"]) if task["subtasks"] else []
                    original_priority = task["priority"]
                    if subtasks != original_subtasks or task_name != task["task"] or task_priority != original_priority:
                        app.set_toast_message("Close? Unsaved changes will be lost. [y] Yes  [n] No")
                        app.draw_toast_message()
                        stdscr.refresh()
                        while True:
                            confirm = stdscr.getch()
                            if confirm == ord('y'):
                                app.set_toast_message("")
                                mode = "view"
                                cursor_pos = 0
                                break
                            elif confirm == ord('n'):
                                app.set_toast_message("")
                                break
                    else:
                        mode = "view"
                        cursor_pos = 0
                elif key == 4:  # ctrl+d — save, stay in edit mode
                    # strip empty subtasks
                    subtasks = [s for s in subtasks if s.get("text", "").strip()]
                    app.db.update_task(task_id, task_name, subtasks)
                    app.db.update_task_status(task_id, task_status)
                    # update priority in DB
                    app.db.c.execute("UPDATE tasks SET priority = ? WHERE id = ?", (task_priority, task_id))
                    app.db.conn.commit()
                    app.set_toast_message("Task saved!")
                elif key == 22:  # ctrl+v — cycle priority
                    priorities = ["low", "medium", "high"]
                    idx = priorities.index(task_priority) if task_priority in priorities else 1
                    task_priority = priorities[(idx + 1) % 3]
                elif key == 2:  # ctrl+b — cycle status
                    statuses = ["ready", "ongoing", "done"]
                    idx = statuses.index(task_status) if task_status in statuses else 0
                    task_status = statuses[(idx + 1) % 3]
                elif key == curses.KEY_UP and cursor_pos > 0:
                    cursor_pos -= 1
                elif key == curses.KEY_DOWN:
                    if cursor_pos < len(subtasks):
                        cursor_pos += 1
                elif key == ord('\n'):
                    # only insert if current line has text
                    current_text = task_name if cursor_pos == 0 else subtasks[cursor_pos - 1].get("text", "")
                    if not current_text.strip():
                        continue
                    # insert new subtask line and move cursor to it
                    if cursor_pos == 0:
                        subtasks.insert(0, {"text": "", "done": False})
                        cursor_pos = 1
                    else:
                        subtasks.insert(cursor_pos, {"text": "", "done": False})
                        cursor_pos += 1
                elif key == 127 or key == curses.KEY_BACKSPACE:
                    if cursor_pos == 0:
                        if task_name:
                            task_name = task_name[:-1]
                    else:
                        idx = cursor_pos - 1
                        text = subtasks[idx].get("text", "")
                        if text:
                            subtasks[idx]["text"] = text[:-1]
                        elif len(subtasks) > 0:
                            del subtasks[idx]
                            if cursor_pos > len(subtasks):
                                cursor_pos = len(subtasks)
                elif 32 <= key <= 126:
                    ch = chr(key)
                    if cursor_pos == 0:
                        task_name += ch
                    else:
                        idx = cursor_pos - 1
                        subtasks[idx]["text"] = subtasks[idx].get("text", "") + ch

        stdscr.nodelay(True)
        curses.curs_set(0)
        self.refresh_data()