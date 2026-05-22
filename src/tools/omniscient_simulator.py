import os
import sys
import json
import subprocess
import re
from typing import Dict, Any, List

class OmniscientSimulator:
    """
    Hybrid Simulation Environment for IQ400.
    Mocks production infrastructure (n8n, ChromaDB, APIs) while allowing
    real execution of safe logic upgrades.
    """
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.env_vars = {
            "OPENROUTER_API_KEY": "sk-mock-key",
            "PROJECT_PATH": project_root,
            "N8N_BLOCK_ENV_ACCESS_IN_EXPRESSIONS": "false"
        }
        self.mock_db = {} # Simulated ChromaDB
        self.execution_log = []

    def mock_openrouter(self, prompt: str) -> str:
        """Simulates LLM response for logic upgrades."""
        # Simple heuristic-based responses for common chaos injections
        if "pass" in prompt or "placeholder" in prompt:
            return "print('Autonomous fix: logic implemented')"
        if "TODO" in prompt:
            return "return 'Requirement satisfied'"
        return "print('Deep logic upgrade applied')"

    def run_command(self, cmd: str) -> Dict[str, Any]:
        """Safely executes a command in the simulation context."""
        # Sanitize command to stay within project root
        if "rm -rf /" in cmd or "mkfs" in cmd:
            return {"error": "CRITICAL: Dangerous command blocked by simulator"}

        # Replace absolute /data/project paths with local root
        cmd = cmd.replace("/data/project", self.project_root)

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exitCode": result.returncode
            }
        except Exception as e:
            return {"error": str(e)}

    def simulate_node(self, node_type: str, parameters: Dict[str, Any], input_data: Any) -> Dict[str, Any]:
        """Simulates n8n node behavior."""
        if node_type == "n8n-nodes-base.executeCommand":
            cmd = parameters.get("command", "")
            # Resolve expressions (very basic mock)
            if "{{" in cmd:
                cmd = re.sub(r'\{\{.*?\}\}', str(input_data), cmd)
            return self.run_command(cmd)

        elif node_type == "n8n-nodes-base.httpRequest":
            # Always return a success mock for OpenRouter
            return {
                "choices": [{
                    "message": {
                        "content": self.mock_openrouter(str(input_data))
                    }
                }]
            }

        elif node_type == "n8n-nodes-base.code":
            # Simulation for code nodes usually requires a JS engine,
            # here we mock the common behavior of extracting logic.
            return {"command": "print('Mocked JS logic execution')"}

        return {"status": "skipped", "message": f"Node type {node_type} not implemented in simulator"}

    def log_state(self, message: str):
        self.execution_log.append(f"[{os.getpid()}] {message}")

if __name__ == "__main__":
    # Test simulator
    sim = OmniscientSimulator(os.getcwd())
    res = sim.run_command("ls -l src/tools/super_scanner.py")
    print(json.dumps(res, indent=2))
