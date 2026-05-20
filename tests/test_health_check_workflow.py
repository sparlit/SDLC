"""
Tests for src/workflows/health_check.json

This workflow was added in this PR to monitor hardware health and send
alerts when system resources are under stress.

The workflow contains four nodes:
  - health-trigger:      scheduleTrigger firing every 30 minutes
  - check-hardware:      executeCommand running hardware_monitor.py (continueOnFail)
  - is-stable:           if-node that branches on the hardware monitor exit code
  - alert-notification:  httpRequest that fires only when the system is NOT stable

These tests verify:
  - The file exists and contains valid JSON
  - The workflow name and structure are correct
  - Each required node is present with the correct type and configuration
  - The connection graph correctly routes healthy (true) and failing (false) paths
  - Boundary and regression conditions
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
def check_hardware_node(nodes_by_id):
    return nodes_by_id["check-hardware"]


@pytest.fixture(scope="module")
def is_stable_node(nodes_by_id):
    return nodes_by_id["is-stable"]


@pytest.fixture(scope="module")
def alert_notification_node(nodes_by_id):
    return nodes_by_id["alert-notification"]


# ---------------------------------------------------------------------------
# File-level tests
# ---------------------------------------------------------------------------

class TestHealthCheckWorkflowFileExists:
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

class TestHealthCheckWorkflowStructure:
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
        assert nodes_by_id["health-trigger"]["type"] == "n8n-nodes-base.scheduleTrigger"

    def test_check_hardware_type(self, nodes_by_id):
        assert nodes_by_id["check-hardware"]["type"] == "n8n-nodes-base.executeCommand"

    def test_is_stable_type(self, nodes_by_id):
        assert nodes_by_id["is-stable"]["type"] == "n8n-nodes-base.if"

    def test_alert_notification_type(self, nodes_by_id):
        assert nodes_by_id["alert-notification"]["type"] == "n8n-nodes-base.httpRequest"

    def test_all_node_ids_are_unique(self, workflow):
        ids = [node["id"] for node in workflow["nodes"]]
        assert len(ids) == len(set(ids)), "Duplicate node IDs found in workflow"

    def test_all_node_names_are_unique(self, workflow):
        names = [node["name"] for node in workflow["nodes"]]
        assert len(names) == len(set(names)), "Duplicate node names found in workflow"


# ---------------------------------------------------------------------------
# Schedule trigger node
# ---------------------------------------------------------------------------

class TestHealthTriggerNode:
    def test_fires_every_30_minutes(self, nodes_by_id):
        params = nodes_by_id["health-trigger"]["parameters"]
        assert params["interval"] == 30

    def test_interval_unit_is_minutes(self, nodes_by_id):
        params = nodes_by_id["health-trigger"]["parameters"]
        assert params["unit"] == "minutes"

    def test_node_name(self, nodes_by_id):
        assert nodes_by_id["health-trigger"]["name"] == "Health Trigger"


# ---------------------------------------------------------------------------
# check-hardware node
# ---------------------------------------------------------------------------

class TestCheckHardwareNode:
    def test_command_runs_hardware_monitor(self, check_hardware_node):
        command = check_hardware_node["parameters"]["command"]
        assert "hardware_monitor.py" in command, (
            f"Expected command to reference 'hardware_monitor.py', got: {command!r}"
        )

    def test_command_uses_python3(self, check_hardware_node):
        command = check_hardware_node["parameters"]["command"]
        assert "python3" in command

    def test_command_references_data_project(self, check_hardware_node):
        command = check_hardware_node["parameters"]["command"]
        assert "/data/project" in command

    def test_continue_on_fail_is_true(self, check_hardware_node):
        """continueOnFail must be true so a missing script doesn't halt the workflow."""
        assert check_hardware_node["parameters"].get("continueOnFail") is True, (
            "check-hardware node must have continueOnFail: true to handle missing script gracefully"
        )

    def test_node_name(self, check_hardware_node):
        assert check_hardware_node["name"] == "Check Hardware"


# ---------------------------------------------------------------------------
# is-stable node
# ---------------------------------------------------------------------------

class TestIsStableNode:
    def test_is_if_node(self, is_stable_node):
        assert is_stable_node["type"] == "n8n-nodes-base.if"

    def test_conditions_check_exit_code(self, is_stable_node):
        """The condition must evaluate the exit code of check-hardware."""
        params = is_stable_node["parameters"]
        raw = json.dumps(params)
        assert "exitCode" in raw, (
            "is-stable conditions should evaluate exitCode from check-hardware"
        )

    def test_exit_code_expected_value_is_zero(self, is_stable_node):
        """A zero exit code means the hardware monitor reported no issues."""
        conditions = is_stable_node["parameters"]["conditions"]
        number_conditions = conditions.get("number", [])
        assert len(number_conditions) > 0
        condition = number_conditions[0]
        assert condition["value2"] == 0, (
            "is-stable should check exitCode == 0 (healthy)"
        )

    def test_condition_operation_is_equal(self, is_stable_node):
        conditions = is_stable_node["parameters"]["conditions"]
        number_conditions = conditions.get("number", [])
        assert number_conditions[0]["operation"] == "equal"

    def test_condition_references_check_hardware_node(self, is_stable_node):
        raw = json.dumps(is_stable_node["parameters"])
        assert "Check Hardware" in raw

    def test_node_name(self, is_stable_node):
        assert is_stable_node["name"] == "Is Stable?"


# ---------------------------------------------------------------------------
# alert-notification node
# ---------------------------------------------------------------------------

class TestAlertNotificationNode:
    def test_uses_post_method(self, alert_notification_node):
        assert alert_notification_node["parameters"]["method"] == "POST"

    def test_send_body_is_true(self, alert_notification_node):
        assert alert_notification_node["parameters"].get("sendBody") is True

    def test_has_body_parameters(self, alert_notification_node):
        params = alert_notification_node["parameters"]
        assert "bodyParameters" in params
        assert "parameters" in params["bodyParameters"]

    def test_alert_title_is_hardware_alert(self, alert_notification_node):
        body_params = alert_notification_node["parameters"]["bodyParameters"]["parameters"]
        title_params = [p for p in body_params if p["name"] == "title"]
        assert len(title_params) == 1
        assert title_params[0]["value"] == "Hardware Alert"

    def test_alert_content_references_check_hardware_output(self, alert_notification_node):
        """Alert body must include the hardware monitor stdout."""
        body_params = alert_notification_node["parameters"]["bodyParameters"]["parameters"]
        content_params = [p for p in body_params if p["name"] == "content"]
        assert len(content_params) == 1
        assert "Check Hardware" in content_params[0]["value"]

    def test_alert_url_has_default_webhook(self, alert_notification_node):
        """URL must have a fallback so the workflow works without ALERT_WEBHOOK_URL set."""
        url = alert_notification_node["parameters"]["url"]
        # The URL uses a template expression; just check a fallback URL is present
        assert "localhost:5678" in url or "5678" in url, (
            "alert-notification should include a default webhook URL"
        )

    def test_alert_node_uses_http_request_type(self, alert_notification_node):
        assert alert_notification_node["type"] == "n8n-nodes-base.httpRequest"

    def test_node_name(self, alert_notification_node):
        assert alert_notification_node["name"] == "Alert Notification"


# ---------------------------------------------------------------------------
# Connection graph
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

    def test_is_stable_false_path_connects_to_alert(self, workflow):
        """
        The false (unhealthy) branch of is-stable must lead to alert-notification.
        n8n if-nodes: main[0] = true path, main[1] = false path.
        """
        connections = workflow["connections"]
        assert "is-stable" in connections
        false_path = connections["is-stable"]["main"][1]
        targets = [e["node"] for e in false_path]
        assert "alert-notification" in targets, (
            "The false (unstable) path of is-stable must lead to alert-notification"
        )

    def test_is_stable_true_path_has_no_connections(self, workflow):
        """When hardware is healthy, no further action is taken."""
        connections = workflow["connections"]
        true_path = connections["is-stable"]["main"][0]
        assert true_path == [], (
            "The true (stable) path of is-stable should have no outgoing connections"
        )

    def test_alert_notification_has_no_outgoing_connections(self, workflow):
        """alert-notification is the terminal node."""
        connections = workflow["connections"]
        assert "alert-notification" not in connections, (
            "alert-notification should have no outgoing connections"
        )

    def test_health_trigger_is_entry_point(self, workflow):
        """health-trigger must not be the target of any connection."""
        all_targets = set()
        for edges in workflow["connections"].values():
            for slot in edges.get("main", []):
                for edge in slot:
                    all_targets.add(edge["node"])
        assert "health-trigger" not in all_targets


# ---------------------------------------------------------------------------
# Boundary / regression tests
# ---------------------------------------------------------------------------

class TestHealthCheckBoundaryAndRegression:
    def test_workflow_does_not_reference_deep_analyzer(self, workflow):
        raw = json.dumps(workflow)
        assert "deep_analyzer" not in raw

    def test_workflow_does_not_reference_super_scanner(self, workflow):
        """Health check is separate from the fixing workflow; no cross-contamination."""
        raw = json.dumps(workflow)
        assert "super_scanner" not in raw

    def test_workflow_references_hardware_monitor(self, workflow):
        raw = json.dumps(workflow)
        assert "hardware_monitor" in raw

    def test_workflow_has_no_duplicate_node_ids(self, workflow):
        ids = [node["id"] for node in workflow["nodes"]]
        assert len(ids) == len(set(ids))

    def test_all_connection_targets_reference_existing_nodes(self, workflow):
        """Every connection target must be a node that actually exists."""
        node_ids = {node["id"] for node in workflow["nodes"]}
        for source, edges in workflow["connections"].items():
            for slot in edges.get("main", []):
                for edge in slot:
                    assert edge["node"] in node_ids, (
                        f"Connection from '{source}' references non-existent node '{edge['node']}'"
                    )

    def test_all_connection_sources_reference_existing_nodes(self, workflow):
        """Every connection source must also be an existing node."""
        node_ids = {node["id"] for node in workflow["nodes"]}
        for source in workflow["connections"]:
            assert source in node_ids, (
                f"Connection source '{source}' does not correspond to any node"
            )

    def test_check_hardware_continues_on_fail(self, workflow):
        """continueOnFail prevents the workflow halting if hardware_monitor.py is absent."""
        nodes_by_id = {n["id"]: n for n in workflow["nodes"]}
        assert nodes_by_id["check-hardware"]["parameters"]["continueOnFail"] is True

    def test_all_nodes_have_required_keys(self, workflow):
        required_keys = {"id", "name", "type", "typeVersion", "position", "parameters"}
        for node in workflow["nodes"]:
            missing = required_keys - set(node.keys())
            assert not missing, (
                f"Node '{node.get('id', '?')}' is missing keys: {missing}"
            )