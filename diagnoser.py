# -*- coding: utf-8 -*-
"""
diagnoser.py
============
AI-powered system diagnostic tool. 

Reads log files, configuration files, service status, and port usage
directly from the server to diagnose complex errors and recommend fixes.
"""

import sys
import config
import ui
from ai_engine import get_diagnostic_commands, analyze_diagnostic_data
from executor import run_command, execute_commands, ask_permission

def run_diagnose_flow(issue: str = None):
    ui.section("AI Server Diagnoser 🔧")
    
    # 1. Ask for issue description if not provided
    if not issue:
        print("  " + ui.C.DIM + "Describe what issue or service error you want to diagnose." + ui.C.RESET)
        print("  " + ui.C.DIM + "Examples:" + ui.C.RESET)
        print("  " + ui.C.DIM + "  * Jenkins service failed to start" + ui.C.RESET)
        print("  " + ui.C.DIM + "  * Nginx fails configuration test with code 1" + ui.C.RESET)
        print("  " + ui.C.DIM + "  * Cannot connect to MySQL database locally" + ui.C.RESET + "\n")
        
        issue = input("  " + ui.C.BOLD + "Describe the issue: " + ui.C.RESET).strip()
        if not issue:
            ui.error("Issue description cannot be empty.")
            return

    os_name = config.get("os_name", "Ubuntu 22.04")
    pkg_mgr = config.get("package_manager", "apt")
    
    ui.info("Asking AI to suggest inspection commands (log files, config checks)...")
    
    # 2. Get commands from AI
    try:
        commands = get_diagnostic_commands(issue, os_name, pkg_mgr)
    except Exception as e:
        ui.error(f"AI error: {e}")
        return
        
    if not commands:
        ui.warn("AI did not suggest any inspection commands. Attempting direct analysis...")
        commands = ["journalctl -n 50", "systemctl status"]

    print(f"\n  {ui.C.BOLD}AI recommended running {len(commands)} diagnostic command(s):{ui.C.RESET}")
    for i, cmd in enumerate(commands, 1):
        print(f"    {i}. {cmd}")
        
    # 3. Execute commands to gather logs/configs
    gathered_data = []
    
    for cmd in commands:
        print()
        ui.info(f"Gathering data with: {ui.C.BOLD}{cmd}{ui.C.RESET}")
        approved = ask_permission(cmd)
        if approved:
            # We don't want to use sudo if it's not needed, but run_command has use_sudo=True by default.
            # Let's let the user approve with/without sudo based on user_sudo prompt.
            success, stdout, stderr = run_command(cmd, use_sudo=True)
            output = f"Command: {cmd}\nSuccess: {success}\n"
            if stdout:
                output += f"Stdout:\n{stdout}\n"
            if stderr:
                output += f"Stderr:\n{stderr}\n"
            gathered_data.append(output)
        else:
            gathered_data.append(f"Command skipped: {cmd}\n")

    # 4. Send gathered data to AI for analysis
    all_data = "\n".join(gathered_data)
    
    ui.section("Analyzing Logs & Configuration Files 🧠")
    ui.info("Sending gathered diagnostics data to AI...")
    
    try:
        analysis = analyze_diagnostic_data(issue, all_data, os_name, pkg_mgr)
    except Exception as e:
        ui.error(f"AI analysis failed: {e}")
        return

    diagnosis = analysis.get("diagnosis", "Unknown diagnosis.")
    fix_commands = analysis.get("fix_commands", [])

    # 5. Display Diagnosis
    print(f"\n  {ui.C.BOLD}{ui.C.YELLOW}📋 Diagnosis:{ui.C.RESET}")
    for line in diagnosis.split("\n"):
        print(f"  {ui.C.CYAN}{line}{ui.C.RESET}")
    print()

    # 6. Offer Fix Commands
    if fix_commands:
        print(f"  {ui.C.BOLD}Recommended fix commands:{ui.C.RESET}")
        for i, cmd in enumerate(fix_commands, 1):
            print(f"    {i}. {cmd}")
            
        confirm = input(f"\n  {ui.C.BOLD}Would you like to execute the fix commands? [y/n] > {ui.C.RESET}").strip().lower()
        if confirm in ("y", "yes"):
            execute_commands(fix_commands, os_name, pkg_mgr)
            ui.success("Diagnosis and fix process complete!")
        else:
            ui.warn("Fix commands execution aborted.")
    else:
        ui.info("No automatic fix commands recommended by AI. You may need to fix the issue manually.")
