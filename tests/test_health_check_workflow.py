import json, os, pytest

WORKFLOW_PATH = os.path.join(os.path.dirname(__file__), "..", "src", "workflows", "health_check.json")

@pytest.fixture
def workflow():
    with open(WORKFLOW_PATH) as f: return json.load(f)

def test_workflow_has_required_nodes(workflow):
    names = {n["name"] for n in workflow["nodes"]}
    required = {"Health Trigger", "Check Hardware", "Is Stable?", "Alert Notification"}
    for r in required: assert r in names

def test_connectivity_flow(workflow):
    conn = workflow["connections"]

    # Check trigger -> check-hardware
    th_found = False
    if "Health Trigger" in conn:
        outputs = [t["node"] for port in conn["Health Trigger"].get("main", []) for t in port]
        if any(n in outputs for n in ["Check Hardware", "Check: Check Hardware (P0)"]): th_found = True
    assert th_found

    # check-hardware -> is-stable
    hi_found = False
    src = "Check Hardware"
    if src in conn:
        outputs = [t["node"] for port in conn[src].get("main", []) for t in port]
        if "Is Stable?" in outputs: hi_found = True
        elif "Check: Check Hardware (P0)" in outputs:
            check_outputs = conn["Check: Check Hardware (P0)"]["main"]
            if len(check_outputs) > 1 and any(t["node"] == "Is Stable?" for t in check_outputs[1]):
                hi_found = True
    assert hi_found
