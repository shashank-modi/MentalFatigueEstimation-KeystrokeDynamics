# src/labeling/gui_scheduler.py
import os, csv, time, signal
import tkinter as tk

LABELS_CSV = "data/labels/labels.csv"
PROMPT_INTERVAL_MIN = 15      # how often to show the popup
LABEL_SPAN_MIN      = 15      # label applies to last N minutes

# ----------------- File Helpers -----------------
def ensure_labels_file():
    """Make sure labels.csv exists with correct header."""
    if not os.path.exists(LABELS_CSV):
        os.makedirs(os.path.dirname(LABELS_CSV), exist_ok=True)
        with open(LABELS_CSV, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["applies_from", "applies_to", "fatigue_score"])

def _save_label_range(t_from_ms: int, t_to_ms: int, score: float):
    """Append one label row to labels.csv."""
    with open(LABELS_CSV, "a", newline="") as f:
        w = csv.writer(f)
        w.writerow([t_from_ms, t_to_ms, float(score)])
    print(f"[label] Saved: [{t_from_ms} → {t_to_ms}] score={score}")

def _last_label_end_ms() -> int | None:
    """Return the last applies_to timestamp from labels.csv (or None)."""
    if not os.path.exists(LABELS_CSV):
        return None
    try:
        with open(LABELS_CSV, "r") as f:
            rows = list(csv.reader(f))
        if len(rows) <= 1:
            return None
        return int(float(rows[-1][1]))
    except Exception:
        return None

# ----------------- UI Helpers -----------------
def draw_round_rect(canvas, x1, y1, x2, y2, r=12, **kwargs):
    """Draw a rounded rectangle on a Canvas."""
    r = max(0, min(r, int((x2 - x1) / 2), int((y2 - y1) / 2)))
    points = [
        x1+r, y1,
        x2-r, y1,
        x2,   y1,
        x2,   y1+r,
        x2,   y2-r,
        x2,   y2,
        x2-r, y2,
        x1+r, y2,
        x1,   y2,
        x1,   y2-r,
        x1,   y1+r,
        x1,   y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)

def rounded_button(parent, text, command, w=56, h=44):
    """Custom rounded white button."""
    bg = "#FFFFFF"
    border = "#222222"
    fg = "#000000"

    c = tk.Canvas(parent, width=w, height=h, highlightthickness=0, bg=bg)
    draw_round_rect(c, 2, 2, w-2, h-2, r=14, fill=bg, outline=border, width=1)
    c.create_text(w//2, h//2, text=str(text), fill=fg, font=("Helvetica", 14, "bold"))

    def on_click(_evt=None):
        command()
    c.bind("<Button-1>", on_click)
    c.configure(cursor="hand2")
    return c

# ----------------- Main Scheduler -----------------
class LabelSchedulerApp:
    def __init__(self, root):
        self.root = root
        self.root.withdraw()
        ensure_labels_file()

        self._final_prompt_open = False  # guard so we don't open twice
        self.root.protocol("WM_DELETE_WINDOW", self.on_quit_request)

        # schedule first periodic popup
        self.root.after(1000, self.popup_now)

        # install signal handlers (SIGINT from Ctrl+C, and SIGTERM)
        self._install_signal_handlers()

    # ---- signals ----
    def _install_signal_handlers(self):
        def _signal_handler(signum, frame):
            # Schedule final prompt on the Tk main thread
            print("\n[label] Signal received → requesting final label…")
            try:
                self.root.after(0, self.on_quit_request)
            except Exception:
                # If root is already gone, just try to quit
                try:
                    self.root.quit()
                except Exception:
                    pass

        signal.signal(signal.SIGINT, _signal_handler)   # Ctrl+C
        signal.signal(signal.SIGTERM, _signal_handler)  # kill/terminate

    # ---- periodic popup ----
    def popup_now(self):
        """Create a small white popup with 1–5 buttons."""
        if self._final_prompt_open:  # don't show periodic popup during final prompt
            return

        win = tk.Toplevel(self.root)
        win.title("Fatigue")
        win.configure(bg="#FFFFFF")
        win.resizable(False, False)
        win.attributes("-topmost", True)

        # Size / center
        W, H = 350, 165
        win.update_idletasks()
        x = (win.winfo_screenwidth() - W) // 2
        y = (win.winfo_screenheight() - H) // 3
        win.geometry(f"{W}x{H}+{x}+{y}")

        tk.Label(
            win,
            text=f"How fatigued are you? (1–5)\n(last {LABEL_SPAN_MIN} min)",
            bg="#FFFFFF", fg="#000000", font=("Helvetica", 12)
        ).pack(pady=(16, 10))

        row = tk.Frame(win, bg="#FFFFFF"); row.pack(pady=6)

        def choose(v):
            t_to = int(time.time() * 1000)
            t_from = t_to - LABEL_SPAN_MIN * 60 * 1000
            _save_label_range(t_from, t_to, float(v))
            win.destroy()
            self.root.after(PROMPT_INTERVAL_MIN * 60 * 1000, self.popup_now)

        for i in range(1, 6):
            rounded_button(row, i, lambda v=i: choose(v), w=56, h=44).pack(side="left", padx=6)

        win.bind("<Escape>", lambda e: (win.destroy(),
                                        self.root.after(PROMPT_INTERVAL_MIN * 60 * 1000, self.popup_now)))
        win.grab_set(); win.focus_force()

    # ---- final prompt on quit or signal ----
    def on_quit_request(self):
        """Ask one final label for remaining time, then quit."""
        if self._final_prompt_open:
            return
        self._final_prompt_open = True

        t_now = int(time.time() * 1000)
        t_from = _last_label_end_ms()
        if t_from is None:
            t_from = t_now - LABEL_SPAN_MIN * 60 * 1000

        win = tk.Toplevel(self.root)
        win.title("Final fatigue")
        win.configure(bg="#FFFFFF")
        win.resizable(False, False)
        win.attributes("-topmost", True)

        W, H = 350, 165
        win.update_idletasks()
        x = (win.winfo_screenwidth() - W) // 2
        y = (win.winfo_screenheight() - H) // 3
        win.geometry(f"{W}x{H}+{x}+{y}")

        tk.Label(
            win,
            text="Before exit, rate your fatigue (1–5)\n(for remaining time)",
            bg="#FFFFFF", fg="#000000", font=("Helvetica", 12)
        ).pack(pady=(16, 10))

        row = tk.Frame(win, bg="#FFFFFF"); row.pack(pady=6)

        def choose_final(v):
            _save_label_range(t_from, t_now, float(v))
            win.destroy()
            try:
                self.root.quit()
            except Exception:
                pass

        for i in range(1, 6):
            rounded_button(row, i, lambda v=i: choose_final(v), w=56, h=44).pack(side="left", padx=6)

        win.bind("<Escape>", lambda e: (win.destroy(), self.root.quit()))
        win.grab_set(); win.focus_force()

# ----------------- Entrypoint -----------------
def main():
    root = tk.Tk()
    app = LabelSchedulerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()