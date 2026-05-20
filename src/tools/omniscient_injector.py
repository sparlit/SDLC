import json
import os
import sys
import uuid

def inject_omniscient_logic(filepath):
    with open(filepath, 'r') as f:
        try:
            workflow = json.load(f)
        except:
            return

    nodes = workflow.get('nodes', [])
    connections = workflow.get('connections', {})

    # Filter for original nodes only to avoid double injection
    original_nodes = [n for n in nodes if not (n['name'].startswith("Check:") or n['name'].startswith("Omniscient Fix:"))]

    skip_types = [
        'n8n-nodes-base.chatTrigger',
        'n8n-nodes-base.scheduleTrigger',
        'n8n-nodes-base.errorTrigger',
        'n8n-nodes-base.executeWorkflowTrigger',
        'n8n-nodes-base.webhook'
    ]

    new_nodes = original_nodes[:]
    new_connections = {}

    for node in original_nodes:
        node_name = node['name']
        orig_conn = connections.get(node_name, {})

        # If it's a trigger, just keep original connections
        if node['type'] in skip_types:
            if orig_conn:
                new_connections[node_name] = orig_conn
            continue

        # Enable continue on fail for the node itself
        node['continueOnFail'] = True

        pos_x, pos_y = node['position']

        # We wrap each main output port
        main_ports = orig_conn.get('main', [[]])
        new_main_ports = []

        for i, targets in enumerate(main_ports):
            # If no targets on this port, just add an empty list
            if not targets:
                new_main_ports.append([])
                continue

            unique_id = f"{node_name[:10]}-{i}-{str(uuid.uuid4())[:4]}"
            check_name = f"Check: {unique_id}"
            fix_name = f"Omniscient Fix: {unique_id}"

            check_node = {
                "parameters": {
                    "conditions": {
                        "boolean": [
                            {
                                "value1": f"={{ $node[\"{node_name}\"].error !== undefined }}",
                                "value2": True
                            }
                        ]
                    }
                },
                "id": str(uuid.uuid4()),
                "name": check_name,
                "type": "n8n-nodes-base.if",
                "typeVersion": 1,
                "position": [pos_x + 200, pos_y + (i * 100) - 50]
            }

            fix_node = {
                "parameters": {
                    "workflowId": "omniscient_error_orchestrator",
                    "options": {
                        "waitForResults": True
                    }
                },
                "id": str(uuid.uuid4()),
                "name": fix_name,
                "type": "n8n-nodes-base.executeWorkflow",
                "typeVersion": 1,
                "position": [pos_x + 400, pos_y + (i * 100)]
            }

            new_nodes.append(check_node)
            new_nodes.append(fix_node)

            # Port i of source node now points to this Check node
            new_main_ports.append([{"node": check_name, "type": "main", "index": 0}])

            # Check node logic:
            # Output 0 (True) -> Error -> Go to Fixer
            # Output 1 (False) -> Success -> Go to Original Targets
            new_connections[check_name] = {
                "main": [
                    [{"node": fix_name, "type": "main", "index": 0}], # Port 0: True
                    targets # Port 1: False
                ]
            }

            # Fixer node loops back to Source node for retry
            new_connections[fix_name] = {
                "main": [[{"node": node_name, "type": "main", "index": 0}]]
            }

        new_connections[node_name] = {"main": new_main_ports}

    workflow['nodes'] = new_nodes
    workflow['connections'] = new_connections

    with open(filepath, 'w') as f:
        json.dump(workflow, f, indent=2)
    print(f"Omnisciently upgraded: {filepath}")

if __name__ == "__main__":
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "src/workflows"
    if os.path.isfile(target_dir):
        inject_omniscient_logic(target_dir)
    else:
        for filename in os.listdir(target_dir):
            if filename.endswith(".json") and filename not in [
                "omniscient_error_orchestrator.json",
                "agent_workflow_fixer.json",
                "agent_operational_fixer.json",
                "agent_code_fixer.json"
            ]:
                try:
                    inject_omniscient_logic(os.path.join(target_dir, filename))
                except Exception as e:
                    print(f"Failed to process {filename}: {e}")
