import json
import os
import sys
import uuid

def inject_omniscient_logic(filepath):
    with open(filepath, 'r') as f:
        workflow = json.load(f)

    nodes = workflow.get('nodes', [])
    connections = workflow.get('connections', {})

    new_nodes = []
    new_connections = {}

    # Filter out nodes we don't want to wrap
    skip_types = [
        'n8n-nodes-base.chatTrigger',
        'n8n-nodes-base.scheduleTrigger',
        'n8n-nodes-base.errorTrigger',
        'n8n-nodes-base.executeWorkflowTrigger',
        'n8n-nodes-base.webhook'
    ]

    # First, collect all original nodes
    original_nodes = []
    for node in nodes:
        # Don't re-wrap if already wrapped
        if "Check: " in node['name'] or "Omniscient Fix: " in node['name']:
            continue
        original_nodes.append(node)

    for node in original_nodes:
        node_name = node['name']
        node_id = node.get('id', str(uuid.uuid4()))
        node['id'] = node_id # Ensure it has an ID
        new_nodes.append(node)

        # Get connections for this node
        orig_conn = connections.get(node_name) or (connections.get(node_id) if node_id else None)

        if node['type'] in skip_types:
            if orig_conn:
                new_connections[node_name] = orig_conn
            continue

        # 1. Enable continueOnFail
        node['continueOnFail'] = True

        # 2. Create Check Node (IF node)
        check_node_name = f"Check: {node_name}"
        check_node_id = f"check-{node_id}"
        check_node = {
            "parameters": {
                "conditions": {
                    "boolean": [
                        {
                            "value1": f"={{{{ $node[\"{node_name}\"].error !== undefined }}}}}}",
                            "value2": True
                        }
                    ]
                }
            },
            "id": check_node_id,
            "name": check_node_name,
            "type": "n8n-nodes-base.if",
            "typeVersion": 1,
            "position": [node['position'][0] + 150, node['position'][1] + 50]
        }
        # FIX: The expression in the condition was wrong in the review, but wait.
        # n8n uses {{ }} for expressions. If I want literal {{ }}, I might need to escape.
        # Let's use a simpler expression that is valid n8n.
        check_node["parameters"]["conditions"]["boolean"][0]["value1"] = f"={{ $node[\"{node_name}\"].error !== undefined }}"

        new_nodes.append(check_node)

        # 3. Create Fixer Node (Execute Workflow)
        fix_node_name = f"Omniscient Fix: {node_name}"
        fix_node_id = f"fix-{node_id}"
        fix_node = {
            "parameters": {
                "workflowId": "omniscient_error_orchestrator",
                "options": {
                    "waitForResults": True
                }
            },
            "id": fix_node_id,
            "name": fix_node_name,
            "type": "n8n-nodes-base.executeWorkflow",
            "typeVersion": 1,
            "position": [node['position'][0] + 150, node['position'][1] + 150]
        }
        new_nodes.append(fix_node)

        # 4. Rewire Connections
        # Node A -> Check Node
        new_connections[node_name] = {
            "main": [[{"node": check_node_name, "type": "main", "index": 0}]]
        }

        # Check Node:
        # Index 0 (True) -> Fixer (Error case)
        # Index 1 (False) -> Original Targets (Success case)
        error_path = [{"node": fix_node_name, "type": "main", "index": 0}]

        # Handle ALL original output branches
        success_paths = []
        if orig_conn and "main" in orig_conn:
            success_paths = orig_conn["main"]
        else:
            success_paths = [[]]

        new_connections[check_node_name] = {
            "main": [
                error_path,
                *success_paths
            ]
        }

        # Fix Node -> Node A (Retry Loop)
        new_connections[fix_node_name] = {
            "main": [[{"node": node_name, "type": "main", "index": 0}]]
        }

    workflow['nodes'] = new_nodes
    workflow['connections'] = new_connections

    with open(filepath, 'w') as f:
        json.dump(workflow, f, indent=2)
    print(f"Injected Omniscient logic into {filepath}")

if __name__ == "__main__":
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "src/workflows"
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
