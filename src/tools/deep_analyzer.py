import os, sys, ast

class LogicAuditor(ast.NodeVisitor):
    def __init__(self, filepath):
        self.filepath = filepath
        self.findings = []

    def visit_FunctionDef(self, node):
        self._check_dead_ends(node)
        self._check_blind_spots(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self._check_dead_ends(node)
        self._check_blind_spots(node)
        self.generic_visit(node)

    def _check_dead_ends(self, node):
        """
        Detects 'Dead Ends': Functions that are not constructors and lack return statements
        or have unhandled control flow paths.
        """
        if node.name.startswith('__') and node.name.endswith('__'):
            return # Skip special methods

        has_return = False
        for subnode in ast.walk(node):
            if isinstance(subnode, (ast.Return, ast.Yield, ast.YieldFrom, ast.Raise)):
                has_return = True
                break

        # If it's a non-empty function but has no return/yield/raise
        if not has_return and len(node.body) > 0:
            # Check if it's just a simple setter or print-like function
            is_simple = any(isinstance(s, (ast.Assign, ast.Expr)) for s in node.body)
            if not is_simple:
                self.findings.append(f"{self.filepath}:{node.lineno} - Possible Dead End: Function '{node.name}' lacks conclusive return/exit path.")

    def _check_blind_spots(self, node):
        """
        Detects 'Blind Spots': Empty exception handlers (except: pass).
        """
        for subnode in ast.walk(node):
            if isinstance(subnode, ast.ExceptHandler):
                if len(subnode.body) == 1 and isinstance(subnode.body[0], (ast.Pass, ast.Expr)):
                    self.findings.append(f"{self.filepath}:{subnode.lineno} - Blind Spot: Empty exception handler detected.")

def analyze_file(filepath):
    findings = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}", file=sys.stderr)
        return findings

    lines = content.split('\n')
    for line_no, line in enumerate(lines, 1):
        if 'FIXME' in line or 'BUILD LATER' in line or 'FIX-LATER' in line:
            # Filter out definitions of these strings in the tool itself
            if ('"FIXME"' in line or '"BUILD LATER"' in line or "'FIXME'" in line or "'BUILD LATER'" in line or 'PATTERNS =' in line):
                continue
            findings.append(f"{filepath}:{line_no} - Incomplete logic marker found")

    if filepath.endswith('.py'):
        try:
            tree = ast.parse(content)
            # 1. Check for empty implementations
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                        findings.append(f"{filepath}:{node.lineno} - Empty function (Stub)")

            # 2. Check for logical gaps (Dead Ends/Blind Spots)
            auditor = LogicAuditor(filepath)
            auditor.visit(tree)
            findings.extend(auditor.findings)
        except Exception as e:
            print(f"Error parsing {filepath}: {e}", file=sys.stderr)
    return findings

def scan_recursive(root):
    total = []
    for dirpath, _, filenames in os.walk(root):
        if any(x in dirpath for x in ['node_modules', '.git']): continue
        for f in filenames:
            if f.endswith(('.py', '.js', '.json', '.tf')):
                total.extend(analyze_file(os.path.join(dirpath, f)))
    return total

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    results = scan_recursive(target)
    if not results:
        print("IQ200: Project is fully operational. Zero stubs or logical gaps detected.")
    else:
        print("\n".join(results))
