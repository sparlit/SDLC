"""
Tests for src/tools/super_scanner.py

This module was added in this PR as the gap-detection component for the
autonomous fixing workflow. It replaces the deleted deep_analyzer.py tool.

Tests cover:
 - PATTERNS list contents and completeness
 - analyze_file(): pattern detection (case-insensitive), line numbers, filepath
 - analyze_file(): self-exclusion (skips files named super_scanner.py)
 - analyze_file(): empty Python function/class detection via AST
 - analyze_file(): error handling for unreadable files and unparseable Python
 - scan_recursive(): directory traversal, hidden-directory skipping
"""

import ast
import os
import sys
import tempfile
import textwrap

import pytest

# ---------------------------------------------------------------------------
# Import the module under test
# ---------------------------------------------------------------------------

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "tools"))
import super_scanner
from super_scanner import PATTERNS, analyze_file, scan_recursive


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_temp_file(content, suffix=".py", dir=None):
    """Create a NamedTemporaryFile, write content, and return the path.
    Caller is responsible for deletion."""
    fd, path = tempfile.mkstemp(suffix=suffix, dir=dir)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(textwrap.dedent(content))
    return path


# ---------------------------------------------------------------------------
# PATTERNS list
# ---------------------------------------------------------------------------

class TestPatternsList:
    def test_patterns_is_a_list(self):
        assert isinstance(PATTERNS, list)

    def test_patterns_is_not_empty(self):
        assert len(PATTERNS) > 0

    @pytest.mark.parametrize("expected", [
        r"TODO",
        r"FIXME",
        r"STUB",
        r"placeholder",
        r"stub",
    ])
    def test_required_pattern_present(self, expected):
        assert expected in PATTERNS, (
            f"Expected pattern {expected!r} to be in PATTERNS"
        )

    def test_all_patterns_are_strings(self):
        for p in PATTERNS:
            assert isinstance(p, str), f"Pattern {p!r} is not a string"

    def test_no_empty_patterns(self):
        for p in PATTERNS:
            assert p.strip() != "", "Empty pattern found in PATTERNS"


# ---------------------------------------------------------------------------
# analyze_file(): clean files produce no findings
# ---------------------------------------------------------------------------

class TestAnalyzeFileCleanFile:
    def test_clean_python_file_has_no_findings(self):
        path = _write_temp_file("""\
            def add(a, b):
                return a + b

            class Calculator:
                def multiply(self, x, y):
                    return x * y
        """)
        try:
            result = analyze_file(path)
            assert result == [], f"Expected no findings, got: {result}"
        finally:
            os.unlink(path)

    def test_clean_text_file_has_no_findings(self):
        path = _write_temp_file("Hello world\nThis is a clean file.\n", suffix=".txt")
        try:
            result = analyze_file(path)
            assert result == []
        finally:
            os.unlink(path)

    def test_empty_file_has_no_findings(self):
        path = _write_temp_file("", suffix=".py")
        try:
            result = analyze_file(path)
            assert result == []
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# analyze_file(): pattern detection
# ---------------------------------------------------------------------------

class TestAnalyzeFilePatternDetection:
    @pytest.mark.parametrize("pattern_text", [
        "TODO",
        "FIXME",
        "STUB",
        "placeholder",
        "stub",
        "build later",
        "fix later",
        "wrapper",
        "bottleneck",
    ])
    def test_detects_pattern(self, pattern_text):
        content = f"# This is a {pattern_text} comment\nprint('hello')\n"
        path = _write_temp_file(content, suffix=".txt")
        try:
            findings = analyze_file(path)
            assert len(findings) >= 1, (
                f"Expected to find pattern '{pattern_text}' but got no findings"
            )
        finally:
            os.unlink(path)

    def test_detection_is_case_insensitive_uppercase(self):
        """Patterns must be matched regardless of case (re.IGNORECASE)."""
        path = _write_temp_file("# TODO: fix this\n", suffix=".txt")
        try:
            findings = analyze_file(path)
            assert len(findings) >= 1
        finally:
            os.unlink(path)

    def test_detection_is_case_insensitive_lowercase(self):
        path = _write_temp_file("# todo: also fix this\n", suffix=".txt")
        try:
            findings = analyze_file(path)
            assert len(findings) >= 1
        finally:
            os.unlink(path)

    def test_detection_is_case_insensitive_mixedcase(self):
        path = _write_temp_file("# Fixme: also fix this\n", suffix=".txt")
        try:
            findings = analyze_file(path)
            assert len(findings) >= 1
        finally:
            os.unlink(path)

    def test_finding_includes_filepath(self):
        path = _write_temp_file("# TODO: fix\n", suffix=".txt")
        try:
            findings = analyze_file(path)
            assert any(path in f for f in findings), (
                f"Expected filepath {path!r} in findings: {findings}"
            )
        finally:
            os.unlink(path)

    def test_finding_includes_line_number(self):
        content = "line one\nline two with TODO here\nline three\n"
        path = _write_temp_file(content, suffix=".txt")
        try:
            findings = analyze_file(path)
            assert len(findings) >= 1
            # Line 2 contains the TODO
            assert any(":2 " in f for f in findings), (
                f"Expected line 2 in findings: {findings}"
            )
        finally:
            os.unlink(path)

    def test_finding_includes_matched_pattern(self):
        path = _write_temp_file("# TODO: needs work\n", suffix=".txt")
        try:
            findings = analyze_file(path)
            assert any("TODO" in f for f in findings)
        finally:
            os.unlink(path)

    def test_finding_includes_line_content(self):
        path = _write_temp_file("x = 1  # FIXME urgent\n", suffix=".txt")
        try:
            findings = analyze_file(path)
            assert len(findings) >= 1
            assert any("FIXME urgent" in f for f in findings), (
                f"Expected line content in findings: {findings}"
            )
        finally:
            os.unlink(path)

    def test_multiple_patterns_on_same_line_create_multiple_findings(self):
        """A line matching two patterns should produce two findings."""
        path = _write_temp_file("# TODO FIXME placeholder\n", suffix=".txt")
        try:
            findings = analyze_file(path)
            assert len(findings) >= 2, (
                f"Expected at least 2 findings for multi-pattern line, got: {findings}"
            )
        finally:
            os.unlink(path)

    def test_multiple_lines_with_patterns(self):
        content = "# TODO first\n# FIXME second\nclean line\n"
        path = _write_temp_file(content, suffix=".txt")
        try:
            findings = analyze_file(path)
            assert len(findings) >= 2
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# analyze_file(): self-exclusion of super_scanner.py
# ---------------------------------------------------------------------------

class TestAnalyzeFileSelfExclusion:
    def test_skips_pattern_matches_in_super_scanner_file(self):
        """When the filepath contains 'super_scanner.py', pattern matches are skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "super_scanner.py")
            with open(path, "w") as f:
                f.write("# TODO: this is the scanner itself\n")
            findings = analyze_file(path)
            # Pattern matches should be skipped, but we may still see AST findings
            pattern_findings = [
                f for f in findings
                if "Found pattern" in f
            ]
            assert pattern_findings == [], (
                f"Expected no pattern findings for super_scanner.py, got: {pattern_findings}"
            )

    def test_non_scanner_files_are_not_excluded(self):
        """Other files named differently should not be excluded."""
        path = _write_temp_file("# TODO fix me\n", suffix=".py")
        try:
            findings = analyze_file(path)
            assert len(findings) >= 1
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# analyze_file(): empty function/class detection (Python AST)
# ---------------------------------------------------------------------------

class TestAnalyzeFileEmptyPythonStructures:
    def test_detects_empty_function(self):
        path = _write_temp_file("""\
            def empty_func():
                pass
        """, suffix=".py")
        try:
            findings = analyze_file(path)
            assert any("Empty function" in f and "empty_func" in f for f in findings), (
                f"Expected empty function finding, got: {findings}"
            )
        finally:
            os.unlink(path)

    def test_detects_empty_async_function(self):
        path = _write_temp_file("""\
            async def empty_async():
                pass
        """, suffix=".py")
        try:
            findings = analyze_file(path)
            assert any("Empty function" in f and "empty_async" in f for f in findings), (
                f"Expected empty async function finding, got: {findings}"
            )
        finally:
            os.unlink(path)

    def test_detects_empty_class(self):
        path = _write_temp_file("""\
            class EmptyClass:
                pass
        """, suffix=".py")
        try:
            findings = analyze_file(path)
            assert any("Empty class" in f and "EmptyClass" in f for f in findings), (
                f"Expected empty class finding, got: {findings}"
            )
        finally:
            os.unlink(path)

    def test_non_empty_function_not_flagged(self):
        path = _write_temp_file("""\
            def real_func():
                return 42
        """, suffix=".py")
        try:
            findings = analyze_file(path)
            empty_findings = [f for f in findings if "Empty function" in f]
            assert empty_findings == [], (
                f"Non-empty function should not be flagged: {empty_findings}"
            )
        finally:
            os.unlink(path)

    def test_function_with_docstring_only_not_flagged(self):
        """A function with only a docstring has a Expr node, not Pass, so it's not empty."""
        path = _write_temp_file("""\
            def documented_func():
                \"\"\"This function has a docstring.\"\"\"
        """, suffix=".py")
        try:
            findings = analyze_file(path)
            empty_findings = [f for f in findings if "Empty function" in f]
            assert empty_findings == [], (
                f"Function with docstring should not be flagged as empty: {empty_findings}"
            )
        finally:
            os.unlink(path)

    def test_empty_function_line_number_is_correct(self):
        path = _write_temp_file("""\
            def first():
                return 1

            def empty_fn():
                pass
        """, suffix=".py")
        try:
            findings = analyze_file(path)
            empty_findings = [f for f in findings if "Empty function" in f and "empty_fn" in f]
            assert len(empty_findings) == 1, f"Expected exactly one finding, got: {empty_findings}"
            # empty_fn starts at line 4 (after dedent/parse)
            assert ":4 " in empty_findings[0] or ":4-" in empty_findings[0] or empty_findings[0].split(":")[1].startswith("4"), (
                f"Expected line 4 for empty_fn, got: {empty_findings[0]}"
            )
        finally:
            os.unlink(path)

    def test_ast_check_only_applies_to_python_files(self):
        """Non-.py files should not trigger AST analysis."""
        path = _write_temp_file("""\
            def empty_func():
                pass
        """, suffix=".txt")
        try:
            findings = analyze_file(path)
            empty_findings = [f for f in findings if "Empty function" in f]
            assert empty_findings == [], (
                f".txt file should not get AST check: {empty_findings}"
            )
        finally:
            os.unlink(path)

    def test_invalid_python_syntax_reported_as_parse_failed(self):
        """If the Python file cannot be parsed, a 'Parse failed' finding is added."""
        path = _write_temp_file("def broken(\n", suffix=".py")
        try:
            findings = analyze_file(path)
            assert any("Parse failed" in f for f in findings), (
                f"Expected 'Parse failed' finding for invalid Python, got: {findings}"
            )
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# analyze_file(): error handling
# ---------------------------------------------------------------------------

class TestAnalyzeFileErrorHandling:
    def test_nonexistent_file_returns_error_finding(self):
        result = analyze_file("/nonexistent/path/to/file.py")
        assert len(result) == 1
        assert "Error reading file" in result[0]
        assert "/nonexistent/path/to/file.py" in result[0]

    def test_error_finding_has_zero_line_number(self):
        result = analyze_file("/no/such/file.txt")
        assert ":0 " in result[0]


# ---------------------------------------------------------------------------
# scan_recursive(): directory traversal
# ---------------------------------------------------------------------------

class TestScanRecursive:
    def test_returns_list(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = scan_recursive(tmpdir)
            assert isinstance(result, list)

    def test_empty_directory_has_no_findings(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = scan_recursive(tmpdir)
            assert result == []

    def test_detects_issues_in_single_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "code.py")
            with open(path, "w") as f:
                f.write("# TODO: fix this later\n")
            result = scan_recursive(tmpdir)
            assert len(result) >= 1

    def test_scans_subdirectories_recursively(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = os.path.join(tmpdir, "subdir")
            os.makedirs(subdir)
            path = os.path.join(subdir, "nested.txt")
            with open(path, "w") as f:
                f.write("# FIXME nested\n")
            result = scan_recursive(tmpdir)
            assert len(result) >= 1
            assert any("nested.txt" in f for f in result)

    def test_skips_hidden_directories(self):
        """Directories starting with '.' must be excluded from scanning."""
        with tempfile.TemporaryDirectory() as tmpdir:
            hidden = os.path.join(tmpdir, ".hidden")
            os.makedirs(hidden)
            path = os.path.join(hidden, "secret.py")
            with open(path, "w") as f:
                f.write("# TODO: hidden\n")
            result = scan_recursive(tmpdir)
            # The .hidden directory should be skipped
            assert not any(".hidden" in f for f in result), (
                f"Hidden directory was not skipped: {result}"
            )

    def test_does_not_skip_non_hidden_directories(self):
        """Only directories starting with '.' should be skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            visible = os.path.join(tmpdir, "visible_dir")
            os.makedirs(visible)
            path = os.path.join(visible, "code.txt")
            with open(path, "w") as f:
                f.write("# TODO: visible\n")
            result = scan_recursive(tmpdir)
            assert len(result) >= 1

    def test_scans_multiple_files_in_same_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            for name in ("a.txt", "b.txt"):
                with open(os.path.join(tmpdir, name), "w") as f:
                    f.write("# TODO: fix\n")
            result = scan_recursive(tmpdir)
            assert len(result) >= 2

    def test_clean_directory_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            for name in ("clean1.py", "clean2.txt"):
                with open(os.path.join(tmpdir, name), "w") as f:
                    f.write("x = 1\n")
            result = scan_recursive(tmpdir)
            assert result == []

    def test_findings_include_full_file_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "file_with_todo.txt")
            with open(path, "w") as f:
                f.write("# TODO: something\n")
            result = scan_recursive(tmpdir)
            assert any(path in f for f in result)

    def test_git_directory_is_skipped(self):
        """The .git directory (hidden) must be excluded from scanning."""
        with tempfile.TemporaryDirectory() as tmpdir:
            git_dir = os.path.join(tmpdir, ".git")
            os.makedirs(git_dir)
            path = os.path.join(git_dir, "config")
            with open(path, "w") as f:
                f.write("# TODO: git internal\n")
            result = scan_recursive(tmpdir)
            assert not any(".git" in f for f in result), (
                f".git directory was not skipped: {result}"
            )
