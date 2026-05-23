import sys
import time
import os
import subprocess
import base64
import json

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("CRITICAL: 'watchdog' library not found. IQ400 Watcher cannot start.", file=sys.stderr)
    print("Please install it using: pip install watchdog", file=sys.stderr)
    sys.exit(1)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
SCANNER_PATH = os.path.join(PROJECT_ROOT, "src/tools/super_scanner.py")
SWARM_ENGINE_PATH = os.path.join(PROJECT_ROOT, "src/tools/swarm_engine.py")

class SDLCWatcherHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith(('.py', '.js', '.json', '.tf')):
            print(f"IQ400 Watcher: Change detected in {event.src_path}. Triggering audit...")
            self.run_audit(event.src_path)

    def run_audit(self, filepath):
        # 1. Run scanner to find gaps
        result = subprocess.run(
            [sys.executable, SCANNER_PATH, filepath],
            capture_output=True,
            text=True
        )

        if "No implementation gaps detected" not in result.stdout:
            print(f"IQ400 Watcher: Gaps found in {filepath}. Initializing Swarm remediation...")
            self.trigger_remediation(filepath, result.stdout)
        else:
            print(f"IQ400 Watcher: {filepath} verified clean.")

    def trigger_remediation(self, filepath, gaps):
        # Prepare context for the swarm engine
        context = {
            "file": filepath,
            "issues": gaps,
            "timestamp": time.time(),
            "action": "autonomous_fix"
        }
        # Base64 encode context to pass to swarm_engine.py safely
        context_b64 = base64.b64encode(json.dumps(context).encode('utf-8')).decode('utf-8')

        # Invoke swarm engine
        # In a real environment, this might also trigger an n8n webhook
        subprocess.Popen(
            [sys.executable, SWARM_ENGINE_PATH, "error_fixing", context_b64],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print(f"IQ400 Watcher: Swarm engine dispatched for {filepath}")

if __name__ == "__main__":
    path = os.path.join(PROJECT_ROOT, "src")
    event_handler = SDLCWatcherHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    print(f"IQ400 Watcher: Monitoring {path} for stubs and errors...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
