# Master SDLC Autonomous Workflow

The `master_orchestrator.json` is your single point of entry for the entire autonomous SDLC.

## Features
- **Project Ideation**: Triggered by chat. Break down ideas and implement files.
- **Continuous Fixing Loop**: Automatically scans for and resolves:
  - Bottlenecks, Dead ends, Loose ends, Loop holes, Blind spots.
  - Wrappers, Placeholders, Stubs, Empty wrappers.
  - TODO, FIXME, Build later, Fix later.
- **Autonomous Self-Healing**: Monitors its own execution and uses AI to patch its own n8n JSON if an error occurs.
- **Verification**: Automatically runs tests and audits after every fix.

## Setup
1. Import `master_orchestrator.json` into n8n.
2. Ensure `N8N_API_KEY` is set in your `.env`.
3. Set up the Chat Node in n8n to connect to this workflow.
