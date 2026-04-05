# Start Here

This is the entry point for any AI agent joining this project.

## Bootstrap Instruction

Read ai/CONTROL_CENTER.md and continue as the assigned agent.

## What You Should Do

1. Read ai/CONTROL_CENTER.md for workflow rules
2. Read ai/AGENT_STATE.json for current state and your assignment
3. Read ai/PROJECT_CONTEXT.md for project background
4. Read ai/TASK_QUEUE.md for your active task
5. Read ai/HANDOFF_LOG.md for recent handoff context
6. Read your role prompt from ai/prompts/

## Role Prompt Map

See `role_prompt_map` in ai/AGENT_STATE.json for the mapping of roles to prompt files.

## Minimal Human Input Pattern

To activate any agent, paste one of these:

- "Read ai/CONTROL_CENTER.md, you are the Implementer, continue."
- "Read ai/CONTROL_CENTER.md, you are the Repo Analyst, continue."
- "Read ai/CONTROL_CENTER.md, you are the Validator, continue."

## Note

A fully automatic multi-model relay requires an external orchestrator.
Inside the repo, this file system is the central shared brain.
