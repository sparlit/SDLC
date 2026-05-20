"""
Tests for src/workflows/health_check.json

This workflow was added in the PR to monitor hardware health and trigger
alerts when system resources are under stress. Tests verify:
- File existence and valid JSON
- Correct node inventory and types
- 30-minute schedule trigger
- Hardware check node continues on failure
- Conditional branching based on exit code
- Alert notification structure
- Pipeline connections
"""

import json
import os
import pytest

WORKFLOW_PATH = os.path.join(
    os.path.dirname(__file__), "..", "src", "workflows", "health_check.json"
)

NODE_IDS = [
    "health-trigger",
    "check-hardware",
    "is-stable",
    "alert-notification",
]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def workflow():
    with open(WORKFLOW_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def nodes_by_id(workflow):
    return {node["id"]: node for node in workflow["nodes"]}


@pytest.fixture(scope="module")
def nodes_by_name(workflow):
    return {node["name"]: node for node in workflow["nodes"]}


# ---------------------------------------------------------------------------
# File-level tests
# ---------------------------------------------------------------------------

class TestHealthCheckFileExists:
    def test_file_exists(self):
        assert os.path.isfile(WORKFLOW_PATH), (
            f"src/workflows/health_check.json not found at {WORKFLOW_PATH}"
        )

    def test_file_is_valid_json(self):
        with open(WORKFLOW_PATH) as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_file_is_not_empty(self):
        assert os.path.getsize(WORKFLOW_PATH) > 0


# ---------------------------------------------------------------------------
# Top-level workflow structure
# ---------------------------------------------------------------------------

class TestHealthCheckStructure:
    def test_workflow_has_name(self, workflow):
        assert "name" in workflow
        assert workflow["name"] != ""

    def test_workflow_name(self, workflow):
        assert workflow["name"] == "Hardware Health Check"

    def test_workflow_has_nodes(self, workflow):
        assert "nodes" in workflow
        assert isinstance(workflow["nodes"], list)

    def test_workflow_has_connections(self, workflow):
        assert "connections" in workflow
        assert isinstance(workflow["connections"], dict)

    def test_workflow_has_four_nodes(self, workflow):
        assert len(workflow["nodes"]) == 4

    def test_all_node_ids_are_unique(self, workflow):
        ids = [node["id"] for node in workflow["nodes"]]
        assert len(ids) == len(set(ids)), "Duplicate node IDs found in workflow"

    def test_all_node_names_are_unique(self, workflow):
        names = [node["name"] for node in workflow["nodes"]]
        assert len(names) == len(set(names)), "Duplicate node names found in workflow"


# ---------------------------------------------------------------------------
# Node inventory
# ---------------------------------------------------------------------------

class TestHealthCheckNodes:
    @pytest.mark.parametrize("node_id", NODE_IDS)
    def test_required_node_present(self, nodes_by_id, node_id):
        assert node_id in nodes_by_id, (
            f"Node '{node_id}' is missing from the health_check workflow"
        )

    def test_health_trigger_type(self, nodes_by_id):
        node = nodes_by_id["health-trigger"]
        assert node["type"] == "n8n-nodes-base.scheduleTrigger"

    def test_check_hardware_type(self, nodes_by_id):
        node = nodes_by_id["check-hardware"]
        assert node["type"] == "n8n-nodes-base.executeCommand"

    def test_is_stable_type(self, nodes_by_id):
        node = nodes_by_id["is-stable"]
        assert node["type"] == "n8n-nodes-base.if"

    def test_alert_notification_type(self, nodes_by_id):
        node = nodes_by_id["alert-notification"]
        assert node["type"] == "n8n-nodes-base.httpRequest"


# ---------------------------------------------------------------------------
# Schedule Trigger configuration
# ---------------------------------------------------------------------------

class TestHealthTrigger:
    def test_schedule_interval_is_30(self, nodes_by_id):
        params = nodes_by_id["health-trigger"]["parameters"]
        assert params["interval"] == 30

    def test_schedule_unit_is_minutes(self, nodes_by_id):
        params = nodes_by_id["health-trigger"]["parameters"]
        assert params["unit"] == "minutes"

    def test_health_trigger_version(self, nodes_by_id):
        node = nodes_by_id["health-trigger"]
        assert node["typeVersion"] == 1


# ---------------------------------------------------------------------------
# Check Hardware node
# ---------------------------------------------------------------------------

class TestCheckHardwareNode:
    def test_command_references_hardware_monitor(self, nodes_by_id):
        command = nodes_by_id["check-hardware"]["parameters"]["command"]
        assert "hardware_monitor.py" in command

    def test_command_uses_python3(self, nodes_by_id):
        command = nodes_by_id["check-hardware"]["parameters"]["command"]
        assert "python3" in command

    def test_command_references_project_path(self, nodes_by_id):
        command = nodes_by_id["check-hardware"]["parameters"]["command"]
        assert "/data/project" in command

    def test_continue_on_fail_is_true(self, nodes_by_id):
        """Hardware check must not halt the workflow on failure."""
        params = nodes_by_id["check-hardware"]["parameters"]
        assert params.get("continueOnFail") is True, (
            "check-hardware node must have continueOnFail=true so the workflow continues "
            "even if the hardware monitor script fails"
        )


# ---------------------------------------------------------------------------
# Is Stable? (IF) node
# ---------------------------------------------------------------------------

class TestIsStableNode:
    def test_is_stable_node_name(self, nodes_by_id):
        assert nodes_by_id["is-stable"]["name"] == "Is Stable?"

    def test_condition_checks_exit_code(self, nodes_by_id):
        """The IF node must branch on the exit code of the hardware check."""
        conditions = nodes_by_id["is-stable"]["parameters"]["conditions"]
        # Conditions are expressed as 'number' comparisons
        assert "number" in conditions
        number_conditions = conditions["number"]
        assert len(number_conditions) > 0
        condition = number_conditions[0]
        assert "exitCode" in condition["value1"]

    def test_condition_checks_exit_code_equals_zero(self, nodes_by_id):
        """Exit code 0 means stable; the node must compare to 0."""
        conditions = nodes_by_id["is-stable"]["parameters"]["conditions"]["number"]
        condition = conditions[0]
        assert condition["operation"] == "equal"
        assert condition["value2"] == 0

    def test_condition_references_check_hardware_node(self, nodes_by_id):
        conditions = nodes_by_id["is-stable"]["parameters"]["conditions"]["number"]
        condition = conditions[0]
        assert "Check Hardware" in condition["value1"]


# ---------------------------------------------------------------------------
# Alert Notification node
# ---------------------------------------------------------------------------

class TestAlertNotificationNode:
    def test_uses_post_method(self, nodes_by_id):
        node = nodes_by_id["alert-notification"]
        assert node["parameters"]["method"] == "POST"

    def test_has_send_body_enabled(self, nodes_by_id):
        node = nodes_by_id["alert-notification"]
        assert node["parameters"].get("sendBody") is True

    def test_url_references_alert_webhook(self, nodes_by_id):
        """URL must use the ALERT_WEBHOOK_URL env var or a fallback webhook."""
        url = nodes_by_id["alert-notification"]["parameters"]["url"]
        assert "ALERT_WEBHOOK_URL" in url or "webhook" in url.lower()

    def test_body_has_title_parameter(self, nodes_by_id):
        body_params = nodes_by_id["alert-notification"]["parameters"]["bodyParameters"]["parameters"]
        titles = [p for p in body_params if p["name"] == "title"]
        assert len(titles) == 1
        assert titles[0]["value"] == "Hardware Alert"

    def test_body_has_content_parameter(self, nodes_by_id):
        body_params = nodes_by_id["alert-notification"]["parameters"]["bodyParameters"]["parameters"]
        contents = [p for p in body_params if p["name"] == "content"]
        assert len(contents) == 1

    def test_content_includes_hardware_stats(self, nodes_by_id):
        """Alert content should include live stdout from the hardware check."""
        body_params = nodes_by_id["alert-notification"]["parameters"]["bodyParameters"]["parameters"]
        contents = [p for p in body_params if p["name"] == "content"]
        assert len(contents) == 1
        assert "Check Hardware" in contents[0]["value"] or "stdout" in contents[0]["value"]

    def test_http_request_type_version(self, nodes_by_id):
        node = nodes_by_id["alert-notification"]
        assert node["typeVersion"] == 4

    def test_alert_notification_url_has_fallback(self, nodes_by_id):
        """URL should define a fallback in case ALERT_WEBHOOK_URL is not set."""
        url = nodes_by_id["alert-notification"]["parameters"]["url"]
        assert "||" in url or "localhost" in url


# ---------------------------------------------------------------------------
# Pipeline connections
# ---------------------------------------------------------------------------

class TestHealthCheckConnections:
    def test_health_trigger_connects_to_check_hardware(self, workflow):
        connections = workflow["connections"]
        assert "health-trigger" in connections
        targets = [e["node"] for e in connections["health-trigger"]["main"][0]]
        assert "check-hardware" in targets

    def test_check_hardware_connects_to_is_stable(self, workflow):
        connections = workflow["connections"]
        assert "check-hardware" in connections
        targets = [e["node"] for e in connections["check-hardware"]["main"][0]]
        assert "is-stable" in targets

    def test_is_stable_false_branch_connects_to_alert(self, workflow):
        """When the system is NOT stable (false/index 1), alert must be triggered."""
        connections = workflow["connections"]
        assert "is-stable" in connections
        false_branch = connections["is-stable"]["main"][1]
        targets = [e["node"] for e in false_branch]
        assert "alert-notification" in targets, (
            "The false branch of is-stable (unstable condition) should connect to alert-notification"
        )

    def test_is_stable_true_branch_has_no_connections(self, workflow):
        """When the system is stable, no action is needed (empty true branch)."""
        connections = workflow["connections"]
        true_branch = connections["is-stable"]["main"][0]
        assert true_branch == [], (
            "The true branch of is-stable should have no outgoing connections (system is healthy)"
        )

    def test_health_trigger_is_entry_point(self, workflow):
        """health-trigger must not be the target of any connection."""
        all_targets = set()
        for edges in workflow["connections"].values():
            for slot in edges.get("main", []):
                for edge in slot:
                    all_targets.add(edge["node"])
        assert "health-trigger" not in all_targets

    def test_alert_notification_is_terminal(self, workflow):
        """alert-notification must have no outgoing connections."""
        assert "alert-notification" not in workflow["connections"], (
            "alert-notification should be a terminal node with no outgoing connections"
        )


# ---------------------------------------------------------------------------
# Regression / boundary tests
# ---------------------------------------------------------------------------

class TestHealthCheckRegressionAndBoundary:
    def test_workflow_does_not_reference_super_scanner(self, workflow):
        """Health check is a separate workflow; must not reference the code scanner."""
        raw = json.dumps(workflow)
        assert "super_scanner" not in raw

    def test_workflow_does_not_reference_autonomous_fixing(self, workflow):
        """health_check.json must be self-contained."""
        raw = json.dumps(workflow)
        assert "autonomous_fixing" not in raw

    def test_node_positions_are_set(self, workflow):
        """All nodes should have position metadata for n8n rendering."""
        for node in workflow["nodes"]:
            assert "position" in node, f"Node '{node['id']}' is missing position"
            assert len(node["position"]) == 2

    def test_all_nodes_have_type_version(self, workflow):
        for node in workflow["nodes"]:
            assert "typeVersion" in node, f"Node '{node['id']}' missing typeVersion"

    def test_all_connection_nodes_exist(self, workflow):
        """Every node referenced in connections must exist in the nodes list."""
        node_ids = {node["id"] for node in workflow["nodes"]}
        for source, edges in workflow["connections"].items():
            assert source in node_ids, f"Connection source '{source}' not in nodes"
            for slot in edges.get("main", []):
                for edge in slot:
                    assert edge["node"] in node_ids, (
                        f"Connection target '{edge['node']}' not in nodes"
                    )

    def test_hardware_check_command_is_full_path(self, nodes_by_id):
        """Command must use an absolute path to avoid working-directory issues."""
        command = nodes_by_id["check-hardware"]["parameters"]["command"]
        assert command.startswith("python3 /"), (
            "check-hardware command should use an absolute path"
        )

    def test_schedule_interval_not_too_frequent(self, nodes_by_id):
        """Hardware monitoring should not run more than once per minute."""
        params = nodes_by_id["health-trigger"]["parameters"]
        if params["unit"] == "minutes":
            assert params["interval"] >= 1
        elif params["unit"] == "seconds":
            assert params["interval"] >= 60