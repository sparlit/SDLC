# Version: 1.1.0
# Version: 1.1.0
import json
import os
import sys

def visualize_workflows(workflow_dir):
    report = ["# IQ400 Workflow Dependency Map\n"]
    for f in os.listdir(workflow_dir):
        if f.endswith('.json'):
            path = os.path.join(workflow_dir, f)
            try:
                with open(path, 'r') as wf:
                    data = json.load(wf)
                name = data.get('name', f)
                nodes = data.get('nodes', [])
                connections = data.get('connections', {})

                report.append(f"## Workflow: {name}")
                report.append(f"- **Nodes**: {len(nodes)}")

                targets = []
                for node_name, conn_data in connections.items():
                    for main_out in conn_data.get('main', []):
                        for target in main_out:
                            targets.append(target.get('node'))

                report.append(f"- **Connections**: {', '.join(set(targets)) if targets else 'None'}\n")
            except Exception:
                pass
    return "\n".join(report)

if __name__ == "__main__":
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "src/workflows"
    print(visualize_workflows(target_dir))
