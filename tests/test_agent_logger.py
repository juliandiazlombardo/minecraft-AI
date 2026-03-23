import sys
from pathlib import Path

if __name__ == "__main__":
    # Add project root to path
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))

    from _agents.scripts.agent_logger import setup_logger

    logger = setup_logger(__file__)
    print(f"Logger target: {logger.log_dir}\n")

    # ---- Test 1: Single-line error → used as-is ----
    print("TEST 1: Normal single-line exception")
    logger.log_error("IndexError: list index out of range", context="test 1")

    # ---- Test 2: Multi-line traceback → preview + agent tag ----
    print("TEST 2: Full multi-line traceback")
    fake_traceback = """Traceback (most recent call last):
  File "main.py", line 101, in <module>
    main()
hydra.errors.MissingConfigException: Cannot find primary config 'conf'.
SystemExit: 1"""
    logger.log_error(fake_traceback, context="test 2")

    # ---- Test 3: Empty string ----
    print("TEST 3: Empty string (KeyboardInterrupt-like)")
    logger.log_error("", context="test 3")

    # ---- Test 4: Single-line custom exception ----
    print("TEST 4: Custom single-line exception")
    logger.log_error("my_module.Timeout: connection timed out after 30s", context="test 4")

    # ---- Test 5: run_with_logging() ----
    print("TEST 5: run_with_logging() with a crashing function")
    from _agents.scripts.agent_logger import run_with_logging
    def fake_crash():
        raise ValueError("Something went wrong in the function")
    try:
        run_with_logging(__file__, fake_crash)
    except ValueError:
        print("  (ValueError re-raised as expected)")

    # ---- Verify ----
    print("\n===== REGISTRY KEYS =====")
    registry = logger._load_registry()
    for i, (symptom, data) in enumerate(registry.items(), 1):
        print(f"  {i}. {symptom}")

    print(f"\nDone. Check `_agents/logs/test_agent_logger/troubleshooting_registry.md`")
