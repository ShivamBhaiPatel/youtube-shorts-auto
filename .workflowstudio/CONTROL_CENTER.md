# AI Control Center

This file is the central operating surface for the multi-agent workflow.
Any agent joining the repo should start here before doing work.

## Current Workflow Goal

Move work forward one task at a time with explicit ownership, explicit handoff, and no duplicated effort. The **Manager** handles routing — worker agents handle execution.

## Source Of Truth Files

Read these in order:
1. ai/CONTROL_CENTER.md
2. ai/AGENT_STATE.json
3. ai/PROJECT_CONTEXT.md
4. ai/TASK_QUEUE.md
5. ai/HANDOFF_LOG.md
6. ai/ASSIGNMENT_LOG.md
7. ai/CHANGE_TASK_LOG.md

## Current State

- Current owner: See ai/AGENT_STATE.json
- Active task: See ai/AGENT_STATE.json
- Next owner: See ai/AGENT_STATE.json
- Workflow phase: See ai/AGENT_STATE.json
- Last assignment decision: See ai/ASSIGNMENT_LOG.md (last entry)

## Universal Agent Rules

- Do not start broad repo work without reading the current state.
- Do not pick a different task unless the active task is blocked or complete.
- Do not overwrite another agent's work without documenting why.
- Update state before and after meaningful work.
- Leave a short handoff note when finishing a step.
- If you discover new work, add or refine tasks instead of hiding the complexity in the current task.
- **If you just completed a task:** the Manager should run next to assign the following task.

## Standard Flow

1. Read ai/AGENT_STATE.json.
2. If you are the **Manager**: scan the queue, assign the next task, log the decision, stop.
3. If you are a **worker agent**: work only on your assigned task.
4. If you are not the assigned owner: review the handoff or wait for the Manager to reassign.
5. After completing your step, update:
   - ai/AGENT_STATE.json
   - ai/TASK_QUEUE.md
   - ai/HANDOFF_LOG.md (worker agents) or ai/ASSIGNMENT_LOG.md (Manager)
6. Set the next owner clearly — or invoke the Manager to decide.

## Manager Invocation

Invoke the Manager (lightweight model: Haiku, GPT-4o-mini, Gemini Flash) after:
- A task is marked DONE or BLOCKED
- A new session begins and `active_task` is empty
- A Planner finishes restructuring the queue

Bootstrap prompt for Manager:
```
Read ai/CONTROL_CENTER.md and continue as Haiku-M1, the Manager agent.
```

## Completion Conditions For Any Step

Before handing off, record:
- what was inspected
- what was changed
- what was verified
- what remains risky
- who should act next (or: "invoke Manager to assign")

## Agent Naming Convention

All agents use worker-identity IDs: `{Model}-{RoleInitial}{Instance}`

| Role | Letter | Description | Suggested model |
|------|--------|-------------|----------------|
| Manager | M | Routing, assignment, queue monitoring | Haiku / Mini / Flash |
| Repo Analyst | R | Architecture, investigation, decomposition | Opus |
| Implementer | I | Precise implementation of bounded tasks | Codex |
| Refactorer | F | Refactors, module cleanup, structure improvements | Sonnet |
| Planner | P | Review, prioritization, synthesis, queue improvement | GPT |
| Validator | V | Validation, edge cases, test strategy, release risk | Gemini |

Rules:
- New instances increment: Codex-I2, Codex-I3, etc.
- Same session = same instance ID (even across multiple tasks).
- New session for same model+role = new instance number.
- Owner fields in TASK_QUEUE.md, HANDOFF_LOG.md, and CHANGE_TASK_LOG.md use instance IDs.
- The full registry lives in `ai/AGENT_STATE.json` under `agent_registry`.

## Handoff Format

Use this in ai/HANDOFF_LOG.md (worker agents only):

```
Date: YYYY-MM-DD
Task: TASK-XXX
From: Agent instance ID
To: Manager (or specific agent if known)
Status: READY | BLOCKED | NEEDS_REVIEW | DONE
Summary:
- item 1
Verification:
- item 1
Risks:
- item 1
Next action: one clear sentence
```

## Assignment Log Format

Use this in ai/ASSIGNMENT_LOG.md (Manager only):

```
---

Date: YYYY-MM-DD
Decision: ASSIGNED | HELD | FLAGGED | IDLE
Task: TASK-XXX
Assigned to: Agent-Instance-ID
Role: Role name
Reason: one sentence
Previous state: what workflow_status was before
Next action: Use "Start Active Task" in Workflow Studio to launch [agent] on [task]

---
```

## Important Constraint

This system centralizes coordination, but separate AI products still need one bootstrap instruction:

- **Worker agents:** `Read ai/CONTROL_CENTER.md and continue as the assigned agent.`
- **Manager:** `Read ai/CONTROL_CENTER.md and continue as Haiku-M1, the Manager agent.`
