# IQ300 Ultimate Autonomous SDLC Engine

## 🚀 About the Project
The **IQ300 Engine** is a state-of-the-art, 100% FOSS autonomous Software Development Life Cycle (SDLC) system built on n8n. It is designed to transform high-level project ideas into production-ready applications with zero human intervention in the middle, while maintaining absolute security and architectural integrity.

It employs a **Adversarial Multi-Agent Architecture**:
- **Scouts**: Deep AST-based scanners that find gaps and stubs.
- **Devils**: Adversarial AI agents that critique and harden code proposals.
- **Architects**: Master implementers that write code and synthesize unit tests.

## 🛠 Specifications
- **Core Engine**: n8n (Production-hardened)
- **Database**: PostgreSQL 16 (Workflow persistence)
- **Context Engine**: ChromaDB (Vector store for long-term memory)
- **Security Suite**: Trivy, Semgrep, Bandit, Scancode
- **Quality Suite**: Radon, Pytest, Jest
- **IaC Engine**: OpenTofu (FOSS Terraform)
- **Observability**: Grafana & Prometheus
- **AI Processing**: OpenRouter (Primary) & Local Whisper (Voice)

## 📖 Detailed 'How To'

### 1. Installation (Windows Laptop)
1. Ensure **Docker Desktop** is installed and running.
2. Clone this repository to `E:\myproject\SDLC`.
3. Navigate to `src/infrastructure`.
4. Run the build and start command:
   ```bash
   docker-compose up -d --build
   ```

### 2. Configuration
1. Open n8n at `http://localhost:5678`.
2. Generate an **API Key** in Settings.
3. Create a `.env` file in `src/infrastructure` with:
   - `OPENROUTER_API_KEY`: Your key.
   - `N8N_API_KEY`: The key you just generated.
   - `PROJECT_PATH`: `E:/myproject/SDLC`

### 3. Importing Workflows
- Go to n8n > Workflows > Import from File.
- Import all `.json` files from `src/workflows/`.
- **Crucial**: Ensure the `god_mode_orchestrator` is active and connected to your Chat Node.

### 4. Usage
- **Text Mode**: Open the Chat interface in n8n and type: *"Create a new microservice for user auth."*
- **Voice Mode**: Send a `.wav` file to the `voice-trigger` webhook path.
- **Autonomous Fixing**: Simply let the system run. It will periodically scan your code and fix placeholders or security gaps automatically.

### 5. Monitoring
- Access the **Real-time Dashboard** at `http://localhost:3000` (Grafana).
- Default credentials: `admin/admin`.

## 📜 Compliance & Safety
- **100% FOSS**: Every tool used is open-source.
- **Zero Stub Policy**: The system is programmed to never leave "TODO" or "Fix Later" markers in your source code.
- **Atomic Locking**: Uses `state_manager.py` to prevent data corruption during parallel multi-threaded operations.
