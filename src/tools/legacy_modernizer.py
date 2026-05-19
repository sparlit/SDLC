import os
import sys

def detect_legacy_patterns(path):
    print(f"Scanning for legacy patterns in {path}...")
    # Example: scanning for old CommonJS 'require' in JS files
    patterns = {
        'require(': 'Legacy CommonJS detected. Recommend migrating to ESM imports.',
        'print ': 'Legacy Python 2 print statement detected. Recommend Python 3 migration.',
        'var ': 'Legacy JS var keyword. Recommend using let/const.'
    }

    findings = []
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            if f.endswith(('.js', '.py')):
                with open(os.path.join(dirpath, f), 'r') as file:
                    content = file.read()
                    for p, msg in patterns.items():
                        if p in content:
                            findings.append(f"{f}: {msg}")
    return findings

if __name__ == "__main__":
    findings = detect_legacy_patterns(sys.argv[1])
    if findings:
        for f in findings: print(f)
    else:
        print("Modern standards verified. No legacy patterns found.")
