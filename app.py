"""
#app.py, Entry point that runs:
  1) Event logger (keyboard + mouse) in a background thread
  2) Label popup scheduler (Tkinter) on the main thread
"""
import threading
import signal
import sys

from src.collector.eventcapture import EventLogger, make_raw_path
from src.labeling.gui_scheduler import main as labels_main  # runs Tk mainloop

_logger_instance = None 

def start_logger_bg() -> EventLogger:
    """Start EventLogger in a background thread and return the instance."""
    out_path = make_raw_path()
    logger = EventLogger(out_path)

    t = threading.Thread(target=logger.run, daemon=True)
    t.start()
    print(f"[app] Event logger started (background) → {out_path}")
    return logger

def _graceful_exit(signum=None, frame=None):
    """Handle Ctrl+C / SIGTERM and stop the logger cleanly."""
    global _logger_instance
    print("\n[app] Shutting down…")
    if _logger_instance is not None:
        try:
            _logger_instance.stop()
        except Exception as e:
            print(f"[app] Logger stop error: {e}", file=sys.stderr)
    sys.exit(0)

def main():
    global _logger_instance
    # Trap signals for clean shutdown
    signal.signal(signal.SIGINT, _graceful_exit)
    signal.signal(signal.SIGTERM, _graceful_exit)

    # 1) Start event logger in background
    _logger_instance = start_logger_bg()
    # 2) Run label scheduler UI on main thread (Tkinter mainloop)
    #    This call blocks until the UI quits; logger keeps running in background.
    try:
        labels_main()
    finally:
        _graceful_exit()
if __name__ == "__main__":
    main()