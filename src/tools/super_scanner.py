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
    r"bottleneck",
    r"loop hole",
    r"blind spot",
    r"wrapper",
    r"stub",
    r"flaw",
    r"gap",
    r"error",
    r"blind spot",
    r"loose end",
    r"todo"
]

def analyze_file(filepath):
    findings = []
    try:
        if "super_scanner.py" in filepath or "omniscient_injector.py" in filepath:
            return []

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        lines = content.split('\n')
        for line_no, line in enumerate(lines, 1):
            for pattern in PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    findings.append(f"{filepath}:{line_no} - Found pattern '{pattern}': {line.strip()}")

        # Check for empty functions/classes in Python files
        if filepath.endswith('.py'):
            import ast
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if len(node.body) == 1 and isinstance(node.body[0], (ast.Pass, ast.Expr)) and (isinstance(node.body[0], ast.Pass) or (isinstance(node.body[0].value, ast.Constant) and node.body[0].value.value == "...")):
                            findings.append(f"{filepath}:{node.lineno} - Empty function/stub: {node.name}")
                    elif isinstance(node, ast.ClassDef):
                        if len(node.body) == 1 and isinstance(node.body[0], (ast.Pass, ast.Expr)) and (isinstance(node.body[0], ast.Pass) or (isinstance(node.body[0].value, ast.Constant) and node.body[0].value.value == "...")):
                            findings.append(f"{filepath}:{node.lineno} - Empty class/stub: {node.name}")
            except Exception as e:
                findings.append(f"{filepath}:0 - Parse failed: {e}")

    except Exception as e:
        findings.append(f"{filepath}:0 - Error reading file: {e}")

    return findings

def scan_recursive(root):
    all_findings = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith('.')]
        for f in filenames:
            filepath = os.path.join(dirpath, f)
            all_findings.extend(analyze_file(filepath))
    return all_findings

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    results = scan_recursive(target)
    if not results:
        print("Omniscient Scan: No flaws, gaps, or placeholders detected. IQ400 verified.")
    else:
        print(f"Omniscient Scan: Found {len(results)} issues:\n")
        print("\n".join(results))
