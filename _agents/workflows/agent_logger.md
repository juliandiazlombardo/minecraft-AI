---
description: How to use the AgentLogger and Knowledge Base for tracing errors and maintaining run history
---

# Agent Logger and Knowledge Base Skill

You have access to a robust logging and troubleshooting system built specifically for AI agents running in this project. The system automatically records your runs, logs errors, and maintains an up-to-date Knowledge Base of bugs and their fixed statuses.

## Your Responsibilities

As an AI Agent operating in this codebase, you **must**:
1. **Initialize the logger** in any file you are running/testing.
2. **Log your runs** whenever you take major actions or make requests.
3. **Log unknown errors** when you hit a bug.
4. **Query the Knowledge Base** when you see an error to check if you or someone else has solved it before.
5. **Update the Knowledge Base** when you believe you have successfully fixed an error.

## 1. Initializing the System (Quickest Way)

Use the `run_with_logging()` wrapper — it handles initialization, start logging, and error catching in one call:

```python
if __name__ == "__main__":
    from _agents.scripts.agent_logger import run_with_logging
    run_with_logging(__file__, main)
```

That's it. If `main()` crashes, the full traceback is automatically saved to the Knowledge Base.

> [!NOTE]
> This creates a `_agents/logs/<your_file_name>/` folder at the project root to cleanly separate runs and Knowledge Bases per script.

## 1b. Manual Initialization (For More Control)

If you need direct access to the logger instance (e.g. to log intermediate steps):

```python
if __name__ == "__main__":
    from _agents.scripts.agent_logger import setup_logger

    logger = setup_logger(__file__)
    logger.log_run({"action": "started script"})

    try:
        main()
    except BaseException as e:
        import traceback
        logger.log_error(traceback.format_exc(), context="Running main")
        raise
```

## 2. Tracking Your Runs

Whenever you perform a significant step, use `log_run()` to track your context.

```python
logger.log_run({
    "action": "Attempting to connect to the Minecraft server",
    "target_ip": "127.0.0.1",
    "status": "pending"
})
```

## 3. Encountering Errors and The Registry

If an operation fails, use `log_error()`. This automatically adds it to the Troubleshooting Registry with a Certainty Score of 0.

```python
try:
    pass  # your failing code
except Exception as e:
    logger.log_error(str(e), context="Attempting server connection")
```

## 4. Querying the Knowledge Base

Before spending time fixing a bug, query the registry to see if a solution already exists.

```python
known_issues = logger.query_knowledge_base("ConnectionRefusedError")

for symptom, data in known_issues.items():
    print(f"Known Issue: {symptom}")
    print(f"Cause: {data['root_cause']}")
    print(f"Solution: {data['solution_steps']}")
    print(f"Certainty Score: {data['certainty_score']}")
```

## 5. Updating the Certainty Score

- **0**: Unfixed / Reoccurring Bug
- **1**: The agent believes the bug has been fixed.
- **2**: The human confirms the bug is fixed.

```python
logger.update_knowledge_base(
    symptom="ConnectionRefusedError: [Errno 111] Connection refused",
    root_cause="The local server port was blocked by a dangling process.",
    solution_steps="Killed the dangling java process using `pkill java` and restarted.",
    certainty_score=1
)
```

> [!CAUTION]
> As an AI Agent, you may only ever assign a `certainty_score` of `0` or `1`. Only a human user can assign a score of `2`.

## 6. Interpreting Tracebacks

When the registry contains entries tagged `[TRACEBACK - agent review pending]`, you **must** read the full traceback from `_agents/logs/<source>/runs_summary.md` and interpret it yourself to determine the root cause.
