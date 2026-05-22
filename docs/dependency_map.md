<!-- Version: 1.1.0 -->
# IQ400 Workflow Dependency Map

## Workflow: RAG Context Indexer
- **Nodes**: 3
- **Connections**: read-files, chroma-upsert

## Workflow: Self-Optimizing Infrastructure
- **Nodes**: 3
- **Connections**: get-resource-usage, ai-optimizer

## Workflow: Stress Test Orchestrator
- **Nodes**: 3
- **Connections**: log-performance, run-stress-test

## Workflow: Full Evolution Engine
- **Nodes**: 4
- **Connections**: ai-evolve-arch, update-arch, read-all-context

## Workflow: Agentic Debate Routine
- **Nodes**: 2
- **Connections**: agent-finalizer

## Workflow: Neural Architecture Optimizer
- **Nodes**: 3
- **Connections**: arch-optimizer, legacy-scan

## Workflow: Autonomous API Documentation
- **Nodes**: 4
- **Connections**: list-files, ai-doc-generator, save-docs

## Workflow: SDLC Main Workflow
- **Nodes**: 8
- **Connections**: Scan Project Files, ai-sdlc-report, is-python, pytest-bandit, npm-test-audit, is-javascript, Polyglot Detection

## Workflow: SDLC Task Orchestrator
- **Nodes**: 6
- **Connections**: AI Planner, ai-coder, Extract Code, Write File, Parse Plan

## Workflow: Prompt Self-Evolution Routine
- **Nodes**: 4
- **Connections**: ai-evolve-prompts, read-logs, update-prompts-file

## Workflow: FOSS Contributor (Bug Bounty)
- **Nodes**: 3
- **Connections**: scan-external, generate-contribution

## Workflow: Infrastructure & Deployment Routine
- **Nodes**: 6
- **Connections**: Check TF Files, Write TF File, has-tf, OpenTofu Apply, AI TF Generator

## Workflow: Proactive Maintenance Engine
- **Nodes**: 3
- **Connections**: proactive-fixer, risk-analysis

## Workflow: SDLC Health Dashboard
- **Nodes**: 4
- **Connections**: save-dashboard, generate-html, fetch-metrics

## Workflow: Multi-threaded Project Refactor
- **Nodes**: 5
- **Connections**: list-chunks, process-chunks-parallel, chunk-project, refactor-logic

## Workflow: IQ200 Unified SDLC Brain
- **Nodes**: 3
- **Connections**: safety-check, scout-analyze

## Workflow: Runtime Monitoring & Fixing
- **Nodes**: 4
- **Connections**: trigger-fix-loop, get-runtime-faults, has-fault

## Workflow: Hardware Health Check
- **Nodes**: 4
- **Connections**: check-hardware, is-stable, alert-notification

## Workflow: Voice-to-SDLC Trigger
- **Nodes**: 3
- **Connections**: whisper-transcribe, trigger-brain

## Workflow: Advanced SDLC Security & Complexity Audit
- **Nodes**: 4
- **Connections**: ai-audit-report, semgrep-scan, radon-complexity

## Workflow: Multi-Agent Swarm Coordinator
- **Nodes**: 3
- **Connections**: spawn-swarm, execute-agent

## Workflow: Autonomous Security Patching
- **Nodes**: 4
- **Connections**: trivy-scan, apply-patch, ai-security-fixer

## Workflow: Ultimate Master SDLC Orchestrator
- **Nodes**: 3
- **Connections**: Get Arch Rules, Orchestrator Planning

## Workflow: Autonomous Fixing Loop
- **Nodes**: 10
- **Connections**: git-commit-push, sanitize-fix, ai-fix-generator, is-fix?, fix-failed-notification, ai-feature-suggester, apply-fix, find-discontinuitys, decide-action

## Workflow: Staging & Promotion Routine
- **Nodes**: 4
- **Connections**: staging-passed, promote-to-prod, verify-staging

## Workflow: Knowledge & Documentation Routine
- **Nodes**: 4
- **Connections**: ai-summarizer, update-docs, get-changes

## Workflow: Workflow Self-Fixing Routine
- **Nodes**: 5
- **Connections**: parse-workflow-fix, get-workflow-json, update-workflow, ai-workflow-fixer
