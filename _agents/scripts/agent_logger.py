import json
import logging
import os
from pathlib import Path
from datetime import datetime


class AgentLogger:
    def __init__(self, source_name: str = "main"):
        """
        Initializes the logger and registry system inside a `_agents/logs/` folder 
        at the root of the project, scoped to the specific `source_name`.
        """
        # Determine the root directory of the project 
        # (Assuming .agents/scripts/agent_logger.py format)
        try:
            current_dir = Path(__file__).resolve().parent
            # Navigate up from _agents/scripts to root
            self.root_dir = current_dir.parent.parent
        except NameError:
            self.root_dir = Path.cwd()

        # Sanitize the source_name for folder paths
        safe_source_name = Path(source_name).stem if source_name else "main"
        
        # Dedicated log directory per source inside _agents/logs/
        self.log_dir = self.root_dir / "_agents" / "logs" / safe_source_name
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # File paths
        self.runs_jsonl_path = self.log_dir / "runs.jsonl"
        self.runs_md_path = self.log_dir / "runs_summary.md"
        self.registry_json_path = self.log_dir / "troubleshooting_registry.json"
        self.registry_md_path = self.log_dir / "troubleshooting_registry.md"

        # Standard python logger setup
        self.logger = logging.getLogger(f"AgentLogger_{safe_source_name}")
        self.logger.setLevel(logging.INFO)
        
        # Prevent adding multiple handlers if instantiated multiple times
        if not self.logger.handlers:
            ch = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

    def log_run(self, run_details: dict):
        """
        Logs a general run event or action taken by the agent.
        Appends to both a pure JSONL file and a human-readable Markdown file.
        """
        timestamp = datetime.now().isoformat()
        entry = {
            "timestamp": timestamp,
            "run_details": run_details
        }

        # 1. Update JSONL
        with open(self.runs_jsonl_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

        # 2. Update Markdown Summary
        md_entry = f"### Run: {timestamp}\n"
        for k, v in run_details.items():
            md_entry += f"- **{k}**: {v}\n"
        md_entry += "\n---\n"
        
        with open(self.runs_md_path, "a", encoding="utf-8") as f:
            if os.path.getsize(self.runs_md_path) == 0:
                f.write("# Agent Run Summary\n\n")
            f.write(md_entry)
            
        self.logger.info(f"Logged run: {run_details.get('action', 'General Event')}")

    def _load_registry(self) -> dict:
        """Helper to load the current JSON registry."""
        if not self.registry_json_path.exists():
            return {}
        try:
            with open(self.registry_json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}

    def _save_registry(self, registry_data: dict):
        """Helper to save to JSON and subsequently export to the Markdown table."""
        # Save JSON
        with open(self.registry_json_path, "w", encoding="utf-8") as f:
            json.dump(registry_data, f, indent=4)
            
        # Export Markdown Table
        self._export_registry_to_md(registry_data)

    def _export_registry_to_md(self, registry_data: dict):
        """Generates the Markdown table for the Knowledge Base."""
        headers = ["Error Symptom", "Root Cause", "Solution Steps", "Certainty Score"]
        header_row = "| " + " | ".join(headers) + " |"
        divider_row = "| " + " | ".join(["---"] * len(headers)) + " |"
        
        rows = []
        for symptom, data in registry_data.items():
            # Replace newlines with <br> for markdown table compatibility
            cause = str(data.get("root_cause", "Unknown")).replace("\n", "<br>")
            steps = str(data.get("solution_steps", "Pending")).replace("\n", "<br>")
            score = data.get("certainty_score", 0)
            rows.append(f"| {symptom} | {cause} | {steps} | {score} |")

        md_content = "# Troubleshooting Registry Knowledge Base\n\n"
        md_content += "Certainty Scores:\n"
        md_content += "- **0**: Unfixed / Reoccurring Bug\n"
        md_content += "- **1**: Agent believes issue is resolved based on context.\n"
        md_content += "- **2**: Human confirmed resolution.\n\n"
        md_content += header_row + "\n" + divider_row + "\n" + "\n".join(rows) + "\n"

        with open(self.registry_md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

    def _sanitize_symptom_for_registry(self, symptom: str) -> str:
        """
        Produces a clean, single-line key for the registry table.

        Logic is intentionally simple:
        - If the symptom is already a single line → use it directly.
        - If it is multi-line (a full traceback) → store a short preview 
          with a tag indicating the agent should read runs_summary.md 
          for the full context and interpret it there.

        This avoids brittle traceback parsing. The AI agent consuming this
        registry is far better at interpreting raw tracebacks than any regex.
        """
        stripped = symptom.strip()

        # Empty or whitespace-only input
        if not stripped:
            return "[EMPTY ERROR - see runs_summary.md for context]"

        # Single-line errors are clean enough to use directly
        # (e.g. "IndexError: list index out of range")
        if "\n" not in stripped:
            return stripped

        # Multi-line input (likely a full traceback).
        # Take a short preview (first 120 chars of the first line)
        # and tag it so the agent knows to check the full logs.
        preview = stripped.split("\n")[0][:120]
        return f"[TRACEBACK - agent review pending, see runs_summary.md] {preview}"

    def log_error(self, symptom: str, context: str = ""):
        """
        Logs a new error to the run tracking and initializes/updates a Knowledge Base entry 
        with a Certainty Score of 0.
        
        The FULL symptom/traceback is preserved in runs_summary.md and runs.jsonl.
        The registry table only stores a clean, single-line version of the symptom
        to keep the Markdown table readable.
        """
        # 1. Add to Run log (full traceback preserved here)
        self.log_run({
            "event_type": "ERROR",
            "symptom": symptom,
            "context": context
        })
        self.logger.error(f"Error encountered: {symptom}")

        # 2. Sanitize the symptom for use as a clean registry key
        clean_symptom = self._sanitize_symptom_for_registry(symptom)

        # 3. Update Registry using the clean, single-line symptom
        registry = self._load_registry()
        
        if clean_symptom not in registry:
            registry[clean_symptom] = {
                "root_cause": "Unknown, pending investigation",
                "solution_steps": "None",
                "certainty_score": 0,
                "occurrences": 1,
                "first_seen": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat()
            }
        else:
            registry[clean_symptom]["occurrences"] += 1
            registry[clean_symptom]["last_seen"] = datetime.now().isoformat()
            # If the error reappeared, reset score back to 0
            if registry[clean_symptom]["certainty_score"] > 0:
                self.logger.warning(f"Regression detected for '{clean_symptom}'. Resetting certainty score to 0.")
                registry[clean_symptom]["certainty_score"] = 0

        self._save_registry(registry)

    def update_knowledge_base(self, symptom: str, root_cause: str, solution_steps: str, certainty_score: int):
        """
        Updates an existing bug in the Knowledge Base once a solution is found or attempted.
        - certainty_score 0: Unfixed or reverted.
        - certainty_score 1: Agent assumes fixed.
        - certainty_score 2: Human validated fixed.
        """
        if certainty_score not in [0, 1, 2]:
            raise ValueError("certainty_score must be 0, 1, or 2.")

        registry = self._load_registry()
        
        if symptom not in registry:
            self.logger.warning(f"Symptom '{symptom}' not found in registry. Adding it as new.")
            registry[symptom] = {
                "occurrences": 0,
                "first_seen": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat()
            }

        registry[symptom]["root_cause"] = root_cause
        registry[symptom]["solution_steps"] = solution_steps
        registry[symptom]["certainty_score"] = certainty_score
        registry[symptom]["last_updated"] = datetime.now().isoformat()

        self._save_registry(registry)
        
        # Log this state change into the run tracking
        self.log_run({
            "event_type": "KNOWLEDGE_BASE_UPDATE",
            "symptom": symptom,
            "new_score": certainty_score,
            "status": "Resolved (Agent)" if certainty_score == 1 else ("Resolved (Human)" if certainty_score == 2 else "Unresolved")
        })

    def query_knowledge_base(self, query: str) -> dict:
        """
        Simple keyword search over the registry's symptoms and root causes.
        Useful for agents trying to find if an error has occurred before.
        """
        registry = self._load_registry()
        results = {}
        query_lower = query.lower()
        
        for symptom, data in registry.items():
            if query_lower in symptom.lower() or query_lower in data.get("root_cause", "").lower():
                results[symptom] = data
                
        return results

def setup_logger(source_name: str = "__main__") -> AgentLogger:
    """Convenience function to quickly instantiate the logger."""
    return AgentLogger(source_name)


def run_with_logging(source_file: str, main_func, *args, **kwargs):
    """
    One-liner convenience function that:
    1. Initializes the logger scoped to the given source file.
    2. Logs the start of the run.
    3. Calls main_func(*args, **kwargs) wrapped in a try/except.
    4. On any crash (including SystemExit), captures the full traceback
       and logs it to the Knowledge Base.
    
    Usage:
        from _agents.scripts.agent_logger import run_with_logging
        run_with_logging(__file__, main)
    """
    import traceback
    logging_message = """
    ================= Logging run for file =================
    ================= Logging run for file =================
    ================= Logging run for file =================
    """
    print(logging_message)
    logger = setup_logger(source_file)
    logger.log_run({"action": "Script started", "source": source_file})

    try:
        main_func(*args, **kwargs)
    except BaseException as e:
        full_error = traceback.format_exc()
        logger.log_error(full_error, context=f"Uncaught exception in {source_file}")
        raise
