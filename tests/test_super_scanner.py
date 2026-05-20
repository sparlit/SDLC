"""
Tests for src/tools/super_scanner.py

The super_scanner module was added in this PR as the gap-detection component
for the autonomous fixing workflow.  It exposes two public functions:

  analyze_file(filepath)   — scans a single file for problematic patterns
                             and empty Python functions/classes.
  scan_recursive(root)     — walks a directory tree and calls analyze_file
                             on every non-hidden file.

These tests verify:
  - Pattern detection (all 14 registered patterns, case-insensitive)
  - The scanner skips its own source file to avoid self-reporting
  - Empty Python function and class detection via AST
  - Error handling for unreadable files and unparseable Python
  - scan_recursive directory traversal, including hidden-dir skipping
"""

import ast
import os
import sys
import tempfile

import pytest

# ---------------------------------------------------------------------------
# Import the module under test
# ---------------------------------------------------------------------------

TOOLS_DIR = os.path.join(os.path.dirname(__file__), "..", "src", "tools")
sys.path.insert(0, os.path.abspath(TOOLS_DIR))

import super_scanner  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_tmp(content: str, suffix: str = ".txt", dir=None) -> str:
    """Write *content* to a temp file and return its absolute path."""
    fd, path = tempfile.mkstemp(suffix=suffix, dir=dir)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(content)
    return path


# ---------------------------------------------------------------------------
# PATTERNS list
# ---------------------------------------------------------------------------

class TestPatternsList:
    """The PATTERNS list must contain every pattern the tool advertises."""

    EXPECTED_PATTERNS = [
        "TODO",
        "FIXME",
        "STUB",
        "build later",
        "fix later",
        "empty wrapper",
        "placeholder",
        "loose end",
        "dead end",
        "bottleneck",
        "loop hole",
        "blind spot",
        "wrapper",
        "stub",
    ]

    @pytest.mark.parametrize("pattern", EXPECTED_PATTERNS)
    def test_pattern_is_registered(self, pattern):
        assert pattern in super_scanner.PATTERNS, (
            f"Expected pattern {pattern!r} to be in PATTERNS"
        )

    def test_patterns_is_a_list(self):
        assert isinstance(super_scanner.PATTERNS, list)

    def test_patterns_is_non_empty(self):
        assert len(super_scanner.PATTERNS) > 0


# ---------------------------------------------------------------------------
# analyze_file — clean files
# ---------------------------------------------------------------------------

class TestAnalyzeFileClean:
    """Files with no problematic content should return no findings."""

    def test_clean_text_file_returns_empty_list(self, tmp_path):
        path = str(tmp_path / "clean.txt")
        with open(path, "w") as f:
            f.write("Hello world\nThis is a normal sentence.\n")
        assert super_scanner.analyze_file(path) == []

    def test_clean_python_file_returns_empty_list(self, tmp_path):
        path = str(tmp_path / "clean.py")
        with open(path, "w") as f:
            f.write("def add(a, b):\n    return a + b\n")
        assert super_scanner.analyze_file(path) == []

    def test_empty_file_returns_empty_list(self, tmp_path):
        path = str(tmp_path / "empty.txt")
        path_obj = tmp_path / "empty.txt"
        path_obj.write_text("")
        assert super_scanner.analyze_file(str(path_obj)) == []


# ---------------------------------------------------------------------------
# analyze_file — pattern detection
# ---------------------------------------------------------------------------

class TestAnalyzeFilePatternDetection:
    """Each registered pattern must be detected when present in a file."""

    @pytest.mark.parametrize("pattern", [
        "TODO",
        "FIXME",
        "STUB",
        "build later",
        "fix later",
        "empty wrapper",
        "placeholder",
        "loose end",
        "dead end",
        "bottleneck",
        "loop hole",
        "blind spot",
        "wrapper",
        "stub",
    ])
    def test_pattern_detected_in_file(self, tmp_path, pattern):
        path = str(tmp_path / "test_pattern.txt")
        with open(path, "w") as f:
            f.write(f"Some text with {pattern} here\n")
        findings = super_scanner.analyze_file(path)
        assert len(findings) > 0, f"Pattern {pattern!r} was not detected"

    def test_todo_detected_case_insensitive_lower(self, tmp_path):
        path = str(tmp_path / "lower_todo.txt")
        with open(path, "w") as f:
            f.write("# todo: fix this later\n")
        findings = super_scanner.analyze_file(path)
        assert len(findings) > 0

    def test_fixme_detected_case_insensitive_upper(self, tmp_path):
        path = str(tmp_path / "fixme.txt")
        with open(path, "w") as f:
            f.write("FIXME: this needs attention\n")
        findings = super_scanner.analyze_file(path)
        assert len(findings) > 0

    def test_placeholder_detected_case_insensitive_mixed(self, tmp_path):
        path = str(tmp_path / "mixed.txt")
        with open(path, "w") as f:
            f.write("Placeholder value here\n")
        findings = super_scanner.analyze_file(path)
        assert len(findings) > 0

    def test_finding_format_contains_filepath(self, tmp_path):
        path = str(tmp_path / "todo_file.txt")
        with open(path, "w") as f:
            f.write("# TODO: implement me\n")
        findings = super_scanner.analyze_file(path)
        assert any(path in finding for finding in findings)

    def test_finding_format_contains_line_number(self, tmp_path):
        path = str(tmp_path / "numbered.txt")
        with open(path, "w") as f:
            f.write("first line\n# TODO: implement\nthird line\n")
        findings = super_scanner.analyze_file(path)
        # Line 2 should be flagged
        assert any(":2 " in finding for finding in findings)

    def test_finding_format_contains_pattern_name(self, tmp_path):
        path = str(tmp_path / "pattern_name.txt")
        with open(path, "w") as f:
            f.write("# TODO implement this\n")
        findings = super_scanner.analyze_file(path)
        assert any("Found pattern 'TODO'" in finding for finding in findings)

    def test_finding_format_contains_line_content(self, tmp_path):
        path = str(tmp_path / "content.txt")
        with open(path, "w") as f:
            f.write("# TODO implement this\n")
        findings = super_scanner.analyze_file(path)
        assert any("implement this" in finding for finding in findings)

    def test_multiple_patterns_on_same_line_generates_multiple_findings(self, tmp_path):
        path = str(tmp_path / "multi.txt")
        with open(path, "w") as f:
            # 'wrapper' and 'TODO' both appear on the same line
            f.write("# TODO: empty wrapper here\n")
        findings = super_scanner.analyze_file(path)
        assert len(findings) >= 2, (
            "Multiple matching patterns on one line should produce multiple findings"
        )

    def test_multiple_matching_lines_all_reported(self, tmp_path):
        path = str(tmp_path / "multi_lines.txt")
        with open(path, "w") as f:
            f.write("# TODO first\n# TODO second\n")
        findings = super_scanner.analyze_file(path)
        assert len(findings) >= 2


# ---------------------------------------------------------------------------
# analyze_file — self-exclusion
# ---------------------------------------------------------------------------

class TestAnalyzeFileSelfExclusion:
    """The scanner must not report findings from its own source file."""

    def test_super_scanner_file_is_excluded(self):
        scanner_path = os.path.join(TOOLS_DIR, "super_scanner.py")
        findings = super_scanner.analyze_file(scanner_path)
        assert findings == [], (
            "super_scanner.py should exclude itself from scan results, "
            f"but returned: {findings}"
        )

    def test_filepath_containing_super_scanner_string_is_excluded(self, tmp_path):
        """Any filepath containing 'super_scanner.py' is excluded."""
        # Create a real file with a TODO in a directory named super_scanner.py
        d = tmp_path / "super_scanner.py"
        d.mkdir()
        path = str(d / "some_file.txt")
        with open(path, "w") as f:
            f.write("# TODO: this should be excluded\n")
        findings = super_scanner.analyze_file(path)
        assert findings == []


# ---------------------------------------------------------------------------
# analyze_file — empty Python constructs
# ---------------------------------------------------------------------------

class TestAnalyzeFileEmptyPythonConstructs:
    """Empty functions and classes (body = pass) must be flagged."""

    def test_empty_function_detected(self, tmp_path):
        path = str(tmp_path / "empty_func.py")
        with open(path, "w") as f:
            f.write("def my_func():\n    pass\n")
        findings = super_scanner.analyze_file(path)
        assert any("Empty function: my_func" in f for f in findings), (
            f"Expected empty function finding, got: {findings}"
        )

    def test_empty_async_function_detected(self, tmp_path):
        path = str(tmp_path / "empty_async.py")
        with open(path, "w") as f:
            f.write("async def my_async():\n    pass\n")
        findings = super_scanner.analyze_file(path)
        assert any("Empty function: my_async" in f for f in findings)

    def test_empty_class_detected(self, tmp_path):
        path = str(tmp_path / "empty_class.py")
        with open(path, "w") as f:
            f.write("class MyClass:\n    pass\n")
        findings = super_scanner.analyze_file(path)
        assert any("Empty class: MyClass" in f for f in findings), (
            f"Expected empty class finding, got: {findings}"
        )

    def test_non_empty_function_not_flagged(self, tmp_path):
        path = str(tmp_path / "real_func.py")
        with open(path, "w") as f:
            f.write("def real_func():\n    return 42\n")
        findings = super_scanner.analyze_file(path)
        assert not any("Empty function" in f for f in findings)

    def test_non_empty_class_not_flagged(self, tmp_path):
        path = str(tmp_path / "real_class.py")
        with open(path, "w") as f:
            f.write("class RealClass:\n    x = 1\n")
        findings = super_scanner.analyze_file(path)
        assert not any("Empty class" in f for f in findings)

    def test_empty_function_finding_includes_line_number(self, tmp_path):
        path = str(tmp_path / "lined_func.py")
        with open(path, "w") as f:
            # Empty function starts at line 3
            f.write("x = 1\ny = 2\ndef stub_func():\n    pass\n")
        findings = super_scanner.analyze_file(path)
        assert any(":3 " in f for f in findings), (
            f"Finding should reference line 3 where function starts: {findings}"
        )

    def test_non_python_file_does_not_trigger_ast_check(self, tmp_path):
        """AST analysis is only for .py files; .txt files with pass-like text should not raise."""
        path = str(tmp_path / "not_python.txt")
        with open(path, "w") as f:
            f.write("def foo():\n    pass\n")
        # Should not fail; may or may not detect patterns but must not raise
        findings = super_scanner.analyze_file(path)
        assert isinstance(findings, list)
        # Should NOT contain "Empty function" findings for non-.py files
        assert not any("Empty function" in f for f in findings)

    def test_class_with_docstring_only_not_flagged(self, tmp_path):
        """A class with only a docstring is not just 'pass' — the AST body has an Expr node."""
        path = str(tmp_path / "doc_class.py")
        with open(path, "w") as f:
            f.write('class DocClass:\n    """A documented class."""\n')
        findings = super_scanner.analyze_file(path)
        assert not any("Empty class" in f for f in findings)

    def test_function_with_docstring_only_not_flagged(self, tmp_path):
        """A function with only a docstring has an Expr node, not Pass."""
        path = str(tmp_path / "doc_func.py")
        with open(path, "w") as f:
            f.write('def doc_func():\n    """Documented."""\n')
        findings = super_scanner.analyze_file(path)
        assert not any("Empty function" in f for f in findings)


# ---------------------------------------------------------------------------
# analyze_file — error handling
# ---------------------------------------------------------------------------

class TestAnalyzeFileErrorHandling:
    """Errors should be captured as findings, not raised as exceptions."""

    def test_nonexistent_file_returns_error_finding(self, tmp_path):
        path = str(tmp_path / "does_not_exist.txt")
        findings = super_scanner.analyze_file(path)
        assert len(findings) == 1
        assert "Error reading file" in findings[0]
        assert path in findings[0]

    def test_nonexistent_file_finding_has_zero_line(self, tmp_path):
        path = str(tmp_path / "missing.txt")
        findings = super_scanner.analyze_file(path)
        assert ":0 -" in findings[0]

    def test_invalid_python_syntax_returns_parse_failed_finding(self, tmp_path):
        path = str(tmp_path / "bad_syntax.py")
        with open(path, "w") as f:
            f.write("def broken(\n    # syntax error\n")
        findings = super_scanner.analyze_file(path)
        assert any("Parse failed" in f for f in findings), (
            f"Expected parse failure finding, got: {findings}"
        )

    def test_invalid_python_syntax_finding_has_zero_line(self, tmp_path):
        path = str(tmp_path / "bad_syntax2.py")
        with open(path, "w") as f:
            f.write("class (:\n    pass\n")
        findings = super_scanner.analyze_file(path)
        parse_findings = [f for f in findings if "Parse failed" in f]
        assert len(parse_findings) == 1
        assert ":0 -" in parse_findings[0]

    def test_analyze_file_always_returns_list(self, tmp_path):
        """Return type must always be a list, even for error cases."""
        path = str(tmp_path / "nonexistent.py")
        result = super_scanner.analyze_file(path)
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# scan_recursive
# ---------------------------------------------------------------------------

class TestScanRecursive:
    """scan_recursive must walk the directory tree and aggregate findings."""

    def test_clean_directory_returns_empty_list(self, tmp_path):
        (tmp_path / "clean.txt").write_text("No issues here.\n")
        (tmp_path / "also_clean.py").write_text("def hello():\n    return 'hi'\n")
        findings = super_scanner.scan_recursive(str(tmp_path))
        assert findings == []

    def test_finds_issues_in_nested_file(self, tmp_path):
        sub = tmp_path / "subdir"
        sub.mkdir()
        (sub / "nested.txt").write_text("# TODO nested issue\n")
        findings = super_scanner.scan_recursive(str(tmp_path))
        assert len(findings) > 0

    def test_aggregates_findings_from_multiple_files(self, tmp_path):
        (tmp_path / "file_a.txt").write_text("# TODO item a\n")
        (tmp_path / "file_b.txt").write_text("# FIXME item b\n")
        findings = super_scanner.scan_recursive(str(tmp_path))
        assert len(findings) >= 2

    def test_skips_hidden_directories(self, tmp_path):
        hidden = tmp_path / ".git"
        hidden.mkdir()
        (hidden / "secret.txt").write_text("# TODO should be ignored\n")
        # Non-hidden file has no issues
        (tmp_path / "clean.txt").write_text("No issues.\n")
        findings = super_scanner.scan_recursive(str(tmp_path))
        assert findings == [], (
            "Findings from inside hidden .git directory should be skipped"
        )

    def test_skips_any_hidden_directory(self, tmp_path):
        hidden = tmp_path / ".hidden_dir"
        hidden.mkdir()
        (hidden / "issue.txt").write_text("placeholder value\n")
        (tmp_path / "normal.txt").write_text("all good\n")
        findings = super_scanner.scan_recursive(str(tmp_path))
        assert all(".hidden_dir" not in f for f in findings)

    def test_does_not_skip_non_hidden_directories(self, tmp_path):
        visible = tmp_path / "visible_dir"
        visible.mkdir()
        (visible / "issue.txt").write_text("# TODO visible\n")
        findings = super_scanner.scan_recursive(str(tmp_path))
        assert len(findings) > 0

    def test_returns_list(self, tmp_path):
        result = super_scanner.scan_recursive(str(tmp_path))
        assert isinstance(result, list)

    def test_excludes_super_scanner_file_from_results(self, tmp_path):
        """Even if super_scanner.py is included in tree, it must be skipped."""
        scanner_copy = tmp_path / "super_scanner.py"
        # Copy the real scanner content to a temp location with the same filename
        real_path = os.path.join(TOOLS_DIR, "super_scanner.py")
        with open(real_path, "r") as src, open(str(scanner_copy), "w") as dst:
            dst.write(src.read())
        findings = super_scanner.scan_recursive(str(tmp_path))
        assert not any("super_scanner.py" in f for f in findings)

    def test_multiple_nesting_levels_scanned(self, tmp_path):
        deep = tmp_path / "a" / "b" / "c"
        deep.mkdir(parents=True)
        (deep / "deep.txt").write_text("# FIXME deep issue\n")
        findings = super_scanner.scan_recursive(str(tmp_path))
        assert len(findings) > 0


# ---------------------------------------------------------------------------
# Boundary / regression tests
# ---------------------------------------------------------------------------

class TestBoundaryAndRegression:
    """Edge cases and boundary conditions."""

    def test_file_with_only_newlines_returns_empty(self, tmp_path):
        path = str(tmp_path / "newlines.txt")
        with open(path, "w") as f:
            f.write("\n\n\n\n")
        findings = super_scanner.analyze_file(path)
        assert findings == []

    def test_pattern_match_is_case_insensitive(self, tmp_path):
        """Patterns must be detected regardless of case."""
        path = str(tmp_path / "case.txt")
        with open(path, "w") as f:
            f.write("tOdO: mixed case\n")
        findings = super_scanner.analyze_file(path)
        assert len(findings) > 0

    def test_stub_pattern_detected_as_substring(self, tmp_path):
        """'stub' should match as a substring (e.g. 'stubbed out')."""
        path = str(tmp_path / "stub_sub.txt")
        with open(path, "w") as f:
            f.write("This function is stubbed out for now\n")
        findings = super_scanner.analyze_file(path)
        assert len(findings) > 0

    def test_analyze_file_first_line_detected(self, tmp_path):
        """A pattern on the very first line (line 1) must be detected."""
        path = str(tmp_path / "first_line.txt")
        with open(path, "w") as f:
            f.write("TODO: this is on line 1\n")
        findings = super_scanner.analyze_file(path)
        assert any(":1 " in f for f in findings)

    def test_analyze_file_last_line_without_newline(self, tmp_path):
        """A file that does not end with a newline must still be scanned."""
        path = str(tmp_path / "no_newline.txt")
        with open(path, "w") as f:
            f.write("TODO: no trailing newline")
        findings = super_scanner.analyze_file(path)
        assert len(findings) > 0

    def test_multiple_empty_functions_all_reported(self, tmp_path):
        """All empty functions in a file should be reported."""
        path = str(tmp_path / "multi_empty.py")
        with open(path, "w") as f:
            f.write(
                "def func_a():\n    pass\n\ndef func_b():\n    pass\n"
            )
        findings = super_scanner.analyze_file(path)
        empty_func_findings = [f for f in findings if "Empty function" in f]
        assert len(empty_func_findings) == 2

    def test_scan_recursive_returns_empty_for_nonexistent_path(self):
        """Scanning a path that doesn't exist should return error findings (not crash)."""
        # os.walk on a non-existent path yields nothing; no findings expected
        result = super_scanner.scan_recursive("/tmp/__nonexistent_path_xyz_12345__")
        assert isinstance(result, list)
