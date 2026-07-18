#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Linux Agentic Tool — Entry Point
=================================
Interactive menu OR direct CLI shortcuts.

USAGE:
  python3 main.py                            # interactive menus
  python3 main.py install nginx              # recipe shortcut
  python3 main.py install wordpress
  python3 main.py task "install jenkins"     # plain-English task
  python3 main.py ask "how do I free space?" # instant AI answer
  python3 main.py chat                       # conversational AI agent
  python3 main.py vhost                      # add nginx/apache vhost
  python3 main.py script                     # AI script writer
  python3 main.py cron                       # cron job manager
  python3 main.py list                       # show all recipes
  python3 main.py setup                      # re-run setup wizard
  python3 main.py --yes install nginx        # skip plan confirmation
  python3 main.py --dry-run task "install htop"  # print commands only
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(__file__))

import config
import ui
from ai_engine import get_install_commands, ask_ai
from executor import execute_commands
from recipes import RECIPES, CATEGORIES, get_recipes_by_category


# ── Setup wizard ───────────────────────────────────────────────────────────────

def setup_wizard():
    ui.section("First-Time Setup")
    ui.info("Welcome! Let's get you set up in under a minute.")

    os_name = ui.select_os()
    config.set_value("os_name", os_name)
    pkg_mgr = config.get_package_manager(os_name)
    config.set_value("package_manager", pkg_mgr)
    ui.success(f"OS saved: {os_name}  (package manager: {pkg_mgr})")

    # Allow skipping API key entry if env var is already set
    if os.environ.get("OPENROUTER_API_KEY"):
        ui.info("OPENROUTER_API_KEY env var detected — skipping manual key entry.")
    else:
        api_key = ui.enter_api_key()
        config.set_value("api_key", api_key)
        ui.success("API key saved securely.")

    config.set_value("setup_done", True)


def ensure_setup():
    if not config.get("setup_done"):
        setup_wizard()
        return
    os_name = config.get("os_name")
    pkg_mgr = config.get("package_manager")
    model   = config.get_model()
    ui.info(
        f"OS: {ui.C.BOLD}{os_name}{ui.C.RESET}  |  "
        f"pkg: {pkg_mgr}  |  "
        f"model: {ui.C.YELLOW}{model}{ui.C.RESET}"
    )


# ── Core actions ───────────────────────────────────────────────────────────────

def run_recipe(recipe_key: str, auto_yes: bool = False):
    if recipe_key not in RECIPES:
        matches = [k for k in RECIPES if recipe_key.lower() in k.lower()]
        if len(matches) == 1:
            recipe_key = matches[0]
        elif len(matches) > 1:
            ui.warn(f"Ambiguous recipe '{recipe_key}'. Matches: {', '.join(matches)}")
            return
        else:
            ui.error(f"Unknown recipe '{recipe_key}'. Run 'python3 main.py list' to see all.")
            return

    recipe  = RECIPES[recipe_key]
    os_name = config.get("os_name")
    pkg_mgr = config.get("package_manager")

    ui.section(f"Recipe: {recipe['name']}")
    ui.info(recipe["description"])
    print(f"\n  {ui.C.DIM}Asking AI to generate commands for {os_name}...{ui.C.RESET}")

    try:
        result = get_install_commands(recipe["task"], os_name, pkg_mgr)
    except Exception as e:
        ui.error(f"AI error: {e}")
        return

    _preview_and_execute(result, recipe["name"], os_name, pkg_mgr, auto_yes)


def run_custom_task(task: str, auto_yes: bool = False):
    os_name = config.get("os_name")
    pkg_mgr = config.get("package_manager")

    ui.section("Custom Task")
    ui.info(f"Task: {task}")
    print(f"\n  {ui.C.DIM}Asking AI to plan commands for {os_name}...{ui.C.RESET}")

    try:
        result = get_install_commands(task, os_name, pkg_mgr)
    except Exception as e:
        ui.error(f"AI error: {e}")
        return

    _preview_and_execute(result, task, os_name, pkg_mgr, auto_yes)


def run_ai_qa(question: str = None):
    os_name = config.get("os_name", "Linux")

    if question:
        ui.section("AI Answer")
        try:
            answer = ask_ai(question, os_name)
            print(f"\n  {ui.C.CYAN}{answer}{ui.C.RESET}\n")
        except Exception as e:
            ui.error(f"AI error: {e}")
        return

    ui.section("Ask AI")
    print(f"  {ui.C.DIM}Type your question. Type 'back' or Ctrl+C to return.{ui.C.RESET}\n")
    while True:
        question = input(f"  {ui.C.BOLD}Question: {ui.C.RESET}").strip()
        if not question or question.lower() in ("back", "exit", "quit"):
            break
        print()
        try:
            answer = ask_ai(question, os_name)
            print(f"  {ui.C.CYAN}{answer}{ui.C.RESET}\n")
        except Exception as e:
            ui.error(f"AI error: {e}")


def list_recipes():
    ui.section("All Available Recipes")
    grouped = get_recipes_by_category()
    for cat_key, cat_label in CATEGORIES.items():
        recipes_in_cat = grouped.get(cat_key, {})
        if not recipes_in_cat:
            continue
        print(f"\n  {ui.C.BOLD}{cat_label}{ui.C.RESET}")
        for key, recipe in recipes_in_cat.items():
            name_col = recipe["name"].ljust(35)
            print(
                f"    {ui.C.YELLOW}{key:<22}{ui.C.RESET} "
                f"{name_col}  {ui.C.DIM}{recipe['description']}{ui.C.RESET}"
            )
    print()


def change_settings():
    ui.section("Settings")
    options = [
        ("1", "Change OS"),
        ("2", "Change API Key"),
        ("3", "Change AI Model"),
        ("4", "View token / credit usage"),
        ("0", "Back"),
    ]
    for k, v in options:
        print(f"  {ui.C.YELLOW}{k}{ui.C.RESET}. {v}")

    choice = input(f"\n  {ui.C.BOLD}Choose: {ui.C.RESET}").strip()
    if choice == "1":
        os_name = ui.select_os()
        pkg_mgr = config.get_package_manager(os_name)
        config.set_value("os_name", os_name)
        config.set_value("package_manager", pkg_mgr)
        ui.success(f"OS updated to: {os_name}  ({pkg_mgr})")
    elif choice == "2":
        key = ui.enter_api_key()
        config.set_value("api_key", key)
        ui.success("API key updated.")
    elif choice == "3":
        current  = config.get_model()
        model_id = ui.select_model(current)
        config.set_model(model_id)
        ui.success(f"Model set to: {model_id}")
    elif choice == "4":
        ui.show_usage_summary()


def _preview_and_execute(result: dict, label: str, os_name: str, pkg_mgr: str, auto_yes: bool):
    description = result.get("description", label)
    commands    = result.get("commands", [])
    warnings    = result.get("warnings", "")

    print(f"\n  {ui.C.BOLD}Plan:{ui.C.RESET} {description}")
    if warnings:
        ui.warn(warnings)
    if not commands:
        ui.error("AI returned no commands.")
        return

    print(f"\n  {ui.C.DIM}AI generated {len(commands)} command(s):{ui.C.RESET}")
    for i, cmd in enumerate(commands, 1):
        print(f"  {ui.C.DIM}  {i}. {cmd}{ui.C.RESET}")

    # Check if DRY_RUN is active
    from executor import DRY_RUN
    if DRY_RUN:
        ui.warn("[DRY-RUN] Showing commands only — nothing will be executed.")

    if auto_yes:
        ui.info("--yes flag set: proceeding automatically.")
    elif not DRY_RUN:
        confirm = input(f"\n  {ui.C.BOLD}Proceed with execution? [y/n] > {ui.C.RESET}").strip().lower()
        if confirm not in ("y", "yes"):
            ui.warn("Aborted.")
            return

    execute_commands(commands, os_name, pkg_mgr)
    if not DRY_RUN:
        ui.success(f"'{label}' sequence complete!")


# ── Interactive main menu ──────────────────────────────────────────────────────

def interactive_mode():
    ui.banner()
    ensure_setup()

    while True:
        choice = ui.main_menu()

        if choice == "1":
            recipe_key = ui.select_recipe()
            if recipe_key:
                run_recipe(recipe_key)

        elif choice == "2":
            task = ui.get_custom_task()
            run_custom_task(task)

        elif choice == "3":
            run_ai_qa()

        elif choice == "4":
            # Conversational AI agent
            from agent_chat import run_agent_chat
            run_agent_chat()

        elif choice == "5":
            # Virtual host manager
            from vhost_manager import add_vhost
            add_vhost()

        elif choice == "6":
            # Script writer
            from script_manager import write_script
            write_script()

        elif choice == "7":
            # Cron manager
            from script_manager import manage_crons
            manage_crons()

        elif choice == "8":
            change_settings()

        elif choice == "9":
            ui.show_usage_summary()

        elif choice == "0":
            print(f"\n  {ui.C.DIM}Goodbye!{ui.C.RESET}\n")
            sys.exit(0)


# ── CLI argument parser ────────────────────────────────────────────────────────

def build_parser():
    parser = argparse.ArgumentParser(
        prog="linuxagent",
        description="AI-powered Linux server management tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
SHORTCUTS:
  install <recipe>          Install a pre-built recipe
  task "<description>"      Run any task in plain English
  ask "<question>"          Get an instant AI answer
  chat                      Start conversational AI agent (multi-turn)
  vhost                     Add a new Nginx/Apache virtual host + SSL
  script                    Write a bash script with AI
  cron                      Manage cron jobs
  model                     Change AI model (all are free)
  usage                     Show token & credit usage stats
  list                      Show all recipes
  setup                     Re-run the first-time setup wizard

FLAGS:
  --yes / -y                Skip plan confirmation prompt
  --dry-run                 Print commands without executing them

ENVIRONMENT VARIABLES:
  OPENROUTER_API_KEY        Override stored API key
  LINUX_AGENT_MODEL         Override stored model
  LINUX_AGENT_DRY_RUN=1     Enable dry-run mode
  LINUX_AGENT_NO_COLOR=1    Disable ANSI colours
  NO_COLOR=1                Disable ANSI colours (standard)

EXAMPLES:
  python3 main.py install nginx
  python3 main.py install wordpress
  python3 main.py task "install and configure Jenkins"
  python3 main.py ask "how do I check open ports?"
  python3 main.py chat
  python3 main.py vhost
  python3 main.py script
  python3 main.py cron
  python3 main.py model
  python3 main.py usage
  python3 main.py --yes install docker
  python3 main.py --dry-run task "install nginx"
  python3 main.py list
        """,
    )

    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip the plan confirmation prompt",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands without executing them (also: LINUX_AGENT_DRY_RUN=1)",
    )

    subs = parser.add_subparsers(dest="command")

    p = subs.add_parser("install", help="Install a recipe")
    p.add_argument("recipe", help="Recipe name (use 'list' to see all)")

    p = subs.add_parser("task", help="Run a plain-English task")
    p.add_argument("description", nargs="+")

    p = subs.add_parser("ask", help="Ask AI a Linux question")
    p.add_argument("question", nargs="+")

    subs.add_parser("chat",   help="Conversational AI agent (multi-turn)")
    subs.add_parser("vhost",  help="Add Nginx/Apache virtual host + SSL")
    subs.add_parser("script", help="AI script writer")
    subs.add_parser("cron",   help="Cron job manager")
    subs.add_parser("list",   help="List all recipes")
    subs.add_parser("model",  help="Change AI model")
    subs.add_parser("usage",  help="Show token / credit usage")
    subs.add_parser("setup",  help="Re-run setup wizard")

    return parser


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    # ── Integrity Check ──────────────────────────────────────────────────────────
    expected_gh = "https://github.com/Vishalsoni2017"
    expected_li = "https://www.linkedin.com/in/vishal-soni-900b30133/"
    if (getattr(config, "CREATOR_NAME", "") != "Vishal Soni" or 
        getattr(config, "CREATOR_GITHUB", "") != expected_gh or 
        getattr(config, "CREATOR_LINKEDIN", "") != expected_li):
        print("\n\033[91m  [ERR] System Integrity Check Failed: Signature or author credentials have been modified.\033[0m\n")
        sys.exit(1)

    parser = build_parser()
    args   = parser.parse_args()

    # Honour --dry-run flag by setting the env var before executor is imported
    if getattr(args, "dry_run", False):
        os.environ["LINUX_AGENT_DRY_RUN"] = "1"

    if not args.command:
        try:
            interactive_mode()
        except KeyboardInterrupt:
            print(f"\n\n  {ui.C.DIM}Interrupted. Goodbye!{ui.C.RESET}\n")
        return

    if args.command != "setup":
        if not config.get("setup_done"):
            ui.banner()
            ui.warn("First-time setup required.")
            setup_wizard()

    auto_yes = getattr(args, "yes", False)

    if args.command == "install":
        ensure_setup()
        run_recipe(args.recipe, auto_yes=auto_yes)

    elif args.command == "task":
        ensure_setup()
        run_custom_task(" ".join(args.description), auto_yes=auto_yes)

    elif args.command == "ask":
        ensure_setup()
        run_ai_qa(question=" ".join(args.question))

    elif args.command == "chat":
        ensure_setup()
        from agent_chat import run_agent_chat
        run_agent_chat()

    elif args.command == "vhost":
        ensure_setup()
        from vhost_manager import add_vhost
        add_vhost()

    elif args.command == "script":
        ensure_setup()
        from script_manager import write_script
        write_script()

    elif args.command == "cron":
        ensure_setup()
        from script_manager import manage_crons
        manage_crons()

    elif args.command == "model":
        current  = config.get_model()
        model_id = ui.select_model(current)
        config.set_model(model_id)
        ui.success(f"Model set to: {model_id}")

    elif args.command == "usage":
        ui.show_usage_summary()

    elif args.command == "list":
        list_recipes()

    elif args.command == "setup":
        ui.banner()
        setup_wizard()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n  {ui.C.DIM}Interrupted. Goodbye!{ui.C.RESET}\n")
        sys.exit(0)
