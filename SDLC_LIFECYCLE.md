# Full-Fledge Autonomous SDLC Lifecycle

This environment implements a complete SDLC with autonomous fixing.

## Workflow Overview

1. **Ideation (Chat)**: Use `task_orchestrator.json`. Type a project idea.
2. **Planning**: AI breaks the idea into a list of file changes.
3. **Coding**: AI generates the code and writes it to `/data/project`.
4. **Verification**: `sdlc_main.json` runs automatically (or can be triggered) to perform polyglot tests and security audits.
5. **Deployment**: `infrastructure_deploy.json` ensures OpenTofu IaC is synced and applied to your environment.
6. **Monitoring**: `runtime_monitoring.json` tails your container logs.
7. **Fixing**: If a runtime error or code gap (TASK) is found, `autonomous_fixing.json` triggers a self-fixing loop with an AI Critic and automated rollback on test failure.
8. **Self-Healing**: If n8n itself fails, `self_fixing_routine.json` patches the workflow logic.
9. **Knowledge**: `knowledge_routine.json` maintains a daily log of lessons learned.

## Directory Structure
- `setup/`: Docker and environment configuration.
- `workflows/`: All n8n workflow JSON files for import.

## Stress & Reliability
- Includes AI Critic patterns for dual-LLM verification.
- Implements file-locking to prevent concurrent fix collisions.
- Automated rollback mechanism using Git.
