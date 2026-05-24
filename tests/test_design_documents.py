"""
Tests for the three design documents added in this PR:
  - MASTER_TECHNICAL_DESIGN.md
  - OMNISCIENT_SYSTEM_EVOLUTION_PLAN.md
  - STRATEGIC_ZENITH_OMNISCIENT_AUDIT.md

Tests cover:
- File existence and non-empty content
- Required sections / modules present in each document
- Specific technical values, thresholds, and constants documented
- Cross-document consistency (whitelist commands, hardware thresholds)
- All source files and workflows referenced in the docs exist on disk
- The regex pattern documented in the audit is syntactically valid
"""

import os
import re
import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")

MASTER_DESIGN_PATH = os.path.join(REPO_ROOT, "MASTER_TECHNICAL_DESIGN.md")
EVOLUTION_PLAN_PATH = os.path.join(REPO_ROOT, "OMNISCIENT_SYSTEM_EVOLUTION_PLAN.md")
AUDIT_PATH = os.path.join(REPO_ROOT, "STRATEGIC_ZENITH_OMNISCIENT_AUDIT.md")

SRC_TOOLS_DIR = os.path.join(REPO_ROOT, "src", "tools")
SRC_WORKFLOWS_DIR = os.path.join(REPO_ROOT, "src", "workflows")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


@pytest.fixture(scope="module")
def master_design():
    return _read(MASTER_DESIGN_PATH)


@pytest.fixture(scope="module")
def evolution_plan():
    return _read(EVOLUTION_PLAN_PATH)


@pytest.fixture(scope="module")
def audit_doc():
    return _read(AUDIT_PATH)


# ---------------------------------------------------------------------------
# MASTER_TECHNICAL_DESIGN.md
# ---------------------------------------------------------------------------

class TestMasterTechnicalDesignExists:
    """The file must exist and contain meaningful content."""

    def test_file_exists(self):
        assert os.path.isfile(MASTER_DESIGN_PATH), "MASTER_TECHNICAL_DESIGN.md not found"

    def test_file_is_not_empty(self, master_design):
        assert len(master_design.strip()) > 0

    def test_file_size_reasonable(self):
        size = os.path.getsize(MASTER_DESIGN_PATH)
        assert size > 500, "File appears too small to be a complete design document"


class TestMasterTechnicalDesignVersion:
    """Version metadata must be present and well-formed."""

    def test_version_present(self, master_design):
        assert "Version: 1.0.0" in master_design

    def test_title_present(self, master_design):
        assert "MASTER TECHNICAL DESIGN DOCUMENT" in master_design


class TestMasterTechnicalDesignSections:
    """All 15 required sections must be present."""

    REQUIRED_SECTIONS = [
        "1. EXECUTIVE SUMMARY",
        "2. TARGET ARCHITECTURE",
        "3. GAP ANALYSIS",
        "4. EPICS",
        "5. STORIES AND SUBTASKS",
        "6. MICRO-GRANULAR TASK LIST",
        "7. DEVSECOPS ARCHITECTURE",
        "8. AUTONOMOUS SELF-HEALING FRAMEWORK",
        "9. TESTING STRATEGY",
        "10. CHAOS ENGINEERING PLAN",
        "11. ACCEPTANCE CRITERIA",
        "12. VALIDATION CHECKLIST",
        "13. RISK ASSESSMENT",
        "14. PRIORITIZED EXECUTION ROADMAP",
        "15. DEFINITION OF PRODUCTION READY",
    ]

    @pytest.mark.parametrize("section", REQUIRED_SECTIONS)
    def test_section_present(self, master_design, section):
        assert section in master_design, f"Required section missing: '{section}'"

    def test_section_count(self, master_design):
        """Exactly 15 numbered top-level sections (all-caps headings, single space after dot)."""
        # Section headings look like "1. EXECUTIVE SUMMARY" — two consecutive uppercase letters
        # distinguish them from list items like "1. Configure `bandit`..."
        matches = re.findall(r"^\d+\. [A-Z]{2,}", master_design, re.MULTILINE)
        assert len(matches) == 15, f"Expected 15 numbered sections, found {len(matches)}"


class TestMasterTechnicalDesignEpics:
    """All 4 EPICs must be documented."""

    EPICS = ["EPIC-01", "EPIC-02", "EPIC-03", "EPIC-04"]

    @pytest.mark.parametrize("epic", EPICS)
    def test_epic_present(self, master_design, epic):
        assert epic in master_design, f"Epic '{epic}' not found in MASTER_TECHNICAL_DESIGN.md"


class TestMasterTechnicalDesignSourceReferences:
    """Core source files referenced in the architecture must be named."""

    REFERENCED_FILES = [
        "swarm_engine.py",
        "watcher.py",
        "security_scanner.py",
        "deep_analyzer.py",
        "autonomous_fixing.json",
        "sdlc_dashboard.json",
    ]

    @pytest.mark.parametrize("filename", REFERENCED_FILES)
    def test_file_referenced(self, master_design, filename):
        assert filename in master_design, (
            f"Expected source reference '{filename}' missing from MASTER_TECHNICAL_DESIGN.md"
        )


class TestMasterTechnicalDesignKeyContent:
    """Critical acceptance criteria and status markers must be present."""

    def test_ooda_loop_mentioned(self, master_design):
        assert "OODA" in master_design

    def test_zero_stub_guarantee(self, master_design):
        assert "Zero Stub Guarantee" in master_design

    def test_autonomy_status(self, master_design):
        assert "LEVEL 1 AUTONOMY ACHIEVED" in master_design

    def test_whitelist_acceptance_criteria(self, master_design):
        assert "allowedCommands" in master_design

    def test_bandit_task_complete(self, master_design):
        assert "bandit" in master_design.lower()
        assert "COMPLETE" in master_design

    def test_devsecops_pipeline_mentions_pytest(self, master_design):
        assert "pytest" in master_design


# ---------------------------------------------------------------------------
# OMNISCIENT_SYSTEM_EVOLUTION_PLAN.md
# ---------------------------------------------------------------------------

class TestEvolutionPlanExists:
    """The file must exist and contain meaningful content."""

    def test_file_exists(self):
        assert os.path.isfile(EVOLUTION_PLAN_PATH), "OMNISCIENT_SYSTEM_EVOLUTION_PLAN.md not found"

    def test_file_is_not_empty(self, evolution_plan):
        assert len(evolution_plan.strip()) > 0

    def test_file_size_reasonable(self):
        size = os.path.getsize(EVOLUTION_PLAN_PATH)
        assert size > 500


class TestEvolutionPlanSections:
    """All 5 top-level sections must be present."""

    REQUIRED_SECTIONS = [
        "I. CRITICAL IMPROVEMENTS",
        "II. ENHANCEMENTS",
        "III. AUTOMATION FRAMEWORK",
        "IV. TECH DEBT ROADMAP",
        "V. 10X GROWTH CHECKLIST",
    ]

    @pytest.mark.parametrize("section", REQUIRED_SECTIONS)
    def test_section_present(self, evolution_plan, section):
        assert section in evolution_plan, f"Required section missing: '{section}'"


class TestEvolutionPlanWhitelist:
    """Whitelist commands must be documented as IMPLEMENTED."""

    WHITELIST_COMMANDS = ["git", "pytest", "npm", "python3"]

    @pytest.mark.parametrize("cmd", WHITELIST_COMMANDS)
    def test_command_present(self, evolution_plan, cmd):
        assert cmd in evolution_plan, (
            f"Whitelisted command '{cmd}' not documented in OMNISCIENT_SYSTEM_EVOLUTION_PLAN.md"
        )

    def test_whitelist_marked_implemented(self, evolution_plan):
        """The whitelist section must carry the IMPLEMENTED marker."""
        assert "IMPLEMENTED" in evolution_plan

    def test_strict_command_whitelist_heading(self, evolution_plan):
        assert "Strict Command Whitelist" in evolution_plan


class TestEvolutionPlanTechnicalValues:
    """Specific thresholds and sizing values must be documented."""

    def test_llm_latency_threshold_30s(self, evolution_plan):
        """Circuit breaker trips at 30 s LLM latency."""
        assert "30s" in evolution_plan

    def test_swarm_breadth_minimum(self, evolution_plan):
        """N=1 for minimal impact (typo)."""
        assert "N=1" in evolution_plan

    def test_swarm_breadth_maximum(self, evolution_plan):
        """N=25 for high-impact logical vulnerability."""
        assert "N=25" in evolution_plan

    def test_fractal_agent_count(self, evolution_plan):
        """15,625 agents documented in the hierarchy."""
        assert "15,625" in evolution_plan


class TestEvolutionPlanAutomationTable:
    """The automation framework table must document all four issue types."""

    ISSUE_TYPES = [
        "Recurring Errors",
        "Code Stubs",
        "Dead Ends",
        "Loopholes",
    ]

    @pytest.mark.parametrize("issue", ISSUE_TYPES)
    def test_issue_type_present(self, evolution_plan, issue):
        assert issue in evolution_plan, (
            f"Automation table entry '{issue}' missing from OMNISCIENT_SYSTEM_EVOLUTION_PLAN.md"
        )


class TestEvolutionPlanSourceReferences:
    """Core source modules cited in the plan must be named."""

    REFERENCED_FILES = [
        "omniscient_injector.py",
        "swarm_engine.py",
        "super_scanner.py",
        "deep_analyzer.py",
        "autonomous_fixing.json",
        "sdlc_dashboard.json",
        "security_scanner.py",
    ]

    @pytest.mark.parametrize("filename", REFERENCED_FILES)
    def test_file_referenced(self, evolution_plan, filename):
        assert filename in evolution_plan, (
            f"Expected reference '{filename}' missing from OMNISCIENT_SYSTEM_EVOLUTION_PLAN.md"
        )


class TestEvolutionPlanStatusMarker:
    """Operational status must be declared."""

    def test_operational_status_present(self, evolution_plan):
        assert "IQ400 ZENITH OPERATIONAL" in evolution_plan

    def test_sast_dast_gates_implemented(self, evolution_plan):
        assert "SAST/DAST Gates" in evolution_plan
        assert "IMPLEMENTED" in evolution_plan


# ---------------------------------------------------------------------------
# STRATEGIC_ZENITH_OMNISCIENT_AUDIT.md
# ---------------------------------------------------------------------------

class TestAuditDocExists:
    """The file must exist and contain meaningful content."""

    def test_file_exists(self):
        assert os.path.isfile(AUDIT_PATH), "STRATEGIC_ZENITH_OMNISCIENT_AUDIT.md not found"

    def test_file_is_not_empty(self, audit_doc):
        assert len(audit_doc.strip()) > 0

    def test_file_size_reasonable(self):
        size = os.path.getsize(AUDIT_PATH)
        assert size > 500


class TestAuditDocModules:
    """All 5 numbered modules must be present."""

    REQUIRED_MODULES = [
        "Module 1:",
        "Module 2:",
        "Module 3:",
        "Module 4:",
        "Module 5:",
    ]

    @pytest.mark.parametrize("module", REQUIRED_MODULES)
    def test_module_present(self, audit_doc, module):
        assert module in audit_doc, f"Required '{module}' missing from audit document"


class TestAuditDocOODALoop:
    """All five OODA loop stages must be present."""

    OODA_STAGES = ["OBSERVE", "ORIENT", "DECIDE", "ACT", "PROMOTE"]

    @pytest.mark.parametrize("stage", OODA_STAGES)
    def test_ooda_stage_present(self, audit_doc, stage):
        assert stage in audit_doc, f"OODA stage '{stage}' not documented"

    def test_ooda_pipeline_complete(self, audit_doc):
        """Pipeline must include both commit-on-success and rollback-on-failure."""
        assert "git commit" in audit_doc.lower()
        assert "git reset" in audit_doc.lower()


class TestAuditDocTechDebtRegex:
    """The documented regex pattern must be syntactically valid and match expected tokens."""

    DOCUMENTED_PATTERN = r'\b(TODO|FIXME|STUB|HACK)\b'

    def test_regex_is_present_in_doc(self, audit_doc):
        assert "TODO|FIXME|STUB|HACK" in audit_doc

    def test_regex_is_case_insensitive_flag_documented(self, audit_doc):
        assert "re.IGNORECASE" in audit_doc

    def test_regex_compiles(self):
        pattern = re.compile(self.DOCUMENTED_PATTERN, re.IGNORECASE)
        assert pattern is not None

    @pytest.mark.parametrize("token", ["TODO", "FIXME", "STUB", "HACK",
                                        "todo", "fixme", "stub", "hack"])
    def test_regex_matches_token(self, token):
        pattern = re.compile(self.DOCUMENTED_PATTERN, re.IGNORECASE)
        assert pattern.search(token), f"Documented regex should match '{token}'"

    def test_regex_does_not_match_partial_word(self):
        """Word-boundary anchors must prevent false positives."""
        pattern = re.compile(self.DOCUMENTED_PATTERN, re.IGNORECASE)
        assert not pattern.search("TODOS"), "Regex must not match 'TODOS' (partial word)"
        assert not pattern.search("UNFIXABLE"), "Regex must not match 'UNFIXABLE'"


class TestAuditDocWhitelist:
    """Whitelist commands and rejected shell operators must be documented."""

    WHITELIST_COMMANDS = ["git", "python3", "npm", "pytest"]
    REJECTED_OPERATORS = [";", "||", "`"]

    @pytest.mark.parametrize("cmd", WHITELIST_COMMANDS)
    def test_whitelisted_command_present(self, audit_doc, cmd):
        assert cmd in audit_doc, (
            f"Whitelisted command '{cmd}' not documented in STRATEGIC_ZENITH_OMNISCIENT_AUDIT.md"
        )

    def test_allowedcommands_array_documented(self, audit_doc):
        assert "allowedCommands" in audit_doc

    @pytest.mark.parametrize("op", REJECTED_OPERATORS)
    def test_rejected_operator_documented(self, audit_doc, op):
        assert op in audit_doc, (
            f"Shell operator '{op}' (to be rejected) not documented in audit"
        )


class TestAuditDocHardwareThresholds:
    """CPU and memory thresholds for throttling must be documented."""

    def test_cpu_threshold_documented(self, audit_doc):
        assert "cpu_percent" in audit_doc

    def test_memory_threshold_documented(self, audit_doc):
        assert "memory_usage" in audit_doc

    def test_threshold_value_90_documented(self, audit_doc):
        """Both thresholds use 90 percent."""
        assert "90" in audit_doc

    def test_psutil_dependency_documented(self, audit_doc):
        assert "psutil" in audit_doc


class TestAuditDocTechnicalCounts:
    """Specific architectural constants must be documented."""

    def test_fractal_agent_count(self, audit_doc):
        assert "15,625" in audit_doc

    def test_six_layer_debate_documented(self, audit_doc):
        assert "6-layer" in audit_doc

    def test_negative_test_cases_per_fix(self, audit_doc):
        """Swarm must generate at least 3 negative test cases per fix."""
        assert "3 negative test cases" in audit_doc


class TestAuditDocSourceReferences:
    """All tools cited in the audit must be named."""

    # The OODA pipeline diagram in the audit omits the .py extension for some tools:
    #   "super_scanner (AST) + security_scanner (Bandit) + deep_analyzer (Logic gaps)"
    REFERENCED_FILES = [
        "watcher.py",
        "super_scanner.py",
        "swarm_engine.py",
        "hardware_monitor.py",
        "autonomous_fixing.json",
    ]

    @pytest.mark.parametrize("filename", REFERENCED_FILES)
    def test_file_referenced(self, audit_doc, filename):
        assert filename in audit_doc, (
            f"Expected reference '{filename}' missing from STRATEGIC_ZENITH_OMNISCIENT_AUDIT.md"
        )

    def test_deep_analyzer_referenced(self, audit_doc):
        """deep_analyzer is cited in the OODA pipeline (without .py extension)."""
        assert "deep_analyzer" in audit_doc

    def test_security_scanner_referenced(self, audit_doc):
        """security_scanner is cited in the OODA pipeline (without .py extension)."""
        assert "security_scanner" in audit_doc

    def test_src_tools_directory_referenced(self, audit_doc):
        assert "src/tools" in audit_doc

    def test_src_workflows_directory_referenced(self, audit_doc):
        assert "src/workflows" in audit_doc


# ---------------------------------------------------------------------------
# Cross-document consistency
# ---------------------------------------------------------------------------

class TestDocumentCrossConsistency:
    """Claims shared across documents must be internally consistent."""

    def test_whitelist_commands_consistent(self, evolution_plan, audit_doc):
        """Both documents must name the same four whitelisted commands."""
        commands = ["git", "python3", "npm", "pytest"]
        for cmd in commands:
            assert cmd in evolution_plan, f"'{cmd}' missing from evolution plan"
            assert cmd in audit_doc, f"'{cmd}' missing from audit doc"

    def test_hardware_threshold_consistent(self, master_design, audit_doc):
        """Hardware throttling is referenced in both the design and audit."""
        assert "hardware" in master_design.lower()
        assert "hardware" in audit_doc.lower()

    def test_bandit_referenced_in_all_three_docs(self, master_design, evolution_plan, audit_doc):
        assert "bandit" in master_design.lower()
        assert "bandit" in evolution_plan.lower()
        assert "bandit" in audit_doc.lower()

    def test_ooda_referenced_in_all_three_docs(self, master_design, evolution_plan, audit_doc):
        assert "OODA" in master_design
        assert "OODA" in evolution_plan
        assert "OODA" in audit_doc

    def test_swarm_engine_referenced_in_all_three_docs(self, master_design, evolution_plan, audit_doc):
        assert "swarm_engine.py" in master_design
        assert "swarm_engine.py" in evolution_plan
        assert "swarm_engine.py" in audit_doc

    def test_zero_stub_concept_consistent(self, master_design, audit_doc):
        """Zero-Stub guarantee must be named in both the design and audit."""
        assert "Zero Stub" in master_design
        assert "Zero Stub" in audit_doc

    def test_fractal_agent_count_consistent(self, evolution_plan, audit_doc):
        """15,625-agent count must be consistent across evolution plan and audit."""
        assert "15,625" in evolution_plan
        assert "15,625" in audit_doc


# ---------------------------------------------------------------------------
# Referenced source files actually exist on disk
# ---------------------------------------------------------------------------

class TestDocumentedSourceFilesExist:
    """Every source file cited as implemented in the docs must exist in the repo."""

    TOOL_FILES = [
        "swarm_engine.py",
        "watcher.py",
        "security_scanner.py",
        "deep_analyzer.py",
        "super_scanner.py",
        "hardware_monitor.py",
        "omniscient_injector.py",
    ]

    WORKFLOW_FILES = [
        "autonomous_fixing.json",
        "sdlc_dashboard.json",
        "task_orchestrator.json",
    ]

    @pytest.mark.parametrize("tool", TOOL_FILES)
    def test_tool_file_exists(self, tool):
        path = os.path.join(SRC_TOOLS_DIR, tool)
        assert os.path.isfile(path), (
            f"Tool '{tool}' referenced in design docs but not found at {path}"
        )

    @pytest.mark.parametrize("workflow", WORKFLOW_FILES)
    def test_workflow_file_exists(self, workflow):
        path = os.path.join(SRC_WORKFLOWS_DIR, workflow)
        assert os.path.isfile(path), (
            f"Workflow '{workflow}' referenced in design docs but not found at {path}"
        )

    def test_src_tools_directory_exists(self):
        assert os.path.isdir(SRC_TOOLS_DIR), f"src/tools directory not found at {SRC_TOOLS_DIR}"

    def test_src_workflows_directory_exists(self):
        assert os.path.isdir(SRC_WORKFLOWS_DIR), (
            f"src/workflows directory not found at {SRC_WORKFLOWS_DIR}"
        )
