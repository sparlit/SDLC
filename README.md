# Autonomous SDLC Workflow with n8n

This project provides a complete autonomous Software Development Life Cycle (SDLC) setup using n8n, Docker, and AI (OpenRouter/Ollama).

## Features
- **Automated Testing Pipeline**: Polyglot detection (JS, Python, Go) and test execution.
- **AI Code Review**: Analyzes project structure and code for gaps using LLMs.
- **Autonomous Fixing Loop**: Automatically finds `TODO`s or placeholders, generates fixes with AI, applies them, and commits to Git.
- **Workflow Self-Fixing**: Monitors n8n execution logs and uses AI to fix its own logic if a node fails.
- **Infrastructure as Code**: Integrated OpenTofu (FOSS Terraform) for local/docker deployments.

## Prerequisites
- Docker & Docker Compose installed on Windows.
- OpenRouter API Key (for LLMs).
- Git repository initialized in `E:\myproject\SDLC`.

## Setup Instructions

1. **Environment Configuration**:
   - Navigate to the `setup` folder.
   - Copy `.env.example` to `.env`.
   - Update `OPENROUTER_API_KEY` and `PROJECT_PATH` (default is `E:/myproject/SDLC`).

2. **Start the Stack**:
   ```bash
   docker-compose up -d
   ```
   This will start n8n, PostgreSQL, and Ollama.

3. **Import Workflows**:
   - Open n8n at `http://localhost:5678`.
   - Go to **Workflows** > **Import from File**.
   - Import the files from the `workflows/` directory:
     - `sdlc_main.json`
     - `autonomous_fixing.json`
     - `self_fixing_routine.json`

4. **Configure n8n API**:
   - To enable the "Self-Fixing" routine, generate an API Key in n8n (Settings > API).
   - Update the `N8N_API_KEY` in your `.env` file.

5. **Local LLM (Optional)**:
   - To use Ollama for free local LLMs, the workflow is configured to talk to `http://ollama:11434`.
   - Run `docker exec -it ollama ollama run llama3` to download a model.

## Usage
- Open the **Chat Node** in the `sdlc_main` workflow.
- Type your project ideas or instructions.
- The workflow will scan your project, run tests, and provide an AI review.
- The autonomous loop will run periodically (or as configured) to fix code gaps.

## FOSS Tools Used
- **n8n**: Workflow automation.
- **OpenTofu**: Infrastructure as Code.
- **PostgreSQL**: Database.
- **Ollama**: Local LLM runner.
- **Git**: Version control.
