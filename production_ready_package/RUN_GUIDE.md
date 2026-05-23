# IQ400 Omniscient Engine - Execution Guide

## 1. Environment Setup
- Install Docker and Docker-Compose.
- Create a `.env` file in the root based on `setup/.env.example`.
- Set `OPENROUTER_API_KEY` and `PROJECT_PATH` (local path to this repo).

## 2. Infrastructure Launch
```bash
cd src/infrastructure
docker-compose up -d --build
```

## 3. Workflow Initialization
Before importing workflows into n8n, run the Omniscient Injector to ensure self-healing capabilities are active:
```bash
python3 src/tools/omniscient_injector.py src/workflows
```

## 4. n8n Import
- Access n8n at `http://localhost:5678`.
- Import all JSON files from `src/workflows/`.
- **Note**: The `sdlc_main.json` is the entry point orchestrator.

## 5. Running a Cycle
1. Open the **SDLC Main Workflow** in n8n.
2. Click **Execute Workflow**.
3. Monitor the **SDLC Dashboard** (`sdlc_dashboard.json`) for real-time progress.

## 6. Maintenance
- To reset workflows to their base state: `python3 src/tools/workflow_cleaner.py src/workflows`.
- Gaps are autonomously filled every 30 minutes via `autonomous_fixing.json`.
