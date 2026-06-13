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

    # ── tick (called by main loop) ──────────────────────────────

    def tick(self):
        """Decrement timer. Called every frame from main loop."""
        if not self.running or self.paused:
            return

        now = time.time()
        elapsed = int(now - self.last_tick)
        if elapsed <= 0:
            return

        self.remaining -= elapsed
        self.last_tick = now

        if self.remaining <= 0:
            if self.phase == "work":
                self.app.db.add_pomo_session(
                    self.task_id, self.work_duration // 60, self.rest_duration // 60
                )
                self.app.set_toast_message("Work complete! Take a break...")
                self.phase = "rest"
                self.remaining = self.rest_duration
            else:
                self.app.set_toast_message("Rest complete! Ready to work.")
                self.phase = "work"
                self.remaining = self.work_duration

    def mini_status(self):
        """Short string for the toast bar when on another view."""
        if not self.running:
            return ""
        if self.paused:
            return "POMODORO — PAUSED"
        mins = self.remaining // 60
        secs = self.remaining % 60
        label = "WORK" if self.phase == "work" else "REST"
        return f"POMODORO — {label} {mins:02d}:{secs:02d}"

    # ── rendering ───────────────────────────────────────────────

    def render(self, stdscr, y_start, y_end):
        h = self.app.height
        w = self.app.width

        center_y = h // 2 - 2
        center_x = w // 2

        phase_label = "WORK" if self.phase == "work" else "REST"
        attr = curses.color_pair(1) | curses.A_BOLD if self.phase == "work" else curses.A_BOLD
        stdscr.addstr(center_y - 2, center_x - len(phase_label) // 2, phase_label, attr)

        mins = self.remaining // 60
        secs = self.remaining % 60
        time_str = f"{mins:02d}:{secs:02d}"
        if self.paused:
            time_str += " (paused)"
        stdscr.addstr(center_y, center_x - len(time_str) // 2, time_str, curses.A_BOLD)

        total = self.work_duration if self.phase == "work" else self.rest_duration
        if total > 0:
            progress = 1 - (self.remaining / total) if self.running else 0
            bar_w = min(w - 10, 40)
            filled = int(bar_w * progress)
            bar = "█" * filled + "░" * (bar_w - filled)
            stdscr.addstr(center_y + 1, center_x - bar_w // 2, bar, curses.A_DIM)

        stdscr.addstr(center_y + 3, center_x - 10,
                      f"Work: {self.work_duration//60}m  Rest: {self.rest_duration//60}m",
                      curses.A_DIM)

        stdscr.hline(h - 3, 0, ' ', w)
        stdscr.addstr(h - 3, 1, self.shortcut_hints(), curses.color_pair(1) | curses.A_DIM)
    
    # ── controls ────────────────────────────────────────────────

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
    
    def shortcut_hints(self):
        if not self.running:
            return "[Space] Start  [w] Set time"
        elif self.paused:
            return "[Space] Resume  [r] Reset"
        else:
            return "[Space] Pause  [r] Reset"

    def start_timer(self):
        self.running = True
        self.paused = False
        self.remaining = self.work_duration
        self.phase = "work"
        self.last_tick = time.time()
        self.app.set_toast_message("Pomodoro started!")

    def pause_timer(self):
        self.paused = True
    
    def resume_timer(self):
        self.paused = False
        self.last_tick = time.time()

    def reset_timer(self):
        self.running = False
        self.paused = False
        self.remaining = 0
        self.phase = "work"
        self.app.set_toast_message("")

    def set_duration(self):
        prompt = self.app.prompt("Work minutes: ", "25")
        try: 
            mins = int(prompt)
            if mins > 0:
                self.work_duration = mins * 60
        except ValueError:
            pass
        prompt = self.app.prompt("Rest minutes: ", "5")
        try:
            mins = int(prompt)
            if mins > 0:
                self.rest_duration = mins * 60
        except ValueError:
            pass
        self.app.set_toast_message(f"Work: {self.work_duration//60}m  Rest: {self.rest_duration//60}m")