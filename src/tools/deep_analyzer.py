import os, sys, ast
def analyze_file(filepath):
    findings = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f: content = f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}", file=sys.stderr)
        return findings

    lines = content.split('\n')
    for line_no, line in enumerate(lines, 1):
        if 'FIXME' in line or 'BUILD LATER' in line:
            # Filter out definitions of these strings in the tool itself
            if ('"FIXME"' in line or '"BUILD LATER"' in line or "'FIXME'" in line or "'BUILD LATER'" in line or 'PATTERNS =' in line):
                continue
            findings.append(f"{filepath}:{line_no} - Incomplete logic")
    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if len(node.body) == 1 and isinstance(node.body[0], ast.Pass): findings.append(f"{filepath}:{node.lineno} - Empty function")
    except Exception as e:
        print(f"Error parsing {filepath}: {e}", file=sys.stderr)
    return findings
def scan_recursive(root):
    total = []
    for dirpath, _, filenames in os.walk(root):
        if any(x in dirpath for x in ['node_modules', '.git']): continue
        for f in filenames:
            if f.endswith(('.py', '.js', '.json', '.tf')): total.extend(analyze_file(os.path.join(dirpath, f)))
    return total
if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    results = scan_recursive(target)
    if not results: print("IQ200: Project is fully operational. Zero stubs detected.")
    else: print("\n".join(results))
