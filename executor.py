"""
Command executor with:
  - Permission prompt before running each command
  - Real-time output streaming (deadlock-safe)
  - Dangerous command detection
  - Error detection
  - Auto retry with AI-generated fixes
  - DRY_RUN mode: set env var LINUX_AGENT_DRY_RUN=1 to print commands without executing

Deadlock fix:
  The previous version read stdout line-by-line in the main thread, then
  called proc.wait(), then read stderr — this blocks when the subprocess fills
  the stderr pipe buffer before stdout is fully consumed.

  Fix: stream stdout in a background thread while the main thread drains
  stderr simultaneously, then join both.
"""

import os
import sys
import threading
import subprocess
from typing import Tuple

# ── Dry-run mode ────────────────────────────────────────────────────────────────
DRY_RUN: bool = os.environ.get("LINUX_AGENT_DRY_RUN", "").strip() in ("1", "true", "yes")

# ── Patterns that indicate a dangerous command ──────────────────────────────────
_DANGEROUS_PATTERNS = [
    "rm -rf /",
    "rm -rf /*",
    "dd if=",
    "mkfs.",
    ":(){ :|:& };:",   # fork bomb
    "> /dev/sda",
    "shred /dev/",
    "chmod -R 777 /",
    "chown -R",
]


# ── ANSI colors ─────────────────────────────────────────────────────────────────
class Color:
    RESET  = "\033[0m"
    RED    = "\033[91m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    CYAN   = "\033[96m"
    BOLD   = "\033[1m"
    DIM    = "\033[2m"


def colorize(text: str, color: str) -> str:
    return f"{color}{text}{Color.RESET}"


# ── Safety check ─────────────────────────────────────────────────────────────────
def _is_dangerous(command: str) -> bool:
    """Return True if the command matches a known-dangerous pattern."""
    lower = command.lower().strip()
    for pat in _DANGEROUS_PATTERNS:
        if pat.lower() in lower:
            return True
    return False


# ── Permission prompt ─────────────────────────────────────────────────────────────
def ask_permission(command: str) -> bool:
    """Show a command and ask the user for permission to run it."""
    if _is_dangerous(command):
        print()
        print(colorize("┌─ ⚠  DANGEROUS COMMAND DETECTED ──────────────────", Color.RED))
        print(colorize(f"│  $ {command}", Color.BOLD))
        print(colorize("└───────────────────────────────────────────────────", Color.RED))
        print(colorize(
            "  This command could cause irreversible damage. "
            "Type 'CONFIRM' in uppercase to proceed, or anything else to skip.",
            Color.YELLOW
        ))
        choice = input(colorize("  > ", Color.YELLOW)).strip()
        if choice == "CONFIRM":
            return True
        print(colorize("  ⏭  Skipped (dangerous command).", Color.DIM))
        return False

    print()
    print(colorize("┌─ Command to execute ──────────────────────────────", Color.CYAN))
    print(colorize(f"│  $ {command}", Color.BOLD))
    print(colorize("└───────────────────────────────────────────────────", Color.CYAN))

    while True:
        choice = input(colorize(
            "  Run this command? [y/n/s(skip)/q(quit)] > ", Color.YELLOW
        )).strip().lower()
        if choice in ("y", "yes"):
            return True
        elif choice in ("n", "no", "s", "skip"):
            print(colorize("  ⏭  Skipped.", Color.DIM))
            return False
        elif choice in ("q", "quit"):
            print(colorize("\n  Aborted by user.", Color.RED))
            sys.exit(0)
        else:
            print("  Please enter y, n, s, or q.")


# ── Core runner ──────────────────────────────────────────────────────────────────
def run_command(command: str, use_sudo: bool = True) -> Tuple[bool, str, str]:
    """
    Execute a shell command, streaming stdout in real time.
    Returns (success: bool, stdout: str, stderr: str)

    Deadlock-safe: stdout is streamed in a background thread while the main
    thread reads stderr, then both are joined before waiting for the process.
    """
    full_cmd = f"sudo {command}" if use_sudo else command

    if DRY_RUN:
        print(colorize(f"\n  [DRY-RUN] Would run: {full_cmd}", Color.YELLOW))
        return True, "", ""

    print(colorize(f"\n  ▶ Running: {full_cmd}", Color.DIM))

    try:
        proc = subprocess.Popen(
            full_cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        stdout_lines: list[str] = []
        stderr_lines: list[str] = []

        def _stream_stdout():
            for line in proc.stdout:
                print(colorize(f"     {line}", Color.DIM), end="", flush=True)
                stdout_lines.append(line)
            proc.stdout.close()

        stdout_thread = threading.Thread(target=_stream_stdout, daemon=True)
        stdout_thread.start()

        # Read stderr in the main thread while stdout drains in background
        stderr_output = proc.stderr.read()
        proc.stderr.close()

        stdout_thread.join()
        proc.wait()

        if stderr_output:
            stderr_lines.append(stderr_output)
            print(colorize(f"\n  ⚠  STDERR:\n{stderr_output}", Color.YELLOW))

        success = proc.returncode == 0
        if success:
            print(colorize("  ✓ Command succeeded.", Color.GREEN))
        else:
            print(colorize(
                f"  ✗ Command failed (exit code {proc.returncode}).", Color.RED
            ))

        return success, "".join(stdout_lines), "".join(stderr_lines)

    except Exception as e:
        msg = str(e)
        print(colorize(f"  ✗ Execution error: {msg}", Color.RED))
        return False, "", msg


# ── Orchestrator ─────────────────────────────────────────────────────────────────
def execute_commands(
    commands: list,
    os_name: str,
    package_manager: str,
    auto_fix: bool = True,
    max_retries: int = 2,
):
    """
    Walk through a list of commands:
    1. Ask permission for each
    2. Run if approved
    3. On failure, ask AI for a fix and retry (up to max_retries times)
    """
    from ai_engine import fix_error

    total = len(commands)
    for idx, cmd in enumerate(commands, start=1):
        print(colorize(f"\n[{idx}/{total}]", Color.BOLD), end=" ")

        approved = ask_permission(cmd)
        if not approved:
            continue

        success, stdout, stderr = run_command(cmd)

        if success:
            continue

        # ── Command failed ──────────────────────────────────────────────────
        if not auto_fix:
            print(colorize("  Auto-fix is disabled. Stopping.", Color.RED))
            break

        error_context = stderr or stdout or "Unknown error"
        retries = 0

        while not success and retries < max_retries:
            retries += 1
            print(colorize(
                f"\n  🔧 Asking AI to diagnose and fix (attempt {retries}/{max_retries})...",
                Color.CYAN
            ))

            try:
                fix = fix_error(cmd, error_context, os_name, package_manager)
            except Exception as e:
                print(colorize(f"  AI error: {e}", Color.RED))
                break

            print(colorize(
                f"\n  📋 Diagnosis: {fix.get('diagnosis', 'Unknown')}", Color.YELLOW
            ))

            fix_cmds = fix.get("fix_commands", [])
            if not fix_cmds:
                print(colorize("  AI could not suggest a fix.", Color.RED))
                break

            # Run the fix commands
            for fix_cmd in fix_cmds:
                print(colorize("\n  Fix step:", Color.CYAN))
                if ask_permission(fix_cmd):
                    run_command(fix_cmd)

            # Retry the original command
            print(colorize("\n  ↩  Retrying original command...", Color.CYAN))
            if ask_permission(cmd):
                success, stdout, stderr = run_command(cmd)
                error_context = stderr or stdout or "Unknown error"
            else:
                break

        if not success:
            print(colorize(
                "\n  ❌ Could not complete this step after retries. "
                "Continuing to next command...\n",
                Color.RED,
            ))
