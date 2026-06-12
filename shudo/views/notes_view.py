"""Notes"""

import curses

class NotesView:
    """Display and manage notes"""

    def __init__(self, app):
        self.app = app
        self.selected_index = 0
        self.notes = []
    
    def refresh_data(self):
        self.notes = self.app.db.get_notes()
        if self.selected_index >= len(self.notes):
            self.selected_index = max(0, len(self.notes) - 1)
    
    def render(self, stdscr, y_start, y_end):
        self.refresh_data()
        y = y_start

        if not self.notes:
            stdscr.addstr(y, 2, "No notes yet.", curses.color_pair(1))
            return

        for i, note in enumerate(self.notes):
            if y >= y_end - 1:
                break

            prefix = "> " if i == self.selected_index else "  "
            title = note["title"]
            max_w = self.app.width - 6
            if len(title) > max_w:
                title = title[:max_w - 3] + "..."
            
            attr = curses.color_pair(2) | curses.A_BOLD if i == self.selected_index else curses.color_pair(1)
            stdscr.addstr(y, 2, f"{prefix}{title}", attr)
            y += 1
        
        stdscr.hline(y_end, 0, ' ', self.app.width)
        stdscr.addstr(y_end, 1, self.shortcut_hints(), curses.color_pair(1))

    def handle_key(self, key):
        """Handle a keypress"""
        if key == ord('n'):
            self.create_note()
        elif key == ord('d'):
            self.delete_note()
        elif key == ord('s'):
            self.search_notes()
        elif key == ord('\n') and self.notes:
            note = self.notes[self.selected_index]
            self._open_editor(note["title"], note["content"], note["id"])
        elif key == curses.KEY_UP and self.selected_index > 0:
            self.selected_index -= 1
        elif key == curses.KEY_DOWN and self.selected_index < len(self.notes) - 1:
            self.selected_index += 1
    
    def shortcut_hints(self):
        return "[n] New  [d] Delete  [s] Search  ↑↓ Navigate"

    def create_note(self):
        title = self.app.prompt("Title: ")
        if not title:
            return 
        self._open_editor(title, "", None)
    
    def delete_note(self):
        if not self.notes:
            return

        note_id = self.notes[self.selected_index]["id"]
        self.app.db.delete_note(note_id)
        self.app.set_toast_message("Note deleted!")
        self.refresh_data()
    
    def search_notes(self):
        # TODO
        self.app.set_toast_message("Search coming soon!")
    
    def _open_editor(self, title, existing_content, note_id=None):
        app = self.app
        stdscr = app.stdscr
        stdscr.nodelay(False)


        original_view = app.current_view

        lines = existing_content.split("\n") if existing_content else [""]
        cursor_y = 0
        cursor_x = 0
        editing = True

        while editing:
            stdscr.erase()

            # Header
            h = stdscr
            x = 1
            for ch in "ShuDo  |  Edit note ":
                h.addch(0, x, ch, curses.color_pair(1) | curses.A_BOLD)
                x += 1
            h.hline(0, x, ' ', app.width - x)

            # Title bar
            stdscr.hline(1, 1, '-', app.width, curses.color_pair(1))
            stdscr.addstr(2, 2, title, curses.color_pair(1))
            stdscr.hline(3, 1, '-', app.width, curses.color_pair(1))

            # Content area
            max_y = app.height - 4
            for i, line in enumerate(lines):
                if i + 4 >= max_y:
                    break
                stdscr.addstr(i + 4, 2, line[:app.width - 4])
            
            # Command string
            cmd_y = app.height - 2
            stdscr.hline(cmd_y, 0, ' ', app.width)
            stdscr.addstr(cmd_y, 2, "[ctrl + d] Save  [ctrl + x] Exit  [ctrl + r] Rename", curses.color_pair(1))

            # Toast
            app.draw_toast_message()

            # Cursor
            curses.curs_set(1)
            stdscr.move(cursor_y + 4, cursor_x + 2)
            stdscr.refresh()

            # Input
            key = stdscr.getch()

            if key == 4:
                content = "\n".join(lines).strip()
                if content:
                    if existing_content:
                        app.db.update_note(note_id, title, content)
                    else:
                        note_id = app.db.add_note(title, content)
                        existing_content = content
                    app.set_toast_message("Note saved!")
                    self.refresh_data()

            elif key == 24:
                # check for unsaved changes
                current_content = "\n".join(lines).strip()
                if current_content != existing_content:
                    app.set_toast_message("Close note? Unsaved changes will be lost. [y] Yes  [n] No")
                    app.draw_toast_message()
                    stdscr.refresh()

                    while True:
                        confirm = stdscr.getch()
                        if confirm == ord('y'):
                            editing = False
                            app.set_toast_message("")
                            app.draw_toast_message()
                            break
                        elif confirm == ord('n'):
                            app.set_toast_message("")
                            app.draw_toast_message()
                            break
                else:
                    editing = False

            elif key == 18:
                new_title = self.app.prompt("New Title: ", title)
                if new_title and new_title != title:
                    title = new_title
                    if note_id is not None:
                        content = "\n".join(lines).strip()
                        app.db.update_note(note_id, title, content)
                    app.set_toast_message(f"Title changed to '{title}'")

            elif key == curses.KEY_UP and cursor_y > 0:
                cursor_y -= 1
                cursor_x = min(cursor_x, len(lines[cursor_y]))

            elif key == curses.KEY_DOWN and cursor_y < len(lines) - 1:
                cursor_y += 1
                cursor_x = min(cursor_x, len(lines[cursor_y]))

            elif key == curses.KEY_LEFT and cursor_x > 0:
                cursor_x -= 1

            elif key == curses.KEY_RIGHT and cursor_x < len(lines[cursor_y]):
                cursor_x += 1
            
            elif key == ord('\n'):  # Enter — split line
                new_line = lines[cursor_y][cursor_x:]
                lines[cursor_y] = lines[cursor_y][:cursor_x]
                lines.insert(cursor_y + 1, new_line)
                cursor_y += 1
                cursor_x = 0
            
            elif key == 127 or key == curses.KEY_BACKSPACE:  # Backspace
                if cursor_x > 0:
                    lines[cursor_y] = lines[cursor_y][:cursor_x - 1] + lines[cursor_y][cursor_x:]
                    cursor_x -= 1
                elif cursor_y > 0:
                    cursor_x = len(lines[cursor_y - 1])
                    lines[cursor_y - 1] += lines[cursor_y]
                    del lines[cursor_y]
                    cursor_y -= 1

            elif key == 330 or key == curses.KEY_DC:  # Delete
                if cursor_x < len(lines[cursor_y]):
                    lines[cursor_y] = lines[cursor_y][:cursor_x] + lines[cursor_y][cursor_x + 1:]
                elif cursor_y < len(lines) - 1:
                    lines[cursor_y] += lines[cursor_y + 1]
                    del lines[cursor_y + 1]
            
            elif key == ord('\t'):
                spaces = "    "
                lines[cursor_y] = lines[cursor_y][:cursor_x] + spaces + lines[cursor_y][cursor_x:]
                cursor_x += 4

            elif 32 <= key <= 126:  # printable characters
                ch = chr(key)
                lines[cursor_y] = lines[cursor_y][:cursor_x] + ch + lines[cursor_y][cursor_x:]
                cursor_x += 1

        app.current_view = original_view
        stdscr.nodelay(True)
        curses.curs_set(0)