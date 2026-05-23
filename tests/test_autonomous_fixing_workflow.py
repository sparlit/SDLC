import json, os, pytest

WORKFLOW_PATH = os.path.join(os.path.dirname(__file__), "..", "src", "workflows", "autonomous_fixing.json")

@pytest.fixture
def workflow():
    with open(WORKFLOW_PATH) as f: return json.load(f)

def test_workflow_has_required_nodes(workflow):
    names = {n["name"] for n in workflow["nodes"]}
    required = {"Schedule Trigger", "Find Gaps/Placeholders", "AI Fix Generator", "Sanitize Fix", "Apply Fix", "Git Commit & Push"}
    for r in required: assert r in names

def test_workflow_connectivity(workflow):
    conn = workflow["connections"]
    pipeline = [("Schedule Trigger", "Find Gaps/Placeholders"), ("Find Gaps/Placeholders", "AI Fix Generator"),
                ("AI Fix Generator", "Sanitize Fix"), ("Sanitize Fix", "Apply Fix"), ("Apply Fix", "Git Commit & Push")]

    for src, dst in pipeline:
        found = False
        if src in conn:
            outputs = [t["node"] for port in conn[src].get("main", []) for t in port]
            if dst in outputs: found = True
            elif f"Check: {src} (P0)" in outputs:
                check_node = f"Check: {src} (P0)"
                check_outputs = conn.get(check_node, {}).get("main", [])
                if len(check_outputs) > 1 and any(t["node"] == dst for t in check_outputs[1]):
                    found = True
        
        # In case the source itself was renamed or the connection is indirect via another check
        if not found:
            for cname, cdata in conn.items():
                if cname.startswith("Check:"):
                    # Does this check point to dst?
                    main = cdata.get("main", [])
                    if len(main) > 1 and any(t["node"] == dst for t in main[1]):
                        # Does something else point to this check?
                        for sname, sdata in conn.items():
                            if any(t["node"] == cname for port in sdata.get("main", []) for t in port):
                                if sname == src: found = True
        
        assert found, f"Logic flow broken: {src} does not reach {dst}"
