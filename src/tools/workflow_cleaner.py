import json, os, sys

def clean_workflow(workflow):
    nodes = workflow.get('nodes', [])
    connections = workflow.get('connections', {})

    # 1. Identify functional nodes (ignore our Check/Fix nodes)
    functional_nodes = [n for n in nodes if not (n['name'].startswith("Check:") or n['name'].startswith("Omniscient Fix:"))]
    functional_names = {n['name'] for n in functional_nodes}

    # 2. Extract original targets from Check nodes' False branches (index 1)
    # n8n connection format: source_node -> port_type -> [port_index] -> [targets]
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
            elif tn in functional_names:
                resolved.append(t)
        return resolved

    # 3. Rebuild connections for functional nodes
    new_connections = {}
    for fn in functional_names:
        if fn in connections:
            new_connections[fn] = {"main": [resolve(p) for p in connections[fn].get("main", [])]}

    workflow['nodes'] = functional_nodes
    workflow['connections'] = new_connections
    return workflow

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "src/workflows"
    paths = [target] if os.path.isfile(target) else [os.path.join(target, f) for f in os.listdir(target) if f.endswith(".json")]
    for p in paths:
        try:
            with open(p, 'r') as f: data = json.load(f)
            cleaned = clean_workflow(data)
            with open(p, 'w') as f: json.dump(cleaned, f, indent=2)
            print(f"Cleaned: {p}")
        except Exception as e: print(f"Error {p}: {e}")
