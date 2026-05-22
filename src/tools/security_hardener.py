# Version: 1.1.0
# Version: 1.1.0
import os
import sys
import stat

def harden_project(root):
    findings = ["# IQ400 Security Hardening Report\n"]
    for dirpath, dirnames, filenames in os.walk(root):
        if ".git" in dirpath: continue

        for name in dirnames + filenames:
            path = os.path.join(dirpath, name)
            try:
                current_mode = os.stat(path).st_mode
                # Check for world-writable
                if current_mode & stat.S_IWOTH:
                    # Fix: remove world-writable
                    os.chmod(path, current_mode & ~stat.S_IWOTH)
                    findings.append(f"FIXED: Removed world-writable from {path}")
            except Exception as e:
                findings.append(f"ERROR: Could not process {path}: {e}")

    if len(findings) == 1:
        findings.append("No insecure permissions detected. System is HARDENED.")
    return "\n".join(findings)

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    print(harden_project(target))
