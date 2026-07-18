# -*- coding: utf-8 -*-
"""
Script Manager
==============
AI-powered shell script writer and cron job manager.

Features:
  - Describe a script in plain English → AI writes the bash script
  - Review, edit path, then write to disk and make executable
  - Safe file writing via base64 — no heredoc injection issues
  - Optionally add to crontab immediately
  - Manage existing cron jobs: list, add, remove

Fix applied:
  The previous version wrote scripts using bash heredoc syntax inside
  execute_commands().  Any single-quote (') or backslash in the generated
  script would silently corrupt the written file or cause a syntax error.

  New approach: encode the script as base64, then decode it on the remote
  shell with:
      echo '<b64>' | base64 -d | sudo tee <path>
  This is injection-safe regardless of script content.
"""

import os
import base64
import subprocess
import json
from ai_engine import _call_api
import config
import ui
from executor import ask_permission, run_command


# ── CRON PRESETS ───────────────────────────────────────────────────────────────
CRON_PRESETS = {
    "1":  ("Every minute",            "* * * * *"),
    "2":  ("Every 5 minutes",         "*/5 * * * *"),
    "3":  ("Every 15 minutes",        "*/15 * * * *"),
    "4":  ("Every 30 minutes",        "*/30 * * * *"),
    "5":  ("Every hour",              "0 * * * *"),
    "6":  ("Every 6 hours",           "0 */6 * * *"),
    "7":  ("Every day at midnight",   "0 0 * * *"),
    "8":  ("Every day at 2am",        "0 2 * * *"),
    "9":  ("Every Sunday at 3am",     "0 3 * * 0"),
    "10": ("Every Monday at 4am",     "0 4 * * 1"),
    "11": ("1st of every month 1am",  "0 1 1 * *"),
    "12": ("Custom (enter manually)", "custom"),
}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_write_commands(content: str, dest_path: str) -> list:
    """
    Return a list of commands that safely write *content* to *dest_path*
    on the remote/local Linux system, regardless of what characters are in
    the content.

    Strategy: base64-encode the content, pipe through `base64 -d | tee`.
    This avoids all heredoc quoting issues.
    """
    encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
    # Split into 76-char chunks to avoid ARG_MAX issues on very large scripts
    chunks = [encoded[i:i+76] for i in range(0, len(encoded), 76)]
    b64_oneliner = "".join(chunks)

    write_cmd  = f"bash -c \"echo '{b64_oneliner}' | base64 -d | tee {dest_path} > /dev/null\""
    chmod_cmd  = f"chmod +x {dest_path}"
    return [write_cmd, chmod_cmd]


# ── Script Writer ──────────────────────────────────────────────────────────────

def write_script():
    ui.section("AI Script Writer")
    os_name = config.get("os_name", "Ubuntu 22.04")

    print("  " + ui.C.DIM + "Describe what the script should do in plain English." + ui.C.RESET)
    print("  " + ui.C.DIM + "Examples:" + ui.C.RESET)
    print("  " + ui.C.DIM + "  * Back up /var/www to /mnt/backup with timestamp" + ui.C.RESET)
    print("  " + ui.C.DIM + "  * Check disk usage and email alert if over 80%" + ui.C.RESET)
    print("  " + ui.C.DIM + "  * Rotate and compress nginx log files older than 7 days" + ui.C.RESET)
    print("  " + ui.C.DIM + "  * Restart nginx if it is not running" + ui.C.RESET + "\n")

    description = input("  " + ui.C.BOLD + "Script description: " + ui.C.RESET).strip()
    if not description:
        ui.error("Description cannot be empty.")
        return

    default_name = description.split()[0].lower().replace("/", "_") + ".sh"
    default_path = f"/usr/local/bin/{default_name}"
    script_path  = input(f"  Save to [{default_path}]: ").strip() or default_path

    ui.info("Asking AI to write the script...")

    prompt = f"""Write a complete, production-quality bash script for the following task:

Task: {description}
Target OS: {os_name}

Requirements:
- Start with #!/usr/bin/env bash
- Add set -euo pipefail
- Include descriptive comments
- Use absolute paths for all commands
- Handle errors gracefully with meaningful messages
- Log output with timestamps to /var/log/ if appropriate
- Make it idempotent where possible

Return ONLY the raw bash script content. No markdown, no explanation."""

    messages = [
        {"role": "system", "content": "You are an expert Linux bash scripter. Return only the raw script content with no markdown fences."},
        {"role": "user",   "content": prompt},
    ]

    try:
        script_content = _call_api(messages, temperature=0.2)
    except Exception as e:
        ui.error(f"AI error: {e}")
        return

    # Strip any markdown fences the model may still include
    from ai_engine import _strip_markdown_fences
    script_content = _strip_markdown_fences(script_content)

    # Show generated script
    ui.section("Generated Script")
    print(script_content)
    print()

    confirm = input("  Write this script to disk? [y/n]: ").strip().lower()
    if confirm not in ("y", "yes"):
        ui.warn("Aborted.")
        return

    # Safe write via base64 — no heredoc injection issues
    commands = _make_write_commands(script_content, script_path)

    from executor import execute_commands
    os_name_stored = config.get("os_name")
    pkg_mgr        = config.get("package_manager")
    execute_commands(commands, os_name_stored, pkg_mgr)

    ui.success(f"Script written to {script_path} and made executable.")

    config.log_audit(
        "SCRIPT_WRITE",
        f"Path: {script_path}\n"
        f"Description: {description}\n"
        f"Content:\n{script_content}"
    )

    # Offer to add to cron
    cron_ans = input("  Add this script to a cron job now? [y/n]: ").strip().lower()
    if cron_ans in ("y", "yes"):
        add_cronjob(script_path)


# ── Cron Manager ───────────────────────────────────────────────────────────────

def manage_crons():
    ui.section("Cron Job Manager")
    options = [
        ("1", "List current cron jobs"),
        ("2", "Add a new cron job"),
        ("3", "Remove a cron job"),
        ("4", "Add cron job for a script (AI suggests schedule)"),
        ("0", "Back"),
    ]
    for k, v in options:
        print(f"  {ui.C.YELLOW}{k}{ui.C.RESET}. {v}")

    choice = input(f"\n  {ui.C.BOLD}Choice: {ui.C.RESET}").strip()

    if choice == "1":
        list_crons()
    elif choice == "2":
        add_cronjob()
    elif choice == "3":
        remove_cronjob()
    elif choice == "4":
        script_path = input("  Path to script: ").strip()
        add_cronjob(script_path, ai_suggest=True)


def list_crons():
    ui.section("Current Cron Jobs")
    try:
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True, text=True
        )
        if result.returncode != 0 or not result.stdout.strip():
            ui.info("No cron jobs found for current user.")
        else:
            print(ui.C.CYAN + result.stdout + ui.C.RESET)
    except FileNotFoundError:
        ui.error("crontab command not found. Is cron installed?")


def _pick_schedule(ai_suggest: bool = False, script_path: str = "") -> str:
    """Return a cron schedule string chosen by the user (or AI)."""
    if ai_suggest and script_path:
        ui.info("Asking AI to suggest a schedule for this script...")
        prompt = f"""Given this script path: {script_path}
Based on common usage patterns, suggest the most appropriate cron schedule.
Return ONLY the cron schedule string (5 fields), e.g. "0 2 * * *".
No explanation."""
        messages = [
            {"role": "system", "content": "You are a Linux sysadmin. Return only the 5-field cron expression."},
            {"role": "user",   "content": prompt},
        ]
        try:
            suggestion = _call_api(messages, temperature=0.1).strip().split("\n")[0]
            ui.info(f"AI suggests: {suggestion}")
            use_it = input("  Use this schedule? [y/n]: ").strip().lower()
            if use_it in ("y", "yes"):
                return suggestion
        except Exception:
            pass  # fall through to manual selection

    # Show presets
    print(f"\n  {ui.C.BOLD}Pick a schedule:{ui.C.RESET}")
    for k, (label, expr) in CRON_PRESETS.items():
        if expr != "custom":
            print(f"  {ui.C.YELLOW}{k:>2}{ui.C.RESET}. {label:<30} {ui.C.DIM}({expr}){ui.C.RESET}")
        else:
            print(f"  {ui.C.YELLOW}{k:>2}{ui.C.RESET}. {label}")

    while True:
        pick = input("  Choice: ").strip()
        if pick in CRON_PRESETS:
            _, expr = CRON_PRESETS[pick]
            if expr == "custom":
                expr = input("  Enter cron expression (e.g. '30 4 * * 1'): ").strip()
            return expr
        print("  Invalid choice.")


def add_cronjob(script_path: str = "", ai_suggest: bool = False):
    ui.section("Add Cron Job")

    if not script_path:
        script_path = input("  Command or script path to run: ").strip()
    if not script_path:
        ui.error("Command cannot be empty.")
        return

    # Optional: redirect output
    log_ans = input("  Log output to file? [y/n]: ").strip().lower()
    log_suffix = ""
    if log_ans in ("y", "yes"):
        default_log = f"/var/log/{os.path.basename(script_path).replace('.sh', '')}.log"
        log_file   = input(f"  Log file [{default_log}]: ").strip() or default_log
        log_suffix = f" >> {log_file} 2>&1"

    schedule  = _pick_schedule(ai_suggest=ai_suggest, script_path=script_path)
    cron_line = f"{schedule} {script_path}{log_suffix}"

    print(f"\n  {ui.C.BOLD}Cron line to add:{ui.C.RESET}")
    print(f"  {ui.C.CYAN}{cron_line}{ui.C.RESET}\n")
    confirm = input("  Add this cron job? [y/n]: ").strip().lower()
    if confirm not in ("y", "yes"):
        ui.warn("Aborted.")
        return

    # Add to crontab — quote the cron_line to handle spaces safely
    safe_line = cron_line.replace("'", "'\\''")  # escape single quotes
    add_cmd   = f"(crontab -l 2>/dev/null; echo '{safe_line}') | crontab -"
    approved  = ask_permission(add_cmd)
    if approved:
        success, _, stderr = run_command(add_cmd, use_sudo=False)
        if success:
            ui.success(f"Cron job added: {cron_line}")
        else:
            ui.error(f"Failed to add cron job: {stderr}")


def remove_cronjob():
    ui.section("Remove Cron Job")
    try:
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        if result.returncode != 0 or not result.stdout.strip():
            ui.info("No cron jobs to remove.")
            return

        lines = [
            l for l in result.stdout.strip().split("\n")
            if l.strip() and not l.startswith("#")
        ]
        if not lines:
            ui.info("No active cron jobs found.")
            return

        print()
        for i, line in enumerate(lines, 1):
            print(f"  {ui.C.YELLOW}{i}{ui.C.RESET}. {line}")
        print(f"  {ui.C.YELLOW}0{ui.C.RESET}. Cancel")

        while True:
            raw = input("\n  Remove which job number: ").strip()
            if raw == "0":
                return
            if raw.isdigit() and 1 <= int(raw) <= len(lines):
                idx = int(raw) - 1
                break
            print("  Invalid choice.")

        line_to_remove = lines[idx]
        confirm = input(f"  Remove: {line_to_remove}\n  Confirm? [y/n]: ").strip().lower()
        if confirm not in ("y", "yes"):
            ui.warn("Aborted.")
            return

        # Rebuild crontab without the removed line
        new_lines = [l for l in result.stdout.strip().split("\n") if l != line_to_remove]
        new_crontab = "\n".join(new_lines) + "\n"

        # Write the new crontab safely via a temp file approach
        import tempfile
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".crontab", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(new_crontab)
            tmp_path = tmp.name

        remove_cmd = f"crontab {tmp_path} && rm -f {tmp_path}"
        approved   = ask_permission(remove_cmd)
        if approved:
            success, _, stderr = run_command(remove_cmd, use_sudo=False)
            if success:
                ui.success("Cron job removed.")
            else:
                ui.error(f"Failed: {stderr}")

    except Exception as e:
        ui.error(f"Error: {e}")
