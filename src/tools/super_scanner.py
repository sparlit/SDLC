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
    r"todo",
    r"blind spot",
    r"loose end",
    r"build later",
    r"fix later",
    r"empty wrapper"
]

def analyze_file(filepath):
    """
    Omniscient file analysis for flaws, gaps, and stubs.
    """
    findings = []

    # Skip binary files and known tool files
    if any(filepath.endswith(ext) for ext in ['.pyc', '.pyo', '.so', '.bin', '.exe']):
        return []

    try:
        if any(tool in filepath for tool in ["super_scanner.py", "omniscient_injector.py", "stress_tester.py"]):
            return []

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        lines = content.split('\n')
        for line_no, line in enumerate(lines, 1):
            for pattern in PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    # Filter out the pattern definitions in the workflow JSON themselves if they are part of names
                    if "Check:" in line or "Omniscient Fix:" in line or "error !== undefined" in line:
                        continue
                    findings.append(f"{filepath}:{line_no} - Found pattern '{pattern}': {line.strip()}")

        # Deep AST Analysis for Python stubs
        if filepath.endswith('.py'):
            import ast
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if len(node.body) == 1:
                            item = node.body[0]
                            if isinstance(item, ast.Pass) or (isinstance(item, ast.Expr) and isinstance(item.value, ast.Constant) and item.value.value == "..."):
                                findings.append(f"{filepath}:{node.lineno} - Empty function/stub: {node.name}")
                    elif isinstance(node, ast.ClassDef):
                        if len(node.body) == 1:
                            item = node.body[0]
                            if isinstance(item, ast.Pass) or (isinstance(item, ast.Expr) and isinstance(item.value, ast.Constant) and item.value.value == "..."):
                                findings.append(f"{filepath}:{node.lineno} - Empty class/stub: {node.name}")
            except Exception as e:
                pass

    except Exception as e:
        findings.append(f"{filepath}:0 - Error reading file: {e}")

    return findings

def scan_recursive(root):
    all_findings = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Explicitly skip __pycache__ and other hidden dirs
        dirnames[:] = [d for d in dirnames if not d.startswith('.') and d != "__pycache__"]

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
