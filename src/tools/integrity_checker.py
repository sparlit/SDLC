# Version: 1.1.0
import json
import os
import sys

def check_integrity(root):
    faults = []
    for dirpath, _, filenames in os.walk(root):
        for f in filenames:
            if f.endswith('.json'):
                path = os.path.join(dirpath, f)
                try:
                    with open(path, 'r') as jf:
                        json.load(jf)
                except Exception as e:
                    faults.append(f"INTEGRITY FAULT: {path} is invalid JSON: {e}")

    if not faults:
        return "IQ400 Integrity Verified: All JSON structures are valid."
    return "\n".join(faults)

if __name__ == "__main__":
    print(check_integrity(sys.argv[1] if len(sys.argv) > 1 else "."))
