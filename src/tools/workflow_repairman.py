import json, os

REPAIRS = {
    "autonomous_fixing.json": [
        ("Schedule Trigger", "Find Gaps/Placeholders"),
        ("Find Gaps/Placeholders", "AI Fix Generator"),
        ("AI Fix Generator", "Sanitize Fix"),
        ("Sanitize Fix", "Apply Fix"),
        ("Apply Fix", "Git Commit & Push")
    ],
    "health_check.json": [
        ("Health Trigger", "Check Hardware"),
        ("Check Hardware", "Is Stable?"),
        ("Is Stable?", "Alert Notification", 1) # False branch (index 1)
    ],
    "sdlc_main.json": [
        ("Chat Trigger", "Scan Project Files"),
        ("Scan Project Files", "Polyglot Detection"),
        ("Polyglot Detection", "Is JS?"),
        ("Polyglot Detection", "Is Python?"),
        ("Is JS?", "NPM Test & Audit", 0), # True branch
        ("Is Python?", "Pytest & Bandit", 0), # True branch
        ("NPM Test & Audit", "AI SDLC Report"),
        ("Pytest & Bandit", "AI SDLC Report"),
        ("AI SDLC Report", "Trigger Infinite Cycle")
    ],
    "agent_executor.json": [
        ("Execute Workflow Trigger", "Encode Context"),
        ("Encode Context", "Execute Fractal Swarm"),
        ("Execute Fractal Swarm", "Check Swarm Error"),
        ("Check Swarm Error", "Omniscient Fix", 0), # True branch
        ("Check Swarm Error", "Format Output", 1), # False branch
        ("Omniscient Fix", "Execute Fractal Swarm")
    ]
}

def repair(filepath):
    fname = os.path.basename(filepath)
    if fname not in REPAIRS: return

    with open(filepath, 'r') as f: data = json.load(f)

    # Reset connections
    new_conn = {}
    nodes = {n['name']: n for n in data['nodes']}

    for repair_step in REPAIRS[fname]:
        src, dst = repair_step[0], repair_step[1]
        port_idx = repair_step[2] if len(repair_step) > 2 else 0

        if src not in nodes or dst not in nodes: continue

        if src not in new_conn: new_conn[src] = {"main": []}

        # Ensure we have enough ports
        while len(new_conn[src]["main"]) <= port_idx:
            new_conn[src]["main"].append([])

        new_conn[src]["main"][port_idx].append({"node": dst, "type": "main", "index": 0})

    data['connections'] = new_conn
    with open(filepath, 'w') as f: json.dump(data, f, indent=2)
    print(f"Repaired: {fname}")

if __name__ == "__main__":
    for f in os.listdir("src/workflows"):
        repair(os.path.join("src/workflows", f))
