# src/collector/event_capture.py
# Demo-ready event logger with CONTENTLESS logging:
# - Captures keyboard & mouse events using pynput
# - Does NOT store printable keys (letters, digits, symbols)
# - Only keeps event type, timing, and limited metadata (Backspace flag, mouse coords)
# - Buffers in memory, flushes to NDJSON every 5s
# - Output file: data/raw/events_<ISO-like-timestamp>.ndjson

from pynput import keyboard, mouse
from collections import deque
from datetime import datetime, timezone
import threading, time, json, os, sys
from typing import Deque, Dict, Any

FLUSH_INTERVAL_SEC = 5
BUFFER_MAXLEN = 10000

def iso_stamp() -> str:
    # e.g., 2025-09-10T13-22-45
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%dT%H-%M-%S")

def now_ms() -> int:
    return int(time.time() * 1000)

def make_raw_path() -> str:
    fname = f"events_{iso_stamp()}.ndjson"
    path = os.path.join("data", "raw", fname)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path

class EventLogger:
    def __init__(self, out_path: str):
        self.out_path = out_path
        self.buf: Deque[Dict[str, Any]] = deque(maxlen=BUFFER_MAXLEN)
        self.lock = threading.Lock()
        self.stop_evt = threading.Event()
        self.writer_thread = threading.Thread(target=self._writer_loop, daemon=True)

    # -------- Event handlers --------
    def on_key_press(self, key):
        ev = {"t": now_ms(), "type": "key_down"}
        try:
            # special key (like backspace), record
            if isinstance(key, keyboard.Key):
                if key == keyboard.Key.backspace:
                    ev["is_backspace"] = True
                else:
                    ev["special"] = str(key)  #e.g,'Key.enter', 'Key.tab'
            else:
                # Printable characters recorded but without their data(for privacy)
                pass
        except Exception:
            pass
        self._append(ev)

    def on_click(self, x, y, button, pressed):
        if not pressed:
            return
        self._append({
            "t": now_ms(),
            "type": "mouse_click",
            "btn": str(button),
            "x": x, "y": y
        })

    def on_move(self, x, y):
        self._append({"t": now_ms(), "type": "mouse_move", "x": x, "y": y})

    def on_scroll(self, x, y, dx, dy):
        self._append({
            "t": now_ms(),
            "type": "mouse_scroll",
            "dx": dx, "dy": dy,
            "x": x, "y": y
        })

    # -------- Internals --------
    def _append(self, ev: Dict[str, Any]):
        with self.lock:
            self.buf.append(ev)

    def _writer_loop(self):
        while not self.stop_evt.is_set():
            time.sleep(FLUSH_INTERVAL_SEC)
            self.flush()

    def flush(self):
        with self.lock:
            if not self.buf:
                return
            batch = list(self.buf)
            self.buf.clear()

        with open(self.out_path, "a", encoding="utf-8") as f:
            for ev in batch:
                f.write(json.dumps(ev, ensure_ascii=False) + "\n")

    # -------- Lifecycle --------
    def run(self):
        print(f"[logger] Writing NDJSON to: {self.out_path}")
        print("[logger] Press Ctrl+C to stop.")
        self.writer_thread.start()

        with keyboard.Listener(on_press=self.on_key_press) as kl, \
             mouse.Listener(on_click=self.on_click, on_move=self.on_move, on_scroll=self.on_scroll) as ml:
            try:
                kl.join(); ml.join()
            except KeyboardInterrupt:
                pass
            finally:
                self.stop()

    def stop(self):
        self.stop_evt.set()
        self.flush()
        print("[logger] Stopped and flushed remaining events.")

def main():
    try:
        out_path = make_raw_path()
        EventLogger(out_path).run()
    except Exception as e:
        print(f"[logger] ERROR: {e}", file=sys.stderr)
        if sys.platform == "darwin":
            print("[logger] On macOS, grant Accessibility permissions to your terminal/IDE (System Settings → Privacy & Security → Accessibility).", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()