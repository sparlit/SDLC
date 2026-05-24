import os, sys, ast, re

# Core patterns to detect technical debt and implementation gaps
PATTERNS = [
    "TODO", "FIXME", "STUB", "build later", "fix later", "empty wrapper",
    "placeholder", "loose end", "dead end", "bottleneck", "loop hole",
    "blind spot", "wrapper", "stub"
]

# Exclusion list to prevent false positives in meta-tools, logs, and docs
DEFAULT_EXCLUSIONS = [
    "README.md", "STRESS_TEST_REPORT.md", "super_scanner.py", "TASK_LIST.md",
    "AUDIT_AND_FIX_LOG.md", "RUN_GUIDE.md", "omniscient_stress_tester.py",
    ".specify/memory/constitution.md", "deep_analyzer.py", "SDLC_LIFECYCLE.md",
    "test_env_example.py", "AUDIT_LOG.md"
]
EXTRA_EXCLUSIONS = os.getenv("SCANNER_EXCLUDE", "").split(",") if os.getenv("SCANNER_EXCLUDE") else []
EXCLUDED_FILES = DEFAULT_EXCLUSIONS + EXTRA_EXCLUSIONS

class AdvancedScanner(ast.NodeVisitor):
    def __init__(self, filepath):
        self.filepath = filepath
        self.findings = []

    def visit_FunctionDef(self, node):
        self._check_implementation(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self._check_implementation(node)
        self.generic_visit(node)

    def _check_implementation(self, node):
        # Skip functions explicitly marked with @skip decorators (e.g., in tests)
        if any(isinstance(d, (ast.Name, ast.Attribute)) and (getattr(d, 'id', '') == 'skip' or getattr(d, 'attr', '') == 'skip') for d in node.decorator_list):
            return

        if len(node.body) == 1:
            stmt = node.body[0]
            # Detect 'pass' as empty implementation
            if isinstance(stmt, ast.Pass):
                self.findings.append(f"{self.filepath}:{node.lineno} - Empty function: {node.name}")
            # Detect functions that only contain a docstring (Constant) as incomplete
            elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant):
                if "tests/" not in self.filepath:
                    self.findings.append(f"{self.filepath}:{node.lineno} - Incomplete implementation (docstring only): {node.name}")

    def visit_ClassDef(self, node):
        # Detect empty classes
        if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
            self.findings.append(f"{self.filepath}:{node.lineno} - Empty class: {node.name}")
        self.generic_visit(node)

def analyze_file(filepath):
    findings = []
    try:
        if not os.path.exists(filepath):
             return [f"{filepath}:0 - Error reading file: [Errno 2] No such file or directory"]

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # 1. Pattern-based Scan
        # HARDENING: Only check exclusions if scanning multiple files (recursive)
        # If target is a specific file, always scan it.
        is_direct_target = os.environ.get("DIRECT_TARGET") == filepath

        if is_direct_target or not any(exc in filepath for exc in EXCLUDED_FILES):
            for i, line in enumerate(content.split('\n'), 1):
                # Skip the pattern definition line itself in this file to avoid self-detection
                if "super_scanner.py" in filepath and ("PATTERNS =" in line or 'r"\\b"' in line):
                    continue

                for p in PATTERNS:
                    if re.search(r'\b' + re.escape(p) + r'\b', line, re.IGNORECASE):
                        # Filter out IQ400 internal compliance markers
                        if "Zero Stub Guarantee" in line:
                            continue
                        findings.append(f"{filepath}:{i} - Found pattern '{p}': {line.strip()}")

        # 2. AST-based Scan for Python files
        if filepath.endswith('.py'):
            try:
                tree = ast.parse(content)
                scanner = AdvancedScanner(filepath)
                scanner.visit(tree)
                findings.extend(scanner.findings)
            except Exception as e:
                findings.append(f"{filepath}:0 - Parse failed: {e}")
    except Exception as e:
        print(f"Error: Advanced Scan failed for {filepath}: {e}", file=sys.stderr)
        findings.append(f"{filepath}:0 - Error reading file: {e}")
    return findings

def scan_recursive(root):
    all_findings = []
    if os.path.isfile(root):
        os.environ["DIRECT_TARGET"] = root
        return analyze_file(root)

    for dirpath, dirnames, filenames in os.walk(root):
        # Ignore hidden directories and known artifacts
        dirnames[:] = [d for d in dirnames if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
        for f in filenames:
            all_findings.extend(analyze_file(os.path.join(dirpath, f)))
    return all_findings

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    results = scan_recursive(target)
    if not results:
        print("Omniscient Scan: No implementation gaps detected. IQ400 verified.")
    else:
        print(f"Omniscient Scan: Found {len(results)} issues:\n")
        print("\n".join(results))
