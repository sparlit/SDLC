"""
Tests for src/tools/super_scanner.py

This file was added in this PR. It scans a codebase for placeholder patterns,
incomplete code markers, and structurally empty Python functions/classes.

The tests here verify:
 - The PATTERNS list contains the expected entries
 - analyze_file() correctly detects each pattern (case-insensitive)
 - analyze_file() excludes itself when scanning super_scanner.py
 - analyze_file() detects empty Python functions and empty Python classes via AST
 - analyze_file() handles non-existent files gracefully
 - analyze_file() returns no false positives for clean files
 - scan_recursive() walks directories and collects findings from multiple files
 - scan_recursive() skips hidden directories (e.g. .git)
 - scan_recursive() returns an empty list for a directory with no matching files
"""

import os
import sys
import pytest

# ---------------------------------------------------------------------------
# Make the src/tools package importable regardless of working directory
# ---------------------------------------------------------------------------

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_SRC_TOOLS = os.path.join(_REPO_ROOT, "src", "tools")
if _SRC_TOOLS not in sys.path:
    sys.path.insert(0, _SRC_TOOLS)

from super_scanner import PATTERNS, analyze_file, scan_recursive


# ---------------------------------------------------------------------------
# PATTERNS list
# ---------------------------------------------------------------------------

class TestPatternsList:
    """The module-level PATTERNS list is the source of truth for what gets flagged."""

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

    def test_patterns_is_a_list(self):
        assert isinstance(PATTERNS, list)

    def test_patterns_is_not_empty(self):
        assert len(PATTERNS) > 0

    @pytest.mark.parametrize("pattern", EXPECTED_PATTERNS)
    def test_expected_pattern_present(self, pattern):
        assert pattern in PATTERNS, f"Expected pattern {pattern!r} to be in PATTERNS"

    def test_patterns_count(self):
        assert len(PATTERNS) == 14


# ---------------------------------------------------------------------------
# analyze_file() – pattern detection
# ---------------------------------------------------------------------------

class TestAnalyzeFilePatternDetection:
    """analyze_file() must report findings for each recognised pattern."""

    @pytest.mark.parametrize("pattern_text", [
        "TODO",
        "FIXME",
        "STUB",
        "placeholder",
        "stub",
        "wrapper",
        "bottleneck",
        "blind spot",
        "loose end",
        "dead end",
        "loop hole",
        "build later",
        "fix later",
        "empty wrapper",
    ])
    def test_detects_pattern(self, tmp_path, pattern_text):
        f = tmp_path / "sample.txt"
        f.write_text(f"# this line contains {pattern_text} in the text\n")
        findings = analyze_file(str(f))
        assert len(findings) >= 1, (
            f"Expected at least one finding for pattern {pattern_text!r}"
        )

    def test_finding_contains_filepath(self, tmp_path):
        f = tmp_path / "myfile.txt"
        f.write_text("# TODO fix this\n")
        findings = analyze_file(str(f))
        assert str(f) in findings[0]

    def test_finding_contains_line_number(self, tmp_path):
        f = tmp_path / "myfile.txt"
        f.write_text("line one\n# TODO fix this\nline three\n")
        findings = analyze_file(str(f))
        # "TODO" is on line 2
        assert ":2 " in findings[0] or ":2-" in findings[0] or findings[0].count(":2") >= 1

    def test_finding_contains_matching_line_content(self, tmp_path):
        f = tmp_path / "myfile.txt"
        f.write_text("# TODO: fix authentication\n")
        findings = analyze_file(str(f))
        assert "TODO: fix authentication" in findings[0]

    def test_multiple_patterns_on_different_lines(self, tmp_path):
        f = tmp_path / "multi.txt"
        f.write_text("# TODO item one\n# FIXME item two\n")
        findings = analyze_file(str(f))
        assert len(findings) >= 2

    def test_multiple_patterns_on_same_line(self, tmp_path):
        """A line matching multiple patterns produces one finding per pattern."""
        f = tmp_path / "overlap.txt"
        # "stub" and "wrapper" are both in PATTERNS; a line can match both
        f.write_text("empty wrapper stub here\n")
        findings = analyze_file(str(f))
        assert len(findings) >= 2


class TestAnalyzeFileCaseInsensitivity:
    """Patterns must be detected regardless of letter case."""

    @pytest.mark.parametrize("variant", ["todo", "Todo", "TODO", "tOdO"])
    def test_todo_case_insensitive(self, tmp_path, variant):
        f = tmp_path / "case_test.txt"
        f.write_text(f"# {variant}: do something\n")
        findings = analyze_file(str(f))
        assert len(findings) >= 1, f"Pattern not detected for variant {variant!r}"

    @pytest.mark.parametrize("variant", ["fixme", "FIXME", "Fixme"])
    def test_fixme_case_insensitive(self, tmp_path, variant):
        f = tmp_path / "case_test.txt"
        f.write_text(f"# {variant} this broken thing\n")
        findings = analyze_file(str(f))
        assert len(findings) >= 1, f"Pattern not detected for variant {variant!r}"

    @pytest.mark.parametrize("variant", ["Placeholder", "PLACEHOLDER", "placeholder"])
    def test_placeholder_case_insensitive(self, tmp_path, variant):
        f = tmp_path / "case_test.txt"
        f.write_text(f"x = '{variant}'\n")
        findings = analyze_file(str(f))
        assert len(findings) >= 1, f"Pattern not detected for variant {variant!r}"


class TestAnalyzeFileSelfExclusion:
    """super_scanner.py must exclude itself from its own findings."""

    def test_self_exclusion(self):
        """Scanning the super_scanner.py file itself must produce zero findings
        even though the PATTERNS list contains strings like 'placeholder' and 'stub'."""
        scanner_path = os.path.join(_SRC_TOOLS, "super_scanner.py")
        if not os.path.isfile(scanner_path):
            pytest.skip("super_scanner.py not found at expected location")
        findings = analyze_file(scanner_path)
        # Pattern-based findings must be suppressed; AST findings (empty fns) could still appear
        pattern_findings = [
            f for f in findings
            if "Found pattern" in f
        ]
        assert len(pattern_findings) == 0, (
            f"super_scanner.py should not report pattern findings on itself: {pattern_findings}"
        )


class TestAnalyzeFileCleanFiles:
    """Files that contain none of the patterns should yield zero findings."""

    def test_no_findings_for_clean_file(self, tmp_path):
        f = tmp_path / "clean.py"
        f.write_text("def greet(name):\n    return f'Hello, {name}'\n")
        findings = analyze_file(str(f))
        assert findings == []

    def test_no_findings_for_empty_file(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_text("")
        findings = analyze_file(str(f))
        assert findings == []


# ---------------------------------------------------------------------------
# analyze_file() – Python AST analysis
# ---------------------------------------------------------------------------

class TestAnalyzeFileASTDetection:
    """For .py files, empty functions and classes (body = pass) must be reported."""

    def test_empty_function_detected(self, tmp_path):
        f = tmp_path / "empty_func.py"
        f.write_text("def my_empty_func():\n    pass\n")
        findings = analyze_file(str(f))
        assert any("Empty function" in finding and "my_empty_func" in finding
                   for finding in findings), (
            f"Expected 'Empty function: my_empty_func' in findings, got: {findings}"
        )

    def test_empty_async_function_detected(self, tmp_path):
        f = tmp_path / "empty_async.py"
        f.write_text("async def my_async_func():\n    pass\n")
        findings = analyze_file(str(f))
        assert any("Empty function" in finding and "my_async_func" in finding
                   for finding in findings)

    def test_empty_class_detected(self, tmp_path):
        f = tmp_path / "empty_class.py"
        f.write_text("class MyEmptyClass:\n    pass\n")
        findings = analyze_file(str(f))
        assert any("Empty class" in finding and "MyEmptyClass" in finding
                   for finding in findings)

    def test_non_empty_function_not_reported(self, tmp_path):
        """A function with a real body must not be flagged as empty."""
        f = tmp_path / "real_func.py"
        f.write_text("def real_func():\n    return 42\n")
        findings = analyze_file(str(f))
        assert not any("Empty function" in finding for finding in findings)

    def test_non_empty_class_not_reported(self, tmp_path):
        """A class with a real method must not be flagged as empty."""
        f = tmp_path / "real_class.py"
        f.write_text("class RealClass:\n    def method(self):\n        return 1\n")
        findings = analyze_file(str(f))
        assert not any("Empty class" in finding for finding in findings)

    def test_function_with_docstring_only_not_flagged_as_empty(self, tmp_path):
        """A function whose only body statement is a docstring has len(body)==1 but
        the body node is an Expr(Constant), not Pass — so it should NOT be flagged."""
        f = tmp_path / "docstring_func.py"
        f.write_text('def documented():\n    """This is documented."""\n')
        findings = analyze_file(str(f))
        assert not any("Empty function" in finding for finding in findings)

    def test_ast_analysis_only_for_py_files(self, tmp_path):
        """Non-.py files should not trigger AST analysis (no 'Empty function' findings)."""
        f = tmp_path / "not_python.txt"
        f.write_text("def my_func():\n    pass\n")
        findings = analyze_file(str(f))
        assert not any("Empty function" in finding for finding in findings)

    def test_empty_function_finding_includes_line_number(self, tmp_path):
        f = tmp_path / "lineno_test.py"
        f.write_text("x = 1\n\ndef stub_fn():\n    pass\n")
        findings = analyze_file(str(f))
        empty_fn_findings = [f for f in findings if "Empty function" in f]
        assert len(empty_fn_findings) == 1
        # Line number for stub_fn definition (line 3) must appear
        assert ":3 " in empty_fn_findings[0] or ":3-" in empty_fn_findings[0] or ":3\n" in empty_fn_findings[0] or "3" in empty_fn_findings[0]

    def test_invalid_python_syntax_does_not_crash(self, tmp_path):
        """analyze_file() must not raise on a .py file with syntax errors."""
        f = tmp_path / "bad_syntax.py"
        f.write_text("def broken(\n    # unclosed\n")
        try:
            findings = analyze_file(str(f))
            # May or may not have pattern-based findings; must not raise
        except Exception as exc:
            pytest.fail(f"analyze_file raised an exception on bad syntax: {exc}")


# ---------------------------------------------------------------------------
# analyze_file() – error handling
# ---------------------------------------------------------------------------

class TestAnalyzeFileErrorHandling:
    """analyze_file() must degrade gracefully when files cannot be read normally."""

    def test_nonexistent_file_returns_error_finding(self, tmp_path):
        missing = str(tmp_path / "does_not_exist.txt")
        findings = analyze_file(missing)
        assert len(findings) == 1
        assert "Error reading file" in findings[0]

    def test_nonexistent_file_finding_contains_filepath(self, tmp_path):
        missing = str(tmp_path / "missing_file.py")
        findings = analyze_file(missing)
        assert missing in findings[0]

    def test_nonexistent_file_finding_line_zero(self, tmp_path):
        """Error findings use ':0' to indicate no specific line."""
        missing = str(tmp_path / "gone.txt")
        findings = analyze_file(missing)
        assert ":0 " in findings[0]

    def test_returns_list(self, tmp_path):
        """Return type must always be a list, even for error cases."""
        f = tmp_path / "file.txt"
        f.write_text("clean content\n")
        result = analyze_file(str(f))
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# scan_recursive()
# ---------------------------------------------------------------------------

class TestScanRecursive:
    """scan_recursive() walks an entire directory tree and aggregates findings."""

    def test_empty_directory_returns_empty_list(self, tmp_path):
        findings = scan_recursive(str(tmp_path))
        assert findings == []

    def test_finds_pattern_in_nested_file(self, tmp_path):
        subdir = tmp_path / "sub" / "deep"
        subdir.mkdir(parents=True)
        f = subdir / "code.py"
        f.write_text("# TODO: refactor this\n")
        findings = scan_recursive(str(tmp_path))
        assert len(findings) >= 1
        assert any(str(f) in finding for finding in findings)

    def test_aggregates_from_multiple_files(self, tmp_path):
        (tmp_path / "a.txt").write_text("# FIXME broken\n")
        (tmp_path / "b.txt").write_text("# TODO also broken\n")
        findings = scan_recursive(str(tmp_path))
        assert len(findings) >= 2

    def test_clean_directory_returns_empty_list(self, tmp_path):
        (tmp_path / "clean.py").write_text("x = 1 + 2\n")
        findings = scan_recursive(str(tmp_path))
        assert findings == []

    def test_skips_hidden_directories(self, tmp_path):
        """Directories starting with '.' (like .git) must be ignored."""
        hidden = tmp_path / ".git"
        hidden.mkdir()
        (hidden / "config").write_text("# TODO should be skipped\n")
        findings = scan_recursive(str(tmp_path))
        assert findings == [], (
            f"scan_recursive should skip .git directory, got: {findings}"
        )

    def test_skips_other_hidden_directories(self, tmp_path):
        """Any directory starting with '.' is hidden and must be skipped."""
        hidden = tmp_path / ".hidden_dir"
        hidden.mkdir()
        (hidden / "notes.txt").write_text("placeholder text\n")
        # Also add a normal file with no patterns
        (tmp_path / "normal.txt").write_text("clean file\n")
        findings = scan_recursive(str(tmp_path))
        assert findings == []

    def test_does_not_skip_visible_subdirectory(self, tmp_path):
        """Non-hidden subdirectories must be walked normally."""
        visible = tmp_path / "src"
        visible.mkdir()
        (visible / "utils.py").write_text("# placeholder logic\n")
        findings = scan_recursive(str(tmp_path))
        assert len(findings) >= 1

    def test_returns_list(self, tmp_path):
        result = scan_recursive(str(tmp_path))
        assert isinstance(result, list)

    def test_finding_format_includes_filepath_and_line(self, tmp_path):
        f = tmp_path / "fmt.txt"
        f.write_text("stub implementation here\n")
        findings = scan_recursive(str(tmp_path))
        assert len(findings) >= 1
        finding = findings[0]
        # Format: "<filepath>:<lineno> - Found pattern '<pattern>': <line>"
        assert str(f) in finding
        assert "Found pattern" in finding


# ---------------------------------------------------------------------------
# Regression / boundary tests
# ---------------------------------------------------------------------------

class TestRegressionAndBoundary:
    """Edge cases and regression guards for super_scanner behaviour."""

    def test_pattern_list_has_no_duplicates(self):
        assert len(PATTERNS) == len(set(PATTERNS)), (
            "PATTERNS list contains duplicate entries"
        )

    def test_pattern_list_contains_only_strings(self):
        for p in PATTERNS:
            assert isinstance(p, str), f"Non-string pattern found: {p!r}"

    def test_analyze_file_with_binary_like_content(self, tmp_path):
        """Files with non-UTF-8 bytes must not crash (errors='ignore' mode)."""
        f = tmp_path / "binary.bin"
        f.write_bytes(b"\xff\xfe TODO binary content \x00\x01")
        try:
            findings = analyze_file(str(f))
            # Result can be empty or contain findings; what matters is no crash
        except Exception as exc:
            pytest.fail(f"analyze_file crashed on binary-like file: {exc}")

    def test_analyze_file_single_line_no_newline(self, tmp_path):
        """Files without a trailing newline must be handled correctly."""
        f = tmp_path / "no_newline.txt"
        f.write_text("TODO no newline at end")
        findings = analyze_file(str(f))
        assert len(findings) >= 1

    def test_very_large_patterns_list_not_truncated(self):
        """Ensure PATTERNS covers both short ('stub') and multi-word patterns."""
        short = [p for p in PATTERNS if " " not in p]
        multi_word = [p for p in PATTERNS if " " in p]
        assert len(short) >= 3, "Expected several single-word patterns"
        assert len(multi_word) >= 3, "Expected several multi-word patterns"

    def test_scan_recursive_on_single_file_directory(self, tmp_path):
        """scan_recursive on a dir with one clean file returns empty list."""
        (tmp_path / "main.py").write_text("print('hello world')\n")
        assert scan_recursive(str(tmp_path)) == []

    def test_analyze_file_with_super_scanner_in_name_skips_patterns(self, tmp_path):
        """Any filepath containing 'super_scanner.py' is excluded from pattern findings."""
        # Simulate a file named like the scanner itself in a tmp subdir
        f = tmp_path / "super_scanner.py"
        f.write_text("# TODO this should be excluded\nPATTERNS = ['placeholder']\n")
        findings = analyze_file(str(f))
        pattern_findings = [fi for fi in findings if "Found pattern" in fi]
        assert len(pattern_findings) == 0

    def test_analyze_file_correctly_numbers_first_line(self, tmp_path):
        """Line numbering must start at 1."""
        f = tmp_path / "first_line.txt"
        f.write_text("TODO first line\nsecond line\n")
        findings = analyze_file(str(f))
        assert any(":1 " in finding for finding in findings), (
            "First line should be numbered :1"
        )
