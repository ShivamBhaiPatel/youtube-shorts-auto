# Change and Task Log

Purpose:
- Keep a durable, chronological record of important queue changes, task lifecycle changes, and coordination updates.
- Avoid losing context when TASK_QUEUE is rebaselined or archived.

Logging rules:
- Append newest entry at the top under "Latest Entries".
- One entry per meaningful workflow event.
- Include what changed, why, and impact on agent execution.

## Latest Entries

<!-- Entry format:

Date: YYYY-MM-DD
Actor: Agent-Instance-ID
Type: Task Update | Queue Change | State Change | Prompt Change | Validation
Summary:
- item 1
- item 2
Why:
- reason for change
Execution impact:
- effect on next agent actions

---

-->
