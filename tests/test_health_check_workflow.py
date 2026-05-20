"""
Tests for src/workflows/health_check.json

This workflow was added in this PR. It periodically checks hardware health
and routes to an alert notification when the system is under stress.

The tests here verify:
 - The file exists and is valid JSON
 - The workflow has the correct name and structure
 - Each expected node is present with the correct type and parameters
 - The schedule trigger fires every 30 minutes (consistent with autonomous_fixing.json)
 - The check-hardware node invokes the hardware_monitor.py tool
 - The is-stable conditional node checks exit code 0
 - The alert-notification node signals a critical hardware alert
 - The connection graph is correctly wired
 - The stable (success) branch of is-stable has no onward connections
 - The unstable (failure) branch of is-stable routes to alert-notification
"""

import json
import os
import pytest

WORKFLOW_PATH = os.path.join(
    os.path.dirname(__file__), "..", "src", "workflows", "health_check.json"
)

EXPECTED_NODE_IDS = [
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

    def test_workflow_has_nodes_list(self, workflow):
        assert "nodes" in workflow
        assert isinstance(workflow["nodes"], list)

    def test_workflow_has_connections_dict(self, workflow):
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
    @pytest.mark.parametrize("node_id", EXPECTED_NODE_IDS)
    def test_required_node_present(self, nodes_by_id, node_id):
        assert node_id in nodes_by_id, (
            f"Node '{node_id}' is missing from the workflow"
        )

    def test_health_trigger_is_schedule_type(self, nodes_by_id):
        node = nodes_by_id["health-trigger"]
        assert node["type"] == "n8n-nodes-base.scheduleTrigger"

    def test_check_hardware_is_execute_command_type(self, nodes_by_id):
        node = nodes_by_id["check-hardware"]
        assert node["type"] == "n8n-nodes-base.executeCommand"

    def test_is_stable_is_if_type(self, nodes_by_id):
        node = nodes_by_id["is-stable"]
        assert node["type"] == "n8n-nodes-base.if"

    def test_alert_notification_is_noop_type(self, nodes_by_id):
        node = nodes_by_id["alert-notification"]
        assert node["type"] == "n8n-nodes-base.noOp"

    def test_all_nodes_have_type_version(self, workflow):
        for node in workflow["nodes"]:
            assert "typeVersion" in node, (
                f"Node '{node.get('id')}' is missing 'typeVersion'"
            )

    def test_all_nodes_have_position(self, workflow):
        for node in workflow["nodes"]:
            assert "position" in node, (
                f"Node '{node.get('id')}' is missing 'position'"
            )
            assert len(node["position"]) == 2


# ---------------------------------------------------------------------------
# Schedule trigger parameters
# ---------------------------------------------------------------------------

class TestHealthTriggerParameters:
    def test_schedule_interval_is_30(self, nodes_by_id):
        params = nodes_by_id["health-trigger"]["parameters"]
        assert params["interval"] == 30

    def test_schedule_unit_is_minutes(self, nodes_by_id):
        params = nodes_by_id["health-trigger"]["parameters"]
        assert params["unit"] == "minutes"

    def test_trigger_name_is_health_trigger(self, nodes_by_id):
        assert nodes_by_id["health-trigger"]["name"] == "Health Trigger"


# ---------------------------------------------------------------------------
# check-hardware node
# ---------------------------------------------------------------------------

class TestCheckHardwareNode:
    def test_command_runs_hardware_monitor(self, nodes_by_id):
        command = nodes_by_id["check-hardware"]["parameters"]["command"]
        assert "hardware_monitor.py" in command, (
            f"Expected command to reference 'hardware_monitor.py', got: {command!r}"
        )

    def test_command_uses_python3(self, nodes_by_id):
        command = nodes_by_id["check-hardware"]["parameters"]["command"]
        assert "python3" in command

    def test_command_uses_data_project_path(self, nodes_by_id):
        command = nodes_by_id["check-hardware"]["parameters"]["command"]
        assert "/data/project" in command

    def test_node_display_name(self, nodes_by_id):
        assert nodes_by_id["check-hardware"]["name"] == "Check Hardware"


# ---------------------------------------------------------------------------
# is-stable conditional node
# ---------------------------------------------------------------------------

class TestIsStableNode:
    def test_checks_exit_code(self, nodes_by_id):
        conditions = nodes_by_id["is-stable"]["parameters"]["conditions"]
        number_conditions = conditions.get("number", [])
        assert len(number_conditions) >= 1, "Expected at least one numeric condition"

    def test_compares_exit_code_to_zero(self, nodes_by_id):
        conditions = nodes_by_id["is-stable"]["parameters"]["conditions"]
        number_conditions = conditions.get("number", [])
        condition = number_conditions[0]
        assert condition["value2"] == 0, "is-stable should compare exit code to 0"

    def test_uses_equal_operation(self, nodes_by_id):
        conditions = nodes_by_id["is-stable"]["parameters"]["conditions"]
        number_conditions = conditions.get("number", [])
        condition = number_conditions[0]
        assert condition["operation"] == "equal"

    def test_references_check_hardware_exit_code(self, nodes_by_id):
        conditions = nodes_by_id["is-stable"]["parameters"]["conditions"]
        number_conditions = conditions.get("number", [])
        condition = number_conditions[0]
        assert "Check Hardware" in condition["value1"]
        assert "exitCode" in condition["value1"]

    def test_node_display_name(self, nodes_by_id):
        assert nodes_by_id["is-stable"]["name"] == "Is Stable?"


# ---------------------------------------------------------------------------
# alert-notification node
# ---------------------------------------------------------------------------

class TestAlertNotificationNode:
    def test_has_content_parameter(self, nodes_by_id):
        params = nodes_by_id["alert-notification"]["parameters"]
        assert "content" in params

    def test_content_mentions_hardware_alert(self, nodes_by_id):
        content = nodes_by_id["alert-notification"]["parameters"]["content"]
        assert "HARDWARE ALERT" in content.upper() or "hardware alert" in content.lower()

    def test_content_references_check_hardware_stdout(self, nodes_by_id):
        content = nodes_by_id["alert-notification"]["parameters"]["content"]
        assert "Check Hardware" in content and "stdout" in content

    def test_has_title_parameter(self, nodes_by_id):
        params = nodes_by_id["alert-notification"]["parameters"]
        assert "title" in params
        assert params["title"] != ""

    def test_node_display_name(self, nodes_by_id):
        assert nodes_by_id["alert-notification"]["name"] == "Alert Notification"


# ---------------------------------------------------------------------------
# Connections
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

    def test_is_stable_unstable_branch_connects_to_alert(self, workflow):
        """Output index 1 (false branch) of is-stable routes to alert-notification."""
        connections = workflow["connections"]
        assert "is-stable" in connections
        # main[1] is the false/unstable branch
        unstable_branch = connections["is-stable"]["main"][1]
        targets = [e["node"] for e in unstable_branch]
        assert "alert-notification" in targets, (
            "Unstable branch must route to alert-notification"
        )

    def test_is_stable_stable_branch_has_no_connections(self, workflow):
        """Output index 0 (true/stable branch) should have no onward connections."""
        connections = workflow["connections"]
        stable_branch = connections["is-stable"]["main"][0]
        assert stable_branch == [], (
            "Stable branch should have no outgoing connections (workflow ends silently)"
        )

    def test_health_trigger_is_entry_point(self, workflow):
        """health-trigger must not be the target of any connection."""
        all_targets = set()
        for edges in workflow["connections"].values():
            for slot in edges.get("main", []):
                for edge in slot:
                    all_targets.add(edge["node"])
        assert "health-trigger" not in all_targets

    def test_alert_notification_has_no_outgoing_connections(self, workflow):
        """alert-notification is a terminal node."""
        connections = workflow["connections"]
        assert "alert-notification" not in connections, (
            "alert-notification should have no outgoing connections"
        )

    def test_each_connection_edge_has_type_and_index(self, workflow):
        """Every edge in the connections graph must have 'node', 'type', and 'index'."""
        for source, edges in workflow["connections"].items():
            for slot in edges.get("main", []):
                for edge in slot:
                    assert "node" in edge, f"Edge from {source!r} is missing 'node'"
                    assert "type" in edge, f"Edge from {source!r} is missing 'type'"
                    assert "index" in edge, f"Edge from {source!r} is missing 'index'"


# ---------------------------------------------------------------------------
# Regression and boundary tests
# ---------------------------------------------------------------------------

class TestHealthCheckRegressionAndBoundary:
    def test_workflow_does_not_reference_deep_analyzer(self, workflow):
        raw = json.dumps(workflow)
        assert "deep_analyzer" not in raw

    def test_workflow_does_not_reference_super_scanner(self, workflow):
        """health_check.json should use hardware_monitor.py, not the code scanner."""
        raw = json.dumps(workflow)
        assert "super_scanner" not in raw

    def test_workflow_references_hardware_monitor(self, workflow):
        raw = json.dumps(workflow)
        assert "hardware_monitor" in raw

    def test_workflow_references_data_project_path(self, workflow):
        """All tool invocations should use the canonical /data/project path."""
        raw = json.dumps(workflow)
        assert "/data/project" in raw

    def test_schedule_matches_autonomous_fixing_interval(self, nodes_by_id):
        """Both health_check and autonomous_fixing use 30-minute intervals."""
        params = nodes_by_id["health-trigger"]["parameters"]
        assert params["interval"] == 30
        assert params["unit"] == "minutes"

    def test_is_stable_has_two_output_branches(self, workflow):
        """An IF node always has exactly two output branches (true and false)."""
        connections = workflow["connections"]
        is_stable_main = connections["is-stable"]["main"]
        assert len(is_stable_main) == 2, (
            "is-stable (IF node) must have exactly 2 output branches"
        )

    def test_workflow_json_is_serialisable(self, workflow):
        """Round-trip: the loaded workflow must be re-serialisable without data loss."""
        serialised = json.dumps(workflow)
        reloaded = json.loads(serialised)
        assert reloaded == workflow