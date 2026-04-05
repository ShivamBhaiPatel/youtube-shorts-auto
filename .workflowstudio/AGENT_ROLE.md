# Agent Roles

## Core Principle

One agent owns analysis and task creation at a time. All other agents consume the task queue and work on narrowly scoped execution, review, or validation. The **Manager** coordinates routing between them — it is the traffic controller, not a worker.

## Shared Rules for All Agents

1. Read the current state before starting any work.
2. Do not invent new architecture — work within the existing structure.
3. Prefer small, verifiable tasks over large, ambitious rewrites.
4. Keep handoffs explicit — document what changed, what was verified, what's risky.
5. Do not overwrite another agent's work without documenting why.
6. Update coordination files (AGENT_STATE.json, TASK_QUEUE.md, HANDOFF_LOG.md) after every meaningful step.
7. If blocked, escalate clearly rather than working around the issue silently.

## Agent Roster

- **Manager (M)**: Lightweight traffic controller. Reads queue state after every task completion and assigns the next task to the correct agent. Uses a fast, cheap model (Haiku, Mini, Flash). Does NOT implement or review code.
- **Repo Analyst (R)**: Repository analysis, architecture review, task decomposition
- **Implementer (I)**: Precise implementation of bounded, approved tasks
- **Refactorer (F)**: Structural improvements, module cleanup, code organization
- **Planner (P)**: Review, prioritization, synthesis, queue optimization
- **Validator (V)**: Quality assurance, edge case analysis, test strategy

## Agent Naming Convention

```
{Model}-{RoleInitial}{Instance}
```

| Role | Letter | Suggested model | Example |
|------|--------|----------------|---------|
| Manager | M | Haiku / Mini / Flash | Haiku-M1 |
| Repo Analyst | R | Opus | Opus-R1 |
| Implementer | I | Codex | Codex-I1 |
| Refactorer | F | Sonnet | Sonnet-F1 |
| Planner | P | ChatGPT | GPT-P1 |
| Validator | V | Gemini | Gemini-V1 |

## Shared File Contract

All agents read these files:
- `ai/PROJECT_CONTEXT.md` — project background and technical context
- `ai/TASK_QUEUE.md` — the active work queue
- `ai/AGENT_STATE.json` — workflow state and agent registry
- `ai/prompts/` — role-specific behavior prompts

Write permissions:
- `ai/HANDOFF_LOG.md` — worker agents only (append-only; Manager does NOT write here)
- `ai/ASSIGNMENT_LOG.md` — Manager only (append-only)

## Workflow Order

```
[Task completes / session starts]
        ↓
    Manager (M)      ← reads state, assigns next task
        ↓
  Worker agent       ← Repo Analyst / Implementer / Refactorer / Validator
        ↓
  Planner (P)        ← every 2–3 completions, re-prioritize queue
        ↓
    Manager (M)      ← next assignment
        ↓
       ...
```
