"""
Tests for src/tools/super_scanner.py

This module was added in the PR as the gap-detection component used by the
autonomous_fixing.json workflow. It scans source files for placeholder patterns
and empty Python constructs (functions/classes containing only `pass`).

Tests cover:
- The PATTERNS constant (completeness)
- analyze_file(): pattern detection, self-exclusion, AST analysis, error handling
- scan_recursive(): hidden-directory filtering, recursive traversal
"""

import os
import sys
import ast
import importlib
import pytest

# ---------------------------------------------------------------------------
# Import the module under test
# ---------------------------------------------------------------------------

SCANNER_PATH = os.path.join(
    os.path.dirname(__file__), "..", "src", "tools", "super_scanner.py"
)

# Dynamically load the module so we don't need the project on PYTHONPATH
import importlib.util

spec = importlib.util.spec_from_file_location("super_scanner", SCANNER_PATH)
super_scanner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(super_scanner)

analyze_file = super_scanner.analyze_file
scan_recursive = super_scanner.scan_recursive
PATTERNS = super_scanner.PATTERNS


# ---------------------------------------------------------------------------
# PATTERNS constant
# ---------------------------------------------------------------------------

class TestPatternsList:
    """The PATTERNS list drives all gap detection; it must be complete."""

    EXPECTED_PATTERNS = [
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
    ]

    def test_patterns_is_a_list(self):
        assert isinstance(PATTERNS, list)

    def test_patterns_is_not_empty(self):
        assert len(PATTERNS) > 0

    @pytest.mark.parametrize("pattern", EXPECTED_PATTERNS)
    def test_expected_pattern_present(self, pattern):
        assert pattern in PATTERNS, (
            f"Expected pattern '{pattern}' missing from PATTERNS list"
        )

    def test_patterns_count(self):
        """There should be exactly 14 patterns."""
        assert len(PATTERNS) == 14


# ---------------------------------------------------------------------------
# analyze_file(): pattern detection
# ---------------------------------------------------------------------------

class TestAnalyzeFilePatternDetection:
    """Verify pattern-matching logic in analyze_file()."""

    def test_returns_empty_list_for_clean_file(self, tmp_path):
        clean = tmp_path / "clean.txt"
        clean.write_text("This file has no issues whatsoever.\n")
        findings = analyze_file(str(clean))
        assert findings == []

    def test_detects_todo_uppercase(self, tmp_path):
        f = tmp_path / "code.py"
        f.write_text("x = 1  # TODO: implement this\n")
        findings = analyze_file(str(f))
        assert any("TODO" in finding for finding in findings)

    def test_detects_fixme(self, tmp_path):
        f = tmp_path / "code.py"
        f.write_text("# FIXME: broken logic\n")
        findings = analyze_file(str(f))
        assert any("FIXME" in finding for finding in findings)

    def test_detects_stub_lowercase(self, tmp_path):
        """Pattern matching is case-insensitive; lowercase 'stub' must trigger."""
        f = tmp_path / "code.py"
        f.write_text("# this is just a stub\n")
        findings = analyze_file(str(f))
        assert any("stub" in finding.lower() for finding in findings)

    def test_detects_placeholder(self, tmp_path):
        f = tmp_path / "config.txt"
        f.write_text("api_key=placeholder\n")
        findings = analyze_file(str(f))
        assert any("placeholder" in finding for finding in findings)

    def test_detects_build_later(self, tmp_path):
        f = tmp_path / "notes.txt"
        f.write_text("We need to build later when ready.\n")
        findings = analyze_file(str(f))
        assert any("build later" in finding for finding in findings)

    def test_detects_fix_later(self, tmp_path):
        f = tmp_path / "notes.txt"
        f.write_text("Will fix later after the release.\n")
        findings = analyze_file(str(f))
        assert any("fix later" in finding for finding in findings)

    def test_detects_wrapper(self, tmp_path):
        f = tmp_path / "code.txt"
        f.write_text("This is just a wrapper around the real logic.\n")
        findings = analyze_file(str(f))
        assert any("wrapper" in finding for finding in findings)

    def test_detects_bottleneck(self, tmp_path):
        f = tmp_path / "code.txt"
        f.write_text("This section is a bottleneck in the system.\n")
        findings = analyze_file(str(f))
        assert any("bottleneck" in finding for finding in findings)

    def test_detects_blind_spot(self, tmp_path):
        f = tmp_path / "code.txt"
        f.write_text("Edge case is a blind spot in our tests.\n")
        findings = analyze_file(str(f))
        assert any("blind spot" in finding for finding in findings)

    def test_case_insensitive_todo(self, tmp_path):
        """todo in lowercase must still be detected."""
        f = tmp_path / "code.js"
        f.write_text("// todo: fix this\n")
        findings = analyze_file(str(f))
        assert any("TODO" in finding for finding in findings)

    def test_case_insensitive_fixme(self, tmp_path):
        f = tmp_path / "code.js"
        f.write_text("// fixme: wrong result\n")
        findings = analyze_file(str(f))
        assert any("FIXME" in finding for finding in findings)

    def test_finding_format_contains_filepath(self, tmp_path):
        f = tmp_path / "check.txt"
        f.write_text("# TODO: do something\n")
        findings = analyze_file(str(f))
        assert len(findings) > 0
        assert str(f) in findings[0]

    def test_finding_format_contains_line_number(self, tmp_path):
        f = tmp_path / "check.txt"
        f.write_text("clean line\n# TODO: on line 2\n")
        findings = analyze_file(str(f))
        # The finding should reference line 2
        assert any(":2 " in finding for finding in findings)

    def test_finding_format_contains_pattern_label(self, tmp_path):
        f = tmp_path / "check.txt"
        f.write_text("# TODO: something\n")
        findings = analyze_file(str(f))
        assert any("Found pattern" in finding for finding in findings)

    def test_finding_format_contains_line_content(self, tmp_path):
        f = tmp_path / "check.txt"
        f.write_text("# TODO: implement feature X\n")
        findings = analyze_file(str(f))
        assert any("implement feature X" in finding for finding in findings)

    def test_multiple_patterns_on_different_lines(self, tmp_path):
        f = tmp_path / "multi.txt"
        f.write_text("# TODO: first\n# FIXME: second\n")
        findings = analyze_file(str(f))
        assert len(findings) >= 2

    def test_non_python_file_no_ast_analysis(self, tmp_path):
        """A .txt file with an empty-looking function text should not trigger AST."""
        f = tmp_path / "notes.txt"
        f.write_text("def my_func():\n    pass\n")
        findings = analyze_file(str(f))
        # AST checks only run for .py; should not find empty function here
        assert not any("Empty function" in finding for finding in findings)


# ---------------------------------------------------------------------------
# analyze_file(): self-exclusion
# ---------------------------------------------------------------------------

class TestAnalyzeFileSelfExclusion:
    """Files whose path contains 'super_scanner.py' are excluded from pattern findings."""

    def test_self_exclusion_suppresses_pattern_findings(self, tmp_path):
        """If the filepath contains 'super_scanner.py', pattern matches are skipped."""
        scanner_file = tmp_path / "super_scanner.py"
        scanner_file.write_text("# TODO: this would normally be flagged\n")
        findings = analyze_file(str(scanner_file))
        # No pattern findings should come through for this file
        pattern_findings = [f for f in findings if "Found pattern" in f]
        assert pattern_findings == [], (
            "super_scanner.py should suppress its own pattern findings"
        )

    def test_other_files_are_not_excluded(self, tmp_path):
        """Files NOT named super_scanner.py must still be scanned normally."""
        other_file = tmp_path / "other.py"
        other_file.write_text("# TODO: this should be flagged\n")
        findings = analyze_file(str(other_file))
        assert len(findings) > 0


# ---------------------------------------------------------------------------
# analyze_file(): AST analysis for Python files
# ---------------------------------------------------------------------------

class TestAnalyzeFileAstAnalysis:
    """analyze_file() uses Python's ast module to detect empty functions and classes."""

    def test_detects_empty_function(self, tmp_path):
        py_file = tmp_path / "sample.py"
        py_file.write_text("def empty_func():\n    pass\n")
        findings = analyze_file(str(py_file))
        assert any("Empty function" in f and "empty_func" in f for f in findings), (
            f"Expected 'Empty function: empty_func' in findings, got: {findings}"
        )

    def test_detects_empty_async_function(self, tmp_path):
        py_file = tmp_path / "async_sample.py"
        py_file.write_text("async def my_async_func():\n    pass\n")
        findings = analyze_file(str(py_file))
        assert any("Empty function" in f and "my_async_func" in f for f in findings)

    def test_detects_empty_class(self, tmp_path):
        py_file = tmp_path / "cls_sample.py"
        py_file.write_text("class EmptyClass:\n    pass\n")
        findings = analyze_file(str(py_file))
        assert any("Empty class" in f and "EmptyClass" in f for f in findings), (
            f"Expected 'Empty class: EmptyClass' in findings, got: {findings}"
        )

    def test_non_empty_function_not_flagged(self, tmp_path):
        py_file = tmp_path / "real.py"
        py_file.write_text("def real_func():\n    return 42\n")
        findings = analyze_file(str(py_file))
        assert not any("Empty function" in f for f in findings)

    def test_non_empty_class_not_flagged(self, tmp_path):
        py_file = tmp_path / "real_cls.py"
        py_file.write_text(
            "class RealClass:\n    def method(self):\n        return 1\n"
        )
        findings = analyze_file(str(py_file))
        assert not any("Empty class" in f for f in findings)

    def test_empty_function_finding_includes_line_number(self, tmp_path):
        py_file = tmp_path / "lineno.py"
        py_file.write_text("x = 1\ndef empty_one():\n    pass\n")
        findings = analyze_file(str(py_file))
        empty_findings = [f for f in findings if "Empty function" in f]
        assert len(empty_findings) > 0
        # Line number should be embedded in the finding string
        assert ":2 " in empty_findings[0] or ":2-" in empty_findings[0] or "2" in empty_findings[0]

    def test_parse_failure_reported_as_finding(self, tmp_path):
        """Unparseable Python content must produce a 'Parse failed' finding, not an exception."""
        py_file = tmp_path / "bad_syntax.py"
        py_file.write_text("def (broken syntax:\n")
        findings = analyze_file(str(py_file))
        assert any("Parse failed" in f for f in findings), (
            f"Expected 'Parse failed' entry for bad syntax, got: {findings}"
        )

    def test_parse_failure_finding_format(self, tmp_path):
        py_file = tmp_path / "bad2.py"
        py_file.write_text("class :\n")
        findings = analyze_file(str(py_file))
        parse_findings = [f for f in findings if "Parse failed" in f]
        if parse_findings:
            assert str(py_file) in parse_findings[0]


# ---------------------------------------------------------------------------
# analyze_file(): error handling
# ---------------------------------------------------------------------------

class TestAnalyzeFileErrorHandling:
    """analyze_file() must handle IO errors gracefully."""

    def test_nonexistent_file_returns_error_finding(self, tmp_path):
        nonexistent = str(tmp_path / "does_not_exist.txt")
        findings = analyze_file(nonexistent)
        assert len(findings) == 1
        assert "Error reading file" in findings[0]

    def test_error_finding_contains_filepath(self, tmp_path):
        nonexistent = str(tmp_path / "missing.py")
        findings = analyze_file(nonexistent)
        assert nonexistent in findings[0]

    def test_error_finding_format_has_line_zero(self, tmp_path):
        nonexistent = str(tmp_path / "nope.txt")
        findings = analyze_file(nonexistent)
        assert ":0 " in findings[0]

    def test_returns_list_not_exception(self, tmp_path):
        """analyze_file() must never propagate exceptions to the caller."""
        result = analyze_file("/this/path/should/not/exist/at/all.py")
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# scan_recursive(): directory traversal
# ---------------------------------------------------------------------------

class TestScanRecursive:
    """scan_recursive() walks a directory tree and collects all findings."""

    def test_returns_empty_list_for_clean_directory(self, tmp_path):
        clean = tmp_path / "clean.txt"
        clean.write_text("No issues here.\n")
        findings = scan_recursive(str(tmp_path))
        assert findings == []

    def test_finds_issues_in_nested_file(self, tmp_path):
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        nested = subdir / "nested.txt"
        nested.write_text("# TODO: fix this nested issue\n")
        findings = scan_recursive(str(tmp_path))
        assert len(findings) > 0

    def test_skips_dot_git_directory(self, tmp_path):
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        git_file = git_dir / "config"
        git_file.write_text("# TODO: this is in .git and should be ignored\n")
        findings = scan_recursive(str(tmp_path))
        # .git directory should be skipped entirely
        git_findings = [f for f in findings if ".git" in f]
        assert git_findings == [], (
            f"scan_recursive should skip .git directory, but found: {git_findings}"
        )

    def test_skips_arbitrary_hidden_directory(self, tmp_path):
        """Any directory starting with '.' should be excluded."""
        hidden = tmp_path / ".hidden_cache"
        hidden.mkdir()
        hidden_file = hidden / "secret.txt"
        hidden_file.write_text("placeholder=value\n")
        findings = scan_recursive(str(tmp_path))
        hidden_findings = [f for f in findings if ".hidden_cache" in f]
        assert hidden_findings == [], (
            "scan_recursive should skip all directories starting with '.'"
        )

    def test_does_not_skip_non_hidden_directory(self, tmp_path):
        """Regular subdirectories (not starting with '.') must be scanned."""
        normal_dir = tmp_path / "src"
        normal_dir.mkdir()
        normal_file = normal_dir / "code.txt"
        normal_file.write_text("# TODO: visible subdir file\n")
        findings = scan_recursive(str(tmp_path))
        assert len(findings) > 0

    def test_aggregates_findings_from_multiple_files(self, tmp_path):
        file_a = tmp_path / "a.txt"
        file_a.write_text("# TODO: file a\n")
        file_b = tmp_path / "b.txt"
        file_b.write_text("# FIXME: file b\n")
        findings = scan_recursive(str(tmp_path))
        assert len(findings) >= 2

    def test_returns_list_type(self, tmp_path):
        findings = scan_recursive(str(tmp_path))
        assert isinstance(findings, list)

    def test_empty_directory_returns_empty_list(self, tmp_path):
        findings = scan_recursive(str(tmp_path))
        assert findings == []

    def test_scan_recursive_includes_python_ast_findings(self, tmp_path):
        """scan_recursive must propagate AST-based findings from analyze_file."""
        py_file = tmp_path / "empty_fn.py"
        py_file.write_text("def stub_fn():\n    pass\n")
        findings = scan_recursive(str(tmp_path))
        # 'stub' pattern will match the function name and body, and AST will detect empty function
        ast_findings = [f for f in findings if "Empty function" in f]
        assert len(ast_findings) > 0


# ---------------------------------------------------------------------------
# Regression / boundary tests
# ---------------------------------------------------------------------------

class TestSuperScannerBoundary:
    def test_file_with_only_whitespace_no_findings(self, tmp_path):
        f = tmp_path / "blank.txt"
        f.write_text("   \n\t\n   \n")
        findings = analyze_file(str(f))
        assert findings == []

    def test_very_long_line_does_not_raise(self, tmp_path):
        f = tmp_path / "longline.txt"
        f.write_text("x" * 10000 + " TODO: at end of long line\n")
        findings = analyze_file(str(f))
        assert any("TODO" in finding for finding in findings)

    def test_unicode_file_no_crash(self, tmp_path):
        """Files with unicode content must not crash the scanner."""
        f = tmp_path / "unicode.txt"
        f.write_text("# 日本語テスト TODO: unicode comment\n", encoding="utf-8")
        findings = analyze_file(str(f))
        assert isinstance(findings, list)

    def test_pattern_at_line_one(self, tmp_path):
        f = tmp_path / "firstline.txt"
        f.write_text("TODO: right at the start\n")
        findings = analyze_file(str(f))
        assert any(":1 " in finding for finding in findings)

    def test_multiple_patterns_on_same_line_produces_multiple_findings(self, tmp_path):
        """If a line matches two distinct patterns, both should be reported."""
        f = tmp_path / "multi_pattern.txt"
        # 'wrapper' and 'stub' are both in PATTERNS; a line with both should get 2 findings
        f.write_text("This is a wrapper stub around nothing.\n")
        findings = analyze_file(str(f))
        assert len(findings) >= 2

    def test_analyze_file_returns_list_for_valid_python(self, tmp_path):
        py_file = tmp_path / "valid.py"
        py_file.write_text("def real_function():\n    return True\n")
        findings = analyze_file(str(py_file))
        assert isinstance(findings, list)

    def test_scan_recursive_self_exclusion_when_scanner_in_tree(self, tmp_path):
        """If a file named super_scanner.py is in the scanned tree, its patterns are skipped."""
        scanner_copy = tmp_path / "super_scanner.py"
        scanner_copy.write_text("# TODO: this is inside a copy of the scanner\nPATTERNS = []\n")
        findings = scan_recursive(str(tmp_path))
        pattern_findings = [f for f in findings if "Found pattern" in f]
        assert pattern_findings == [], (
            "Files named super_scanner.py must be excluded from pattern findings"
        )
