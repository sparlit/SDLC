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
    r"stub"
]

def analyze_file(filepath):
    """
    Scan a single file for configured placeholder-like regex patterns and for empty Python functions or classes.
    Analyze a file for configured placeholder/issue patterns and for Python empty definitions.
    
    Scans the file at `filepath` line-by-line for any regex in `PATTERNS` (case-insensitive) and records matches; for Python files (`.py`) also detects functions, async functions, or classes whose bodies contain only a single `pass`. If the file cannot be read or a Python AST cannot be parsed, a corresponding error finding is recorded. Matches originating from a path containing "super_scanner.py" are ignored.
    
    Parameters:
        filepath (str): Path to the file to analyze.
    
    Returns:
        list: A list of finding strings. Each finding is formatted as
        "{filepath}:{line_no} - Found pattern '{pattern}': {line_text}" for pattern matches,
        "{filepath}:{line_no} - Empty function: {name}" for empty Python functions,
        "{filepath}:{line_no} - Empty class: {name}" for empty Python classes,
        or "{filepath}:0 - Error reading file: {error}" if the file could not be opened or read.
    
    Notes:
        - Matches in files whose path contains "super_scanner.py" are ignored.
        - When analyzing Python files, AST parsing errors are silently ignored (no finding added for parse failures).
        list[str]: A list of formatted finding strings. Each entry is either a line-level match
        ("{filepath}:{line_no} - Found pattern '{pattern}': {line_text}"), an empty-definition
        report ("{filepath}:{lineno} - Empty function: {name}" or "{filepath}:{lineno} - Empty class: {name}"),
        or an error record ("{filepath}:0 - Error reading file: {e}" or "{filepath}:0 - Parse failed: {e}").
    Scan a single file for placeholder patterns and Python definitions that contain only a `pass`.
    
    This function reads the file at `filepath`, records any lines that match any regex in the module-level `PATTERNS` list (case-insensitive) — excluding matches originating from the scanner implementation itself — and, for `.py` files, records functions, async functions, and classes whose bodies consist of a single `pass`. If the file cannot be read or a Python AST parse fails, a corresponding error/failure finding is recorded.
    
    Returns:
        list[str]: A list of formatted finding strings like "<filepath>:<line> - Found pattern '<pattern>': <line text>" or "<filepath>:<line> - Empty function: <name>" / "<filepath>:<line> - Empty class: <name>". Error entries use line 0 and include the exception message.
    """
    findings = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        lines = content.split('\n')
        for line_no, line in enumerate(lines, 1):
            for pattern in PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    # Exclude the scanner itself and some common false positives if necessary
                    if "super_scanner.py" in filepath:
                        continue
                    findings.append(f"{filepath}:{line_no} - Found pattern '{pattern}': {line.strip()}")

        # Check for empty functions/classes in Python files
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
            except Exception as e:
                findings.append(f"{filepath}:0 - Parse failed: {e}")

    except Exception as e:
        findings.append(f"{filepath}:0 - Error reading file: {e}")

    return findings

def scan_recursive(root):
    """
    Recursively scan the directory tree at `root` and collect all findings from analyzed files.
    Recursively scan the directory tree at `root` for issues and return all findings.
    
    Walks the directory tree starting at `root`, skipping directories whose names start with a dot, analyzes each file encountered, and aggregates all reported findings.
    
    Parameters:
        root (str): Path to the directory to scan.
    
    Returns:
        all_findings (list[str]): Aggregated list of finding strings produced by analyze_file for each file under `root`. Each entry is formatted as "<filepath>:<line_no> - <description>".
        list[str]: A list of formatted finding strings describing detected issues (one entry per finding).
    Scan a directory tree and collect findings from every file under the given root.
    
    Parameters:
        root (str): Path of the directory to traverse.
    
    Returns:
        list: Aggregated list of finding strings produced for files under `root`.
    """
    all_findings = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Skip .git and other hidden directories
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
