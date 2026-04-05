# Orchestration Guide

## Workflow Order

```
[Task completes or session starts]
          ↓
     Manager (M)           ← lightweight; reads state, assigns next task, logs decision
          ↓
  Worker agent runs        ← Repo Analyst / Implementer / Refactorer / Validator
          ↓
  [Task marked DONE/BLOCKED]
          ↓
     Manager (M)           ← re-invoked; picks up next task
          ↓
  Planner (P) [periodic]   ← every 2–3 completions; re-prioritize, split, merge tasks
          ↓
     Manager (M)           ← assigns tasks from the re-ordered queue
          ↓
        ...
```

### Standard cycle (one task):

1. **Manager** reads state → assigns next task → updates AGENT_STATE.json → logs to ASSIGNMENT_LOG.md
2. Human uses **"Start Active Task"** in Workflow Studio → bootstrap prompt copied to clipboard
3. **Worker agent** executes task → updates TASK_QUEUE.md + AGENT_STATE.json + HANDOFF_LOG.md
4. **Manager** re-invoked → assigns next task

---

## Role Boundaries

| Role | Does | Does NOT |
|------|------|----------|
| **Manager** | Reads state, assigns tasks, logs to ASSIGNMENT_LOG.md | Implement, review code, modify task content, write to HANDOFF_LOG.md |
| **Repo Analyst** | Reads code, produces analysis and task definitions | Implement anything |
| **Implementer** | Executes one task at a time | Pick unassigned work |
| **Refactorer** | Improves structure within task scope | Change behavior without authorization |
| **Planner** | Reviews, prioritizes, synthesizes | Implement unless explicitly asked |
| **Validator** | Tests, challenges, verifies | Fix — creates follow-up tasks instead |

---

## Handoff Rules

1. Every task transition updates AGENT_STATE.json, TASK_QUEUE.md, and HANDOFF_LOG.md.
2. After every task completion or blockage, invoke the Manager.
3. No agent works on a task outside its assigned scope.
4. Blocked tasks must be escalated with a clear reason, not silently skipped.
5. Follow-up work discovered during a task becomes a new task, not scope creep.
6. Manager logs routing decisions to ASSIGNMENT_LOG.md — never to HANDOFF_LOG.md.

---

## Queue Discipline

Good tasks are:
- **Atomic**: One clear outcome per task
- **Evidence-based**: Created from actual code analysis, not assumptions
- **Owned**: Assigned to a specific agent role
- **Bounded**: Completable in 30–120 minutes
- **Sequenced**: Dependencies are explicit

---

## Success Standard

Every agent should be able to answer these 4 questions at any time:
1. What is the current truth about this project?
2. What is the next task? ← Manager answers this
3. Who owns it? ← Manager answers this
4. What evidence defines done?
