#!/usr/bin/env python3
"""ShuDo - a cli programming productivity tool"""

import curses
import time

from db import Database
from views.notes_view import NotesView
from views.tasks_view import TasksView

class ShuDoApp:
    """Main application controller."""

    VIEW_NAMES = ["Notes", "Tasks", "Pomo"]
    
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.db = Database()
        self.current_view = 0
        self.running = True
        self.command_str = "[tab] switch views  [q] quit"
        self.toast_message = ""
        self.toast_time = 0.0
        self.toast_duration = 2

        self.views = [
            NotesView(self),
            TasksView(self),
        ]

        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_GREEN, -1)

        curses.curs_set(0)
        self.stdscr.keypad(True)
        self.stdscr.nodelay(True)


    @property
    def width(self):
        return self.stdscr.getmaxyx()[1]

    @property
    def height(self):
        return self.stdscr.getmaxyx()[0]
    
    def draw_header(self):
        h = self.stdscr
        x = 1
        for ch in "ShuDo | ":
            h.addch(0, x, ch, curses.color_pair(1) | curses.A_BOLD)
            x += 1
        for i, name in enumerate(self.VIEW_NAMES):
            if i == self.current_view:
                tab = f" {name} "
                attr = curses.color_pair(1) | curses.A_BOLD
            else:
                tab = f" {name} "
                attr = curses.A_DIM
            for ch in tab:
                if x < self.width:
                    h.addch(0, x, ch, attr)
                    x += 1
        h.hline(0, x, ' ', self.width - x)
    
    def draw_command_string(self):
        """Draw the last-line commands bar."""
        y = self.height - 2
        msg = self.command_str
        self.stdscr.hline(y, 0, ' ', self.width)
        if msg:
            self.stdscr.addstr(y, 1, msg, curses.color_pair(1) | curses.A_DIM)
    
    def draw_toast_message(self):
        """Draw a toast message"""
        y = self.height - 1
        self.stdscr.hline(y, 0, ' ', self.width)

        if time.time() - self.toast_time > self.toast_duration:
            self.toast_message = ""
            return
        
        if self.toast_message:
            self.stdscr.addstr(y, 1, self.toast_message, curses.color_pair(1))

    def set_toast_message(self, message):
        self.toast_message = message
        self.toast_time = time.time()

    def run(self):
        self.db.init_db()
        while self.running:
            self.stdscr.erase()
            self.draw_header()

            self.views[self.current_view].render(
                self.stdscr, 2, self.height - 3
            )

            self.draw_command_string()
            self.draw_toast_message()
            self.stdscr.refresh()

            key = self.stdscr.getch()

            if key == -1:
                time.sleep(0.05)
                continue
            elif key == ord('q'):
                self.running = False
            elif key == ord('\t'):
                self.current_view = (self.current_view + 1) % len(self.VIEW_NAMES)
            elif key == 27: #escape
                self.running = False
            else:
                self.views[self.current_view].handle_key(key)
    
    def prompt(self, label, default=""):
        curses.curs_set(1)
        self.stdscr.nodelay(False)

        y = self.height - 1
        self.stdscr.hline(y, 0, ' ', self.width)
        self.stdscr.addstr(y, 1, label + default, curses.color_pair(1))        

        curses.echo()
        result = self.stdscr.getstr(y, 1 + len(label), 60).decode("utf-8")
        curses.noecho()

        curses.curs_set(0)
        self.stdscr.nodelay(True)

        if not result and default:
            return default
        
        return result.strip()

def main(stdscr):
    app = ShuDoApp(stdscr)
    app.run()

if __name__ == "__main__":
    curses.wrapper(main)