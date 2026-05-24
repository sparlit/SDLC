import sys
import time
import os
import subprocess
import json
import tempfile
from threading import Thread, BoundedSemaphore

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("CRITICAL: 'watchdog' library not found. IQ400 Watcher cannot start.", file=sys.stderr)
    print("Please install it using: pip install watchdog", file=sys.stderr)
    sys.exit(1)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
SUPER_SCANNER = os.path.join(PROJECT_ROOT, "src/tools/super_scanner.py")
SECURITY_SCANNER = os.path.join(PROJECT_ROOT, "src/tools/security_scanner.py")
DEEP_ANALYZER = os.path.join(PROJECT_ROOT, "src/tools/deep_analyzer.py")
SWARM_ENGINE = os.path.join(PROJECT_ROOT, "src/tools/swarm_engine.py")

# Guardrail: Limit concurrent swarm processes
MAX_CONCURRENT_SWARMS = 2
swarm_semaphore = BoundedSemaphore(MAX_CONCURRENT_SWARMS)

def run_background_swarm(filepath, report, temp_path):
    """Execution wrapper to ensure semaphore release after process completion."""
    try:
        print(f"IQ400 Watcher: Initializing Swarm remediation for {filepath}...")
        # Synchronous wait for the background process
        process = subprocess.run(
            [sys.executable, SWARM_ENGINE, "error_fixing", f"@{temp_path}"],
            capture_output=True,
            text=True
        )
        if process.returncode == 0:
            print(f"IQ400 Watcher: Swarm remediation SUCCESS for {filepath}")
        else:
            print(f"IQ400 Watcher: Swarm remediation FAILED for {filepath}: {process.stderr}", file=sys.stderr)
    except Exception as e:
        print(f"IQ400 Watcher: Critical failure in background swarm: {e}", file=sys.stderr)
    finally:
        # Release resource
        swarm_semaphore.release()
        # Clean up context file
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass

class SDLCWatcherHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith(('.py', '.js', '.json', '.tf')):
            # Ignore audit reports and design docs to prevent loops
            if any(x in event.src_path for x in ["STRATEGIC", "AUDIT", "REPORT", "BLUEPRINT", "PLAN", "DESIGN"]):
                return

            time.sleep(1.0) # Debounce
            self.run_full_audit(event.src_path)

    def run_full_audit(self, filepath):
        all_issues = []

        # 1. Structural Scan
        res_super = subprocess.run([sys.executable, SUPER_SCANNER, filepath], capture_output=True, text=True)
        if "No implementation gaps detected" not in res_super.stdout:
            all_issues.append(f"Structural Gaps:\n{res_super.stdout}")

        # 2. Security Scan
        res_sec = subprocess.run([sys.executable, SECURITY_SCANNER, filepath], capture_output=True, text=True)
        if "PASS" not in res_sec.stdout:
            all_issues.append(f"Security Vulnerabilities:\n{res_sec.stdout}")

        # 3. Logic Scan
        res_logic = subprocess.run([sys.executable, DEEP_ANALYZER, filepath], capture_output=True, text=True)
        if "fully operational" not in res_logic.stdout:
            all_issues.append(f"Logic Gaps:\n{res_logic.stdout}")

        if all_issues:
            self.trigger_remediation(filepath, "\n---\n".join(all_issues))
        else:
            print(f"IQ400 Watcher: {filepath} verified clean.")

    def trigger_remediation(self, filepath, report):
        if not swarm_semaphore.acquire(blocking=False):
            print(f"IQ400 Watcher: Max concurrent swarms reached. Skipping {filepath}.")
            return

        try:
            context = {
                "file": filepath,
                "audit_report": report,
                "timestamp": time.time(),
                "action": "autonomous_fix"
            }

            fd, temp_path = tempfile.mkstemp(suffix='.json', prefix='swarm_ctx_')
            with os.fdopen(fd, 'w') as f:
                json.dump(context, f)

            # Spawn a thread to manage the lifecycle of the swarm process
            Thread(target=run_background_swarm, args=(filepath, report, temp_path)).start()
            print(f"IQ400 Watcher: Swarm engine dispatched for {filepath} in background.")
        except Exception as e:
            print(f"IQ400 Watcher: Failed to trigger remediation: {e}", file=sys.stderr)
            swarm_semaphore.release()

if __name__ == "__main__":
    path = os.path.join(PROJECT_ROOT, "src")
    event_handler = SDLCWatcherHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    print(f"IQ400 Watcher (v3.0): Monitoring {path}...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
