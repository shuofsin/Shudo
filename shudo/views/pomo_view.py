"""Pomodoro"""

import curses
import time

class PomoView:

    def __init__(self, app):
        self.app = app
        self.running = False
        self.phase = "work"
        self.remaining = 0
        self.work_duration = 25 * 60
        self.rest_duration = 5 * 60
        self.task_id = None
        self.start_time = 0
        self.paused = False
        self.pause_remaining = 0
    
    def refresh_data(self):
        pass

    def render(self, stdscr, y_start, y_end):
        h = self.app.height
        w = self.app.width

        center_y = h // 2 - 2
        center_x = w // 2

        phase_label = "WORK" if self.phase == "work" else "REST"
        phase_attr = curses.color_pair(1) | curses.A_BOLD if self.phase == "work" else curses.A_BOLD
        stdscr.addstr(center_y - 2, center_x - len(phase_label) // 2, phase_label, phase_attr)

        mins = self.remaining // 60
        secs = self.remaining % 60
        time_str = f"{mins:02d}:{secs:02d}"
        stdscr.addstr(center_y, center_x - len(time_str) // 2, time_str, curses.A_BOLD)

        total = self.work_duration if self.phase == "work" else self.rest_duration
        if total > 0:
            progress = 1 - (self.remaining / total)
            bar_w = min(w - 10, 40)
            filled = int(bar_w * progress)
            bar = "█" * filled + "░" * (bar_w - filled)
            stdscr.addstr(center_y + 1, center_x - bar_w // 2, bar, curses.A_DIM)

        stdscr.hline(h - 3, 0, ' ', w)
        stdscr.addstr(h - 3, 1, self.shortcut_hints(), curses.color_pair(1) | curses.A_DIM)
    
    def handle_key(self, key):
        if key == ord(' '):
            if not self.running:
                self.start_timer()
            elif self.paused:
                self.resume_timer()
            else:
                self.pause_timer()
        elif key == ord('r'):
            self.reset_timer()
        elif key == ord('w'):
            self.set_duration()
        elif key == ord('q'):
            if self.running:
                self.stop_timer()
    
    def shortcut_hints(self):
        if not self.running:
            return "[Space] Start  [w] Set work time  [q] Back"
        elif self.paused:
            return "[Space] Resume  [r] Reset  [q] Back"
        else:
            return "[Space] Pause  [r] Reset  [q] Back"
    
    def start_timer(self):
        self.running = True
        self.paused = False
        self.remaining = self.work_duration
        self.phase = "work"
        self.start_time = time.time()
        self._run_timer()
    
    def pause_timer(self):
        self.paused = True
        self.pause_remaining = self.remaining
    
    def resume_timer(self):
        self.paused = False
        self.start_time = time.time()
        self.remaining = self.pause_remaining
        self._run_timer()
    
    def reset_timer(self):
        self.running = False
        self.paused = False
        self.remaining = 0
        self.phase = "work"
    
    def stop_timer(self):
        self.running = False
        self.paused = False
        self.remaining = 0
    
    def set_duration(self):
        prompt = self.app.prompt("Work minutes: ", "25")
        try: 
            mins = int(prompt)
            if mins > 0:
                self.work_duration = mins * 60
        except ValueError:
            # TODO - Throw toast message error and reprompt user
            pass
        prompt = self.app.prompt("Rest minutes: ", "5")
        try:
            mins = int(prompt)
            if mins > 0:
                self.rest_duration = mins * 60
        except ValueError:
            # TODO - Throw toast message error and reprompt user
            pass
        self.app.set_toast_message(f"Work: {self.work_duration//60}m Rest: {self.rest_duration//60}m")
    
    def _run_timer(self):
        app = self.app
        stdscr = app.stdscr

        while self.running and not self.paused:
            now = time.time()
            elapsed = int(now - self.start_time)
            self.remaining = max(0, self.work_duration - elapsed) if self.phase == "work" else max(0, self.rest_duration - elapsed)

            if self.remaining <= 0:
                if self.phase == "work":
                    app.db.add_pomo_session(self.task_id, self.work_duration // 60, self.rest_duration // 60)
                    app.set_toast_message("Work session complete! Take a break...")
                    self.phase = "rest"
                    self.remaining = self.rest_duration
                    self.start_time = time.time()
                else:
                    app.set_toast_message("Time's up! Get ready to work...")
                    self.phase = "work"
                    self.remaining = self.work_duration
                    self.start_time = time.time()
            
            stdscr.erase()
            app.draw_header()
            self.render(stdscr, 2, app.height - 3)
            app.draw_command_string()
            app.draw_toast_message()
            stdscr.refresh()

            key = stdscr.getch()
            if key != -1:
                if key == ord(' '):
                    self.pause_timer()
                    break
                elif key == ord('r'):
                    self.reset_timer()
                    break
                elif key == ord('q'):
                    self.stop_timer()
                    break

            time.sleep(0.1)