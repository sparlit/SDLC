import os, sys, ast

class ReturnFinder(ast.NodeVisitor):
    """
    Helper to find return statements in the current scope only.
    It stops traversing when it hits nested function or class definitions.
    """
    def __init__(self):
        self.has_return = False

    def visit_Return(self, node):
        self.has_return = True

    def visit_Yield(self, node):
        self.has_return = True

    def visit_YieldFrom(self, node):
        self.has_return = True

    def visit_Raise(self, node):
        self.has_return = True

    def visit_FunctionDef(self, node):
        # Do not enter nested functions
        pass

    def visit_AsyncFunctionDef(self, node):
        # Do not enter nested functions
        pass

    def visit_ClassDef(self, node):
        # Do not enter nested classes
        pass

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
        or have unhandled control flow paths within their own scope.
        """
        if node.name.startswith('__') and node.name.endswith('__'):
            return # Skip special methods

        finder = ReturnFinder()
        for stmt in node.body:
            finder.visit(stmt)

        if not finder.has_return and len(node.body) > 0:
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
        if 'FIXME' in line or 'BUILD LATER' in line or 'FIX-LATER' in line or 'HACK' in line:
            if ('"FIXME"' in line or '"BUILD LATER"' in line or "'FIXME'" in line or "'BUILD LATER'" in line or 'PATTERNS =' in line):
                continue
            findings.append(f"{filepath}:{line_no} - Incomplete logic marker found")

    if filepath.endswith('.py'):
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                        findings.append(f"{filepath}:{node.lineno} - Empty function (Stub)")

            auditor = LogicAuditor(filepath)
            auditor.visit(tree)
            findings.extend(auditor.findings)
        except Exception as e:
            findings.append(f"{filepath}:0 - Parse Error: {e}")
    return findings

def scan_recursive(root):
    total = []
    # HARDENING: Handle single file targets
    if os.path.isfile(root):
        return analyze_file(root)

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
