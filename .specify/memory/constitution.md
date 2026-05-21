# IQ400 Constitution

## Core Principles

### I. Zero Stub Guarantee (NON-NEGOTIABLE)
Every line of code must be functional and purposeful. Source code shall never contain TODOs, FIXMEs, stubs, placeholders, or empty wrappers. All functions and classes must have complete implementations. The `super_scanner.py` utility is the final arbiter of this principle.

### II. Omniscient Self-Healing
The system is built on a self-healing foundation. Every n8n node and workflow component must be wrapped in retry logic that routes failures through the Omniscient AI Error Orchestrator. Errors are not failures; they are triggers for autonomous fixing.

### III. 100% FOSS & FOSS-First
All tools, dependencies, and infrastructure must be 100% Free and Open Source Software. OpenTofu is the standard for Infrastructure as Code (IaC). Proprietary black boxes are strictly prohibited.

### IV. Hierarchical Swarm Intelligence
Development and operations are orchestrated by a 6-layer fractal swarm (Models -> Orchestrators -> Teams -> Leaders -> Agents -> Sub-agents). All complex tasks must be debated and synthesized through the Swarm Engine to ensure robust outcomes.

### V. Deep Planning Mode
No execution without certainty. All tasks must start with a deep planning phase involving exhaustive questioning and assumption verification. A plan is only valid once it has been explicitly approved and recorded.

## Technical Constraints

### Architecture
- **Orchestration**: n8n workflows with `N8N_BLOCK_ENV_ACCESS_IN_EXPRESSIONS=false`.
- **Memory**: ChromaDB for persistent 'Omniscient' memory and debate caching.
- **Models**: Prioritize OpenRouter and FOSS model providers.
- **Verification**: Playwright for frontend, Pytest for backend and workflow structure.

### Autonomous Fixing
- Autonomous fixing workflows must trigger on a 30-minute interval.
- All code generation must include a sanitization step to blacklist dangerous shell commands.

## Development Workflow

### Step-by-Step
1. **Planning**: Use `/speckit.specify` and `/speckit.clarify` to define requirements.
2. **Design**: Use `/speckit.plan` to align with the Omniscient architecture.
3. **Tasking**: Use `/speckit.tasks` to generate actionable items.
4. **Execution**: Use `/speckit.implement` to build, ensuring the Zero Stub Guarantee.
5. **Verification**: Run `super_scanner.py` and `pytest` after every implementation.

## Governance
This Constitution supersedes all other practices and documentation. Any code that violates the Zero Stub Guarantee must be rejected or immediately fixed by the autonomous fixing swarm.

**Version**: 1.0.0 | **Ratified**: 2025-05-22 | **Last Amended**: 2025-05-22
