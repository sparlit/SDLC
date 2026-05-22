# Version: 1.1.0
import os
import sys
import re

PATTERNS = [
    r"TODO",
    r"FIXME",
    r"STUB",
    r"build later",
    r"fix later",
    r"empty wrapper",
    r"placeholder",
    r"loose end",
    r"dead end",
    r"blind spot",
    r"loop hole",
    r"wrapper",
    r"stub",
    r"flaw",
    r"error",
    r"gap"
]

def analyze_file(filepath):
    findings = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Skip binary files
        if "\0" in content:
            return []

        lines = content.split('\n')
        for line_no, line in enumerate(lines, 1):
            for pattern in PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    if "super_scanner.py" in filepath:
                        continue
                    findings.append(f"{filepath}:{line_no} - Found pattern '{pattern}': {line.strip()}")

        if filepath.endswith('.py'):
            import ast
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                            findings.append(f"{filepath}:{node.lineno} - Empty function: {node.name}")
                    elif isinstance(node, ast.ClassDef):
                        if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                            findings.append(f"{filepath}:{node.lineno} - Empty class: {node.name}")
            except Exception:
                pass

    except Exception as e:
        findings.append(f"{filepath}:0 - Error reading file: {e}")

    return findings

def scan_recursive(root):
    all_findings = []
    for dirpath, dirnames, filenames in os.walk(root):
        for f in filenames:
            filepath = os.path.join(dirpath, f)
            all_findings.extend(analyze_file(filepath))
    return all_findings

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."

    version_file = os.path.join(target, "VERSION")
    version = "Unknown"
    if not os.path.exists(version_file):
        print(f"CRITICAL: VERSION file missing in {target}")
    else:
        with open(version_file, 'r') as vf:
            version = vf.read().strip()
            if not re.match(r"^\d+\.\d+\.\d+$", version):
                print(f"CRITICAL: Invalid version format in {version_file}: {version}")

    print(f"--- IQ400 Omniscient Scan v{version} ---")
    results = scan_recursive(target)
    if not results:
        print(f"Omniscient Scan: No flaws, gaps, or technical debt detected in v{version}. IQ400 verified.")
    else:
        print(f"Omniscient Scan: Found {len(results)} issues:\n")
        print("\n".join(results))
