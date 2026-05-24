# 🌌 IQ400 'Omniscient' Zenith - Step-by-Step Usage Guide

Welcome to the definitive guide for operating the IQ400 'Omniscient' Zenith engine. This guide will walk you through setting up the environment, launching the autonomous SDLC infrastructure, and executing your first AI-driven development cycle.

---

## ⚡ Quick Start (Single Command)

If you want to get up and running immediately with default settings:

```bash
chmod +x bootstrap.sh
./bootstrap.sh
```

This script will:
1. Create your `.env` file and initialize `PROJECT_PATH`.
2. Install necessary Python dependencies.
3. Inject self-healing logic into all workflows.
4. Launch the entire Docker infrastructure.
5. **Autonomously import** all workflows into your n8n instance.

*Note: You will still need to manually add your `OPENROUTER_API_KEY` to the `.env` file after the script runs.*

---

## 📋 0. Prerequisites

Before starting, ensure your system meets these requirements:
- **Docker & Docker Compose**: V2 recommended.
- **Python 3.10+**: For running local utility scripts.
- **OpenRouter API Key**: Obtain one from [openrouter.ai](https://openrouter.ai/).
- **RAM**: Minimum 16GB (32GB+ recommended for full swarm scaling).

---

## 🛠️ Step 1: Environment Configuration

1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd SDLC
   ```

2. **Initialize Environment Variables**:
   Copy the example environment file and edit it:
   ```bash
   cp setup/.env.example .env
   ```
   Open `.env` and fill in the following:
   - `OPENROUTER_API_KEY`: Your OpenRouter key.
   - `PROJECT_PATH`: The **absolute path** to the `/data/project` folder where the AI will write code (e.g., `/home/user/SDLC/project_data`).
   - `N8N_API_KEY`: You can generate this later in n8n (User Settings > Personal API Keys).

---

## 🚀 Step 2: Infrastructure Launch

Launch the core services (PostgreSQL, Redis, ChromaDB, Gitea, Grafana, and n8n):

```bash
cd src/infrastructure
docker-compose up -d --build
```

Verify that all containers are running:
```bash
docker ps
```

---

## 💉 Step 3: Workflow Injection & Import

The "Omniscient" capability requires wrapping standard workflows with self-healing logic.

1. **Inject Self-Healing Logic**:
   Run the injector tool on the workflow directory:
   ```bash
   python3 src/tools/omniscient_injector.py src/workflows
   ```
   *Note: This adds "Check" and "Fix" nodes to every functional step.*

2. **Import into n8n**:
   - Access n8n at `http://localhost:5678`.
   - Go to **Settings > Import from File**.
   - Select all JSON files in `src/workflows/`.
   - **Important**: Open `sdlc_main.json` and `autonomous_fixing.json` and ensure they are toggled to **Active**.

---

## 🏗️ Step 4: Your First Autonomous Project

Now that the engine is running, let's build something.

1. **Trigger the Orchestrator**:
   - Open the **SDLC Task Orchestrator** (`task_orchestrator.json`) in n8n.
   - Click **Execute Workflow**.
   - When prompted in the Chat Trigger (if using the UI), enter your project idea (e.g., *"Build a Python Flask API with a single endpoint /health that returns JSON status OK"*).

2. **The Autonomous Loop**:
   - **AI Planner**: Breaks your idea into a file list.
   - **AI Coder**: Writes the functional code.
   - **Verification**: `sdlc_main` will trigger to run `pytest` and `bandit` security scans.

3. **Check the Output**:
   The code will be generated in the path you specified in `PROJECT_PATH` in your `.env`.

---

## 🔍 Step 5: Monitoring & Self-Healing

### Real-time Monitoring
Start the **Watcher** to monitor your project for technical debt or logic gaps:
```bash
python3 src/tools/watcher.py
```
If you manually add a `# TODO` or a `pass` statement to any `.py` file in `src/`, the Watcher will detect it and trigger a **Fractal Swarm** to fix it immediately.

### Performance Dashboard
Access the **SDLC Dashboard** workflow in n8n to see a visual representation of successful vs. failed fixes and system health.

---

## 🧹 Maintenance & Reset

- **Reset Workflows**: To remove the "Omniscient" wrappers and go back to base workflows:
  ```bash
  python3 src/tools/workflow_cleaner.py src/workflows
  ```
- **Stress Testing**: To verify the engine's reliability under pressure:
  ```bash
  python3 src/tools/omniscient_stress_tester.py 10
  ```

---

## 🎯 Summary of Key Workflows

| Workflow | Purpose |
| :--- | :--- |
| `sdlc_main.json` | Coordinates the full end-to-end lifecycle. |
| `task_orchestrator.json` | Entry point for new project ideas. |
| `autonomous_fixing.json` | The self-healing logic that repairs failed steps. |
| `runtime_monitoring.json` | Monitors container logs for production errors. |

**Congratulations!** You are now operating the world's most advanced autonomous SDLC engine.
