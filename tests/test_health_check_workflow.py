"""
Tests for src/workflows/health_check.json

This workflow was added in this PR as the hardware monitoring component.
It runs on a 30-minute schedule, checks hardware health, and sends alerts
when the system is under stress.

Tests cover:
 - File existence and valid JSON
 - Workflow name and top-level structure
 - All required nodes are present with correct types
 - Schedule trigger interval (30 minutes)
 - Hardware check command and continueOnFail flag
 - Stability check (if node) logic
 - Alert notification configuration (POST method, body, env-var URL)
 - Pipeline connections (trigger -> check -> is-stable -> alert on failure)
 - Node uniqueness
 - Boundary/regression checks
"""

import json
import os

import pytest

WORKFLOW_PATH = os.path.join(
    os.path.dirname(__file__), "..", "src", "workflows", "health_check.json"
)

# Node IDs defined in the workflow
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
def alert_node(nodes_by_id):
    return nodes_by_id["alert-notification"]


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

class TestHealthCheckWorkflowStructure:
    def test_workflow_has_name(self, workflow):
        assert "name" in workflow
        assert workflow["name"] != ""

    def test_workflow_name(self, workflow):
        assert workflow["name"] == "Hardware Health Check"

    def test_workflow_has_nodes_key(self, workflow):
        assert "nodes" in workflow

    def test_workflow_nodes_is_list(self, workflow):
        assert isinstance(workflow["nodes"], list)

    def test_workflow_has_connections_key(self, workflow):
        assert "connections" in workflow

    def test_workflow_connections_is_dict(self, workflow):
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
            f"Node '{node_id}' is missing from health_check.json"
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

    def test_all_nodes_have_id(self, workflow):
        for node in workflow["nodes"]:
            assert "id" in node, f"Node missing 'id': {node}"

    def test_all_nodes_have_name(self, workflow):
        for node in workflow["nodes"]:
            assert "name" in node, f"Node missing 'name': {node}"

    def test_all_nodes_have_type(self, workflow):
        for node in workflow["nodes"]:
            assert "type" in node, f"Node missing 'type': {node}"

    def test_all_node_ids_are_unique(self, workflow):
        ids = [node["id"] for node in workflow["nodes"]]
        assert len(ids) == len(set(ids)), "Duplicate node IDs found in health_check.json"

    def test_all_node_names_are_unique(self, workflow):
        names = [node["name"] for node in workflow["nodes"]]
        assert len(names) == len(set(names)), "Duplicate node names found in health_check.json"


# ---------------------------------------------------------------------------
# Schedule trigger node
# ---------------------------------------------------------------------------

class TestHealthTriggerNode:
    def test_trigger_interval_is_30(self, nodes_by_id):
        params = nodes_by_id["health-trigger"]["parameters"]
        assert params["interval"] == 30, (
            f"Expected interval=30, got {params.get('interval')}"
        )

    def test_trigger_unit_is_minutes(self, nodes_by_id):
        params = nodes_by_id["health-trigger"]["parameters"]
        assert params["unit"] == "minutes", (
            f"Expected unit='minutes', got {params.get('unit')!r}"
        )

    def test_trigger_node_name(self, nodes_by_id):
        assert nodes_by_id["health-trigger"]["name"] == "Health Trigger"


# ---------------------------------------------------------------------------
# Check Hardware node
# ---------------------------------------------------------------------------

class TestCheckHardwareNode:
    def test_command_references_hardware_monitor(self, check_hardware_node):
        command = check_hardware_node["parameters"]["command"]
        assert "hardware_monitor.py" in command, (
            f"Expected command to reference 'hardware_monitor.py', got: {command!r}"
        )

    def test_command_uses_python3(self, check_hardware_node):
        command = check_hardware_node["parameters"]["command"]
        assert "python3" in command, (
            "check-hardware command should use python3"
        )

    def test_command_uses_data_project_path(self, check_hardware_node):
        command = check_hardware_node["parameters"]["command"]
        assert "/data/project" in command, (
            "check-hardware command should reference /data/project path"
        )

    def test_continue_on_fail_is_enabled(self, check_hardware_node):
        """continueOnFail must be true so the workflow can branch on failure."""
        assert check_hardware_node["parameters"].get("continueOnFail") is True, (
            "check-hardware node must have continueOnFail=true"
        )

    def test_node_name(self, check_hardware_node):
        assert check_hardware_node["name"] == "Check Hardware"


# ---------------------------------------------------------------------------
# Is Stable? (if) node
# ---------------------------------------------------------------------------

class TestIsStableNode:
    def test_checks_exit_code_of_check_hardware(self, nodes_by_id):
        """The if node should compare the exitCode output of the check-hardware node."""
        node = nodes_by_id["is-stable"]
        conditions = json.dumps(node["parameters"].get("conditions", {}))
        assert "exitCode" in conditions, (
            f"is-stable should check exitCode, got conditions: {conditions}"
        )
        assert "Check Hardware" in conditions, (
            "is-stable should reference the 'Check Hardware' node output"
        )

    def test_checks_for_exit_code_zero(self, nodes_by_id):
        """A zero exit code means the hardware monitor succeeded (system is stable)."""
        node = nodes_by_id["is-stable"]
        conditions = json.dumps(node["parameters"].get("conditions", {}))
        # value2 should be 0 (integer comparison)
        assert '"value2": 0' in conditions or '"value2":0' in conditions, (
            "is-stable should compare exitCode to 0"
        )

    def test_uses_equal_operation(self, nodes_by_id):
        node = nodes_by_id["is-stable"]
        conditions = json.dumps(node["parameters"].get("conditions", {}))
        assert "equal" in conditions, (
            "is-stable should use 'equal' operation for comparing exitCode"
        )

    def test_node_name(self, nodes_by_id):
        assert nodes_by_id["is-stable"]["name"] == "Is Stable?"


# ---------------------------------------------------------------------------
# Alert Notification node
# ---------------------------------------------------------------------------

class TestAlertNotificationNode:
    def test_uses_post_method(self, alert_node):
        assert alert_node["parameters"]["method"] == "POST"

    def test_url_references_alert_webhook(self, alert_node):
        url = alert_node["parameters"]["url"]
        assert "ALERT_WEBHOOK_URL" in url or "webhook/alert" in url, (
            f"Alert URL should reference ALERT_WEBHOOK_URL env var or fallback, got: {url!r}"
        )

    def test_url_has_env_var_fallback(self, alert_node):
        """URL should use $env.ALERT_WEBHOOK_URL with a localhost fallback."""
        url = alert_node["parameters"]["url"]
        assert "localhost" in url or "ALERT_WEBHOOK_URL" in url

    def test_send_body_is_enabled(self, alert_node):
        assert alert_node["parameters"].get("sendBody") is True

    def test_body_has_title_parameter(self, alert_node):
        body_params = alert_node["parameters"]["bodyParameters"]["parameters"]
        title_params = [p for p in body_params if p["name"] == "title"]
        assert len(title_params) == 1, "Alert must have a 'title' body parameter"
        assert title_params[0]["value"] == "Hardware Alert"

    def test_body_has_content_parameter(self, alert_node):
        body_params = alert_node["parameters"]["bodyParameters"]["parameters"]
        content_params = [p for p in body_params if p["name"] == "content"]
        assert len(content_params) == 1, "Alert must have a 'content' body parameter"

    def test_content_includes_hardware_stats(self, alert_node):
        """Alert content should embed the hardware monitor stdout."""
        body_params = alert_node["parameters"]["bodyParameters"]["parameters"]
        content_params = [p for p in body_params if p["name"] == "content"]
        content_value = content_params[0]["value"]
        assert "Check Hardware" in content_value, (
            "Alert content should reference the Check Hardware node stdout"
        )

    def test_alert_node_type_version(self, alert_node):
        assert alert_node["typeVersion"] == 4

    def test_node_name(self, alert_node):
        assert alert_node["name"] == "Alert Notification"


# ---------------------------------------------------------------------------
# Pipeline connections
# ---------------------------------------------------------------------------

class TestHealthCheckConnections:
    def test_health_trigger_connects_to_check_hardware(self, workflow):
        connections = workflow["connections"]
        assert "health-trigger" in connections
        targets = [
            e["node"]
            for e in connections["health-trigger"]["main"][0]
        ]
        assert "check-hardware" in targets

    def test_check_hardware_connects_to_is_stable(self, workflow):
        connections = workflow["connections"]
        assert "check-hardware" in connections
        targets = [
            e["node"]
            for e in connections["check-hardware"]["main"][0]
        ]
        assert "is-stable" in targets

    def test_is_stable_false_branch_connects_to_alert(self, workflow):
        """When the system is NOT stable (false/second branch), it must alert."""
        connections = workflow["connections"]
        assert "is-stable" in connections
        # Branch index 1 = false/else branch of if node
        false_branch = connections["is-stable"]["main"][1]
        targets = [e["node"] for e in false_branch]
        assert "alert-notification" in targets, (
            f"is-stable false branch should connect to alert-notification, got: {targets}"
        )

    def test_is_stable_true_branch_is_empty(self, workflow):
        """When the system IS stable, no further action is needed."""
        connections = workflow["connections"]
        true_branch = connections["is-stable"]["main"][0]
        assert true_branch == [], (
            f"is-stable true (stable) branch should have no connections, got: {true_branch}"
        )

    def test_health_trigger_is_entry_point(self, workflow):
        """No node should connect TO health-trigger."""
        all_targets = set()
        for edges in workflow["connections"].values():
            for slot in edges.get("main", []):
                for edge in slot:
                    all_targets.add(edge["node"])
        assert "health-trigger" not in all_targets, (
            "health-trigger must not be the target of any connection"
        )

    def test_alert_notification_has_no_outgoing_connections(self, workflow):
        """alert-notification is the terminal node; it must have no outgoing connections."""
        connections = workflow["connections"]
        assert "alert-notification" not in connections, (
            "alert-notification should be the terminal node with no outgoing connections"
        )

    def test_all_connection_targets_are_valid_node_ids(self, workflow):
        """Every connection target must reference an existing node ID."""
        valid_ids = {node["id"] for node in workflow["nodes"]}
        for source, edges in workflow["connections"].items():
            for slot in edges.get("main", []):
                for edge in slot:
                    assert edge["node"] in valid_ids, (
                        f"Connection target '{edge['node']}' from '{source}' is not a valid node ID"
                    )


# ---------------------------------------------------------------------------
# Boundary / regression tests
# ---------------------------------------------------------------------------

class TestHealthCheckBoundaryAndRegression:
    def test_workflow_does_not_reference_super_scanner(self, workflow):
        """health_check.json uses hardware_monitor.py, not super_scanner.py."""
        raw = json.dumps(workflow)
        assert "super_scanner.py" not in raw

    def test_workflow_does_not_reference_deep_analyzer(self, workflow):
        raw = json.dumps(workflow)
        assert "deep_analyzer" not in raw

    def test_workflow_references_hardware_monitor(self, workflow):
        raw = json.dumps(workflow)
        assert "hardware_monitor.py" in raw

    def test_check_hardware_node_continue_on_fail_prevents_pipeline_halt(self, nodes_by_id):
        """Even if hardware_monitor.py returns non-zero, the workflow should proceed."""
        node = nodes_by_id["check-hardware"]
        assert node["parameters"].get("continueOnFail") is True

    def test_workflow_node_positions_are_defined(self, workflow):
        """All nodes should have a position for the n8n canvas."""
        for node in workflow["nodes"]:
            assert "position" in node, f"Node '{node['id']}' is missing a position"
            assert isinstance(node["position"], list)
            assert len(node["position"]) == 2

    def test_connection_type_is_main_for_all_edges(self, workflow):
        """All edge connection types should be 'main'."""
        for source, edges in workflow["connections"].items():
            for slot in edges.get("main", []):
                for edge in slot:
                    assert edge.get("type") == "main", (
                        f"Connection from '{source}' has unexpected type: {edge.get('type')!r}"
                    )

    def test_schedule_interval_matches_autonomous_fixing(self, nodes_by_id):
        """Both health_check and autonomous_fixing run on 30-minute intervals."""
        params = nodes_by_id["health-trigger"]["parameters"]
        assert params["interval"] == 30
        assert params["unit"] == "minutes"