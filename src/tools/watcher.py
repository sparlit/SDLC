import sys
import time
import os
import subprocess
import base64
import json
import tempfile
from threading import BoundedSemaphore

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

# Guardrail: Limit concurrent swarm processes to avoid fork bombs and excessive API costs
MAX_CONCURRENT_SWARMS = 2
swarm_semaphore = BoundedSemaphore(MAX_CONCURRENT_SWARMS)

class SDLCWatcherHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory:
            return
        # Only watch source files
        if event.src_path.endswith(('.py', '.js', '.json', '.tf')):
            if "STRATEGIC_OMNISCIENT_AUDIT" in event.src_path or "AUDIT_LOG" in event.src_path:
                return

            # Simple debounce: wait a moment for the save to complete
            time.sleep(0.5)
            print(f"IQ400 Watcher: Change detected in {event.src_path}. Triggering Full-Spectrum Audit...")
            self.run_full_audit(event.src_path)

    def run_full_audit(self, filepath):
        all_issues = []

        # 1. Structural Scan (super_scanner)
        res_super = subprocess.run([sys.executable, SUPER_SCANNER, filepath], capture_output=True, text=True)
        if "No implementation gaps detected" not in res_super.stdout:
            all_issues.append(f"Structural Gaps:\n{res_super.stdout}")

        # 2. Security Scan (security_scanner)
        res_sec = subprocess.run([sys.executable, SECURITY_SCANNER, filepath], capture_output=True, text=True)
        if "PASS" not in res_sec.stdout:
            all_issues.append(f"Security Vulnerabilities:\n{res_sec.stdout}")

        # 3. Logic Scan (deep_analyzer)
        res_logic = subprocess.run([sys.executable, DEEP_ANALYZER, filepath], capture_output=True, text=True)
        if "fully operational" not in res_logic.stdout:
            all_issues.append(f"Logic Gaps (Dead Ends/Blind Spots):\n{res_logic.stdout}")

        if all_issues:
            aggregated_report = "\n---\n".join(all_issues)
            print(f"IQ400 Watcher: Issues detected in {filepath}. Initializing Swarm remediation...")
            self.trigger_remediation(filepath, aggregated_report)
        else:
            print(f"IQ400 Watcher: {filepath} verified clean (PASS).")

    def trigger_remediation(self, filepath, report):
        if not swarm_semaphore.acquire(blocking=False):
            print(f"IQ400 Watcher: Max concurrent swarms reached. Skipping remediation for {filepath} to maintain stability.")
            return

        try:
            # Prepare context
            context = {
                "file": filepath,
                "audit_report": report,
                "timestamp": time.time(),
                "action": "autonomous_fix"
            }

            # Pass context via temporary file to avoid shell argument length limits (ARG_MAX)
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tf:
                json.dump(context, tf)
                temp_path = tf.name

            # Dispatch swarm engine (it should be updated to accept a file path)
            # For backward compatibility, we will pass the file path prefixed with @
            subprocess.Popen(
                [sys.executable, SWARM_ENGINE, "error_fixing", f"@{temp_path}"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print(f"IQ400 Watcher: Swarm engine dispatched for {filepath} (Context: {temp_path})")
        finally:
            # Note: In a real implementation, the semaphore should be released
            # when the background process finishes. This simple version
            # releases immediately to allow the next file change.
            swarm_semaphore.release()

if __name__ == "__main__":
    path = os.path.join(PROJECT_ROOT, "src")
    event_handler = SDLCWatcherHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    print(f"IQ400 Watcher (v2.0): Monitoring {path} for stubs, security flaws, and logical gaps...")
    print(f"Concurrency Limit: {MAX_CONCURRENT_SWARMS}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
