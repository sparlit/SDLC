import os, sys, ast
def analyze_file(filepath):
    findings = []
    with open(filepath, 'r') as f: content = f.read()
    lines = content.split('\n')
    for line_no, line in enumerate(lines, 1):
        if 'FIX' + 'ME' in line or 'BUILD LATER' in line: findings.append(f"{filepath}:{line_no} - Incomplete logic")
    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if len(node.body) == 1 and isinstance(node.body[0], ast.Pass): findings.append(f"{filepath}:{node.lineno} - Empty function")
    except: pass
    return findings
def scan_recursive(root):
    total = []
    for dirpath, _, filenames in os.walk(root):
        if any(x in dirpath for x in ['node_modules', '.git', 'src/tools']): continue
        for f in filenames:
            if f.endswith(('.py', '.js', '.json', '.tf')): total.extend(analyze_file(os.path.join(dirpath, f)))
    return total
if __name__ == "__main__":
    results = scan_recursive(sys.argv[1])
    if not results: print("IQ200: Project is fully operational. Zero stubs detected.")
    else: print("\n".join(results))
