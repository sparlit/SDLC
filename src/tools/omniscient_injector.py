import json, os, sys, uuid

def clean_workflow_data(workflow):
    """
    Removes all 'Check:' and 'Omniscient Fix:' nodes and restores original functional connectivity.
    """
    nodes = workflow.get('nodes', [])
    connections = workflow.get('connections', {})

    # Identify non-injected functional nodes
    functional_nodes = [n for n in nodes if not (n['name'].startswith("Check:") or n['name'].startswith("Omniscient Fix:"))]
    functional_names = {n['name'] for n in functional_nodes}

    # Map Check nodes to their 'Success' (False) branches which contain original targets
    check_to_targets = {}
    for source, conn in connections.items():
        if source.startswith("Check:"):
            main = conn.get('main', [])
            if len(main) > 1:
                check_to_targets[source] = main[1]

    def resolve(targets, visited=None):
        if visited is None: visited = set()
        resolved = []
        for t in targets:
            tn = t['node']
            if tn in visited: continue
            visited.add(tn)
            if tn.startswith("Check:"):
                resolved.extend(resolve(check_to_targets.get(tn, []), visited))
            elif not tn.startswith("Omniscient Fix:"):
                resolved.append(t)
        return resolved

    new_connections = {}
    for fn in functional_names:
        if fn in connections:
            new_connections[fn] = {"main": [resolve(p) for p in connections[fn].get("main", [])]}

    workflow['nodes'] = functional_nodes
    workflow['connections'] = new_connections
    return workflow

def inject(filepath):
    fix_workflow_id = os.getenv("OMNISCIENT_FIX_WORKFLOW", "omniscient_error_orchestrator")
    try:
        with open(filepath, 'r') as f:
            workflow = json.load(f)
    except: return

    # Normalize: Remove previous injections and restore connectivity
    workflow = clean_workflow_data(workflow)
    nodes = workflow['nodes']
    conn = workflow['connections']

    # Node types that should not be wrapped in retries (triggers, entry points)
    skip = ['n8n-nodes-base.chatTrigger', 'n8n-nodes-base.scheduleTrigger', 'n8n-nodes-base.errorTrigger', 'n8n-nodes-base.executeWorkflowTrigger', 'n8n-nodes-base.webhook']

    new_nodes = nodes[:]
    new_connections = {}

    for node in nodes:
        node_name = node['name']
        orig_conn = conn.get(node_name, {})

        if node['type'] in skip:
            if orig_conn: new_connections[node_name] = orig_conn
            continue

        # Enable 'Continue On Fail' so the Check node can handle the error
        node['continueOnFail'] = True
        pos_x, pos_y = node['position']

        # Ports to wrap
        main_ports = orig_conn.get('main', [])
        if not main_ports: main_ports = [[]] # Wrap terminal nodes too

        new_outputs = []
        for i, targets in enumerate(main_ports):
            check_name = f"Check: {node_name} (P{i})"
            fix_name = f"Omniscient Fix: {node_name} (P{i})"

            check_node = {
                "parameters": {"conditions": {"boolean": [{"value1": f"={{ $node[\"{node_name}\"].error !== undefined }}", "value2": True}]}},
                "id": str(uuid.uuid4()), "name": check_name, "type": "n8n-nodes-base.if", "typeVersion": 1,
                "position": [pos_x + 200, pos_y + (i * 200) - 100]
            }
            fix_node = {
                "parameters": {"workflowId": fix_workflow_id, "options": {"waitForResults": True}},
                "id": str(uuid.uuid4()), "name": fix_name, "type": "n8n-nodes-base.executeWorkflow", "typeVersion": 1,
                "position": [pos_x + 400, pos_y + (i * 200)]
            }

            new_nodes.extend([check_node, fix_node])
            new_outputs.append([{"node": check_name, "type": "main", "index": 0}])

            new_connections[check_name] = {"main": [
                [{"node": fix_name, "type": "main", "index": 0}], # True = Error -> Fix
                targets                                         # False = Success -> Original
            ]}
            new_connections[fix_name] = {"main": [[{"node": node_name, "type": "main", "index": 0}]]}

        new_connections[node_name] = {"main": new_outputs}

    workflow.update({'nodes': new_nodes, 'connections': new_connections})
    with open(filepath, 'w') as f:
        json.dump(workflow, f, indent=2)

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "src/workflows"
    paths = [target] if os.path.isfile(target) else [os.path.join(target, f) for f in os.listdir(target) if f.endswith(".json") and f not in ["omniscient_error_orchestrator.json", "agent_workflow_fixer.json", "agent_operational_fixer.json", "agent_code_fixer.json"]]
    for p in paths:
        inject(p)
