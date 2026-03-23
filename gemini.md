# Minecraft AI Agents Project - Gemini Instructions

## Project Overview
This project focuses on creating AI agents for Minecraft using Python and Large Language Models (LLMs). The core premise of the architecture is the separation of **atomic abilities (`tools`)** written in Python and **complex strategies (`skills`)** defined as Markdown files. The bot connects to Minecraft using the `javascript` Python package wrapper around the Node.js `mineflayer` library.

## Architecture Guidelines
When assisting with this project, keep the following architecture in mind:

1. **`src/core/bot_client.py`:** Handles the pure Minecraft connection using `mineflayer`. Any low-level interaction with the Minecraft world should be routed through this layer.
2. **`src/core/brain.py`:** The LLM integration layer. This acts as the agent's brain, receiving observations and deciding which tool to call or what to say.
3. **`src/core/skill_loader.py`:** Parses and loads complex skills from Markdown files.
4. **`src/core/tool_registry.py`:** Registers Python functions (tools) into a JSON schema that the LLM can understand and invoke.
5. **`src/tools/`:** Contains atomic actions (e.g., `movement.py`). When adding a new capability, consider if it's an atomic action that belongs here. Tools should be simple, robust, and well-typed.
6. **`src/skills/`:** Contains Markdown files that instruct the AI on how to combine tools to achieve complex goals (e.g., "Build a house", "Mine diamonds").
7. **`mineCLIP/`:** Handles any embedding or vision/text inference using MineCLIP for the agent to understand the visual or semantic context of Minecraft.
8. **`_agents/`:** Contains the AI agent logging and Knowledge Base system. This directory is a standard Python package (importable via `from _agents.scripts.agent_logger import ...`). It houses:
   - `scripts/agent_logger.py`: The `AgentLogger` class and `run_with_logging()` convenience function.
   - `workflows/agent_logger.md`: Skill instructions for AI agents on how to use the logging system.
   - `logs/<source_name>/`: Auto-generated per-script run histories and troubleshooting registries.

## Development Rules for AI (Gemini)
- **Language:** The project primarily uses Python 3.10+. Code variables, classes, and methods should be in English. Project documentation (README) and logging prints (`main.py`) are mostly in Spanish. When writing console outputs, prefer Spanish to match the existing style, unless instructed otherwise.
- **Node.js Integration:** The project relies on the `javascript` library to execute Node.js `mineflayer` code directly from Python (`require('mineflayer')`). Do not attempt to use `mcpi` or other wrappers unless specifically asked.
- **Tools vs. Skills:** 
  - If the user asks to add a new *action* (e.g., "make the bot jump"), write a Python function in `src/tools/` and register it in `tool_registry`.
  - If the user asks to add a new *behavior* (e.g., "teach the bot how to survive the first night"), create a Markdown file in `src/skills/` explaining the steps and tools to use.
- **Testing:** Include tests in the `tests/` directory using pytest.
- **Error Handling:** Ensure robust error handling, especially for network connections (e.g., Minecraft server unavailability).

## Common Tasks 
- **Updating the Brain:** When modifying the prompt logic or LLM provider, update `brain.py`.
- **Modifying State:** The bot's world perception is handled in `perception.py`. If the agent needs to "see" more data (e.g., entities, inventory), update perception methods.
