# -*- coding: utf-8 -*-
"""
Terminal UI helpers - menus, dropdowns, banners.

Improvements:
  - Removed global sys.stdout reassignment (was breaking subprocess pipes)
  - Added LINUX_AGENT_NO_COLOR env var support for piped / CI usage
  - Banner now shows the currently-configured model
"""

import sys
import os

# Reconfigure stdout/stderr to replace unsupported characters instead of throwing UnicodeEncodeError on Windows/legacy terminals
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(errors="replace")
    except Exception:
        pass

# ── Color support ─────────────────────────────────────────────────────────────
# Respect NO_COLOR standard (https://no-color.org/) and custom env var
_NO_COLOR = (
    os.environ.get("LINUX_AGENT_NO_COLOR", "")
    or os.environ.get("NO_COLOR", "")
    or not sys.stdout.isatty()
)


class C:
    if _NO_COLOR:
        RESET = GREEN = RED = YELLOW = BLUE = CYAN = WHITE = BOLD = DIM = ""
    else:
        RESET  = "\033[0m"
        RED    = "\033[91m"
        GREEN  = "\033[92m"
        YELLOW = "\033[93m"
        BLUE   = "\033[94m"
        CYAN   = "\033[96m"
        WHITE  = "\033[97m"
        BOLD   = "\033[1m"
        DIM    = "\033[2m"


from config import SUPPORTED_OS, AVAILABLE_MODELS, DEFAULT_MODEL, CREATOR_NAME, CREATOR_GITHUB, CREATOR_LINKEDIN
from recipes import RECIPES, CATEGORIES, get_recipes_by_category

VERSION = "2.0"


def banner():
    import config as cfg
    model = cfg.get_model()
    print(C.CYAN + C.BOLD)
    print(" ===================================================")
    print(f"    LINUX AGENTIC TOOL v{VERSION}")
    print("    AI-Powered Linux Server Management")
    print(f"    👤 Creator:  {CREATOR_NAME}")
    print(f"    🐙 GitHub:   {CREATOR_GITHUB}")
    print(f"    🔗 LinkedIn: {CREATOR_LINKEDIN}")
    print(" ===================================================")
    print(f"    🤖 Active model: {model}")
    print(" ===================================================")
    print(C.RESET)


def section(title):
    print("\n" + C.CYAN + C.BOLD + "=" * 60 + C.RESET)
    print(C.CYAN + C.BOLD + "  " + title + C.RESET)
    print(C.CYAN + C.BOLD + "=" * 60 + C.RESET + "\n")


def success(msg):
    print(C.GREEN + "  ✅ [OK]  " + msg + C.RESET)


def warn(msg):
    print(C.YELLOW + "  ⚠️  [!]   " + msg + C.RESET)


def error(msg):
    print(C.RED + "  ❌ [ERR] " + msg + C.RESET)


def info(msg):
    print(C.CYAN + "  ℹ️  [i]   " + msg + C.RESET)


# OS Dropdown
def select_os():
    section("Select Your Linux Distribution")
    for i, os_name in enumerate(SUPPORTED_OS, start=1):
        print("  " + C.YELLOW + str(i).rjust(2) + C.RESET + ". " + os_name)

    while True:
        raw = input(
            "\n" + C.BOLD + "  Enter number (1-" + str(len(SUPPORTED_OS)) + "): " + C.RESET
        ).strip()
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(SUPPORTED_OS):
                return SUPPORTED_OS[idx]
        print(
            "  " + C.RED + "Invalid choice. Please enter a number between 1 and "
            + str(len(SUPPORTED_OS)) + "." + C.RESET
        )


# API Key Entry
def enter_api_key():
    section("OpenRouter API Key Setup")
    print("  Get your FREE API key at: " + C.CYAN + "https://openrouter.ai/keys" + C.RESET)
    print(
        "  " + C.DIM + "The key is stored locally in ~/.linux_agent/config.json" + C.RESET
    )
    print(
        "  " + C.DIM
        + "You can also set the OPENROUTER_API_KEY environment variable." + C.RESET + "\n"
    )

    while True:
        key = input("  " + C.BOLD + "Paste your OpenRouter API key: " + C.RESET).strip()
        if key.startswith("sk-") and len(key) > 20:
            return key
        warn("Key should start with 'sk-' and be at least 20 characters. Try again.")


# Main Menu
def main_menu():
    section("Main Menu")
    options = [
        ("1", "[PKG]    Install from recipe (Nginx, WordPress, Docker, Prometheus...)"),
        ("2", "[AI]     Custom task (describe anything in plain English)"),
        ("3", "[Q&A]    Ask AI a question about Linux"),
        ("4", "[CHAT]   Conversational AI agent (multi-turn)"),
        ("5", "[VHOST]  Add Nginx / Apache virtual host + SSL"),
        ("6", "[SCRIPT] Write a bash script with AI"),
        ("7", "[CRON]   Manage cron jobs"),
        ("8", "[CFG]    Settings (OS / API key / Model)"),
        ("9", "[STATS]  View token & credit usage"),
        ("0", "[EXIT]   Exit"),
    ]
    for key, label in options:
        print("  " + C.YELLOW + key + C.RESET + ". " + label)

    while True:
        choice = input("\n" + C.BOLD + "  Choose an option: " + C.RESET).strip()
        if choice in [o[0] for o in options]:
            return choice
        print("  " + C.RED + "Invalid choice." + C.RESET)


# Model selector
def select_model(current_model: str = DEFAULT_MODEL) -> str:
    section("Select AI Model")
    print("  " + C.DIM + "All models below are FREE on OpenRouter." + C.RESET)
    print("  " + C.DIM + "Current model: " + C.YELLOW + current_model + C.RESET + "\n")

    for i, (display, model_id, description) in enumerate(AVAILABLE_MODELS, start=1):
        marker = " <-- active" if model_id == current_model else ""
        print(
            "  " + C.YELLOW + str(i).rjust(2) + C.RESET + ". "
            + C.BOLD + display + C.RESET
            + C.DIM + marker + C.RESET
        )
        print("       " + C.DIM + description + C.RESET)

    print()
    while True:
        raw = input(
            C.BOLD + "  Enter number (1-" + str(len(AVAILABLE_MODELS)) + "): " + C.RESET
        ).strip()
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(AVAILABLE_MODELS):
                _, model_id, _ = AVAILABLE_MODELS[idx]
                return model_id
        print("  " + C.RED + "Invalid choice." + C.RESET)


# Token / credit usage display
def show_usage_summary():
    import config as cfg
    session  = cfg.get_session_usage()
    lifetime = cfg.get_lifetime_usage()

    section("Token Usage")
    print("  " + C.BOLD + "This session:" + C.RESET)
    print("  " + C.CYAN + "  API calls  : " + str(session["calls"])      + C.RESET)
    print("  " + C.CYAN + "  Prompt     : " + str(session["prompt"])     + " tokens" + C.RESET)
    print("  " + C.CYAN + "  Completion : " + str(session["completion"]) + " tokens" + C.RESET)
    print("  " + C.CYAN + "  Total      : " + str(session["total"])      + " tokens" + C.RESET)

    print()
    print("  " + C.BOLD + "Lifetime (all sessions):" + C.RESET)
    print("  " + C.DIM  + "  API calls  : " + str(lifetime["calls"])      + C.RESET)
    print("  " + C.DIM  + "  Prompt     : " + str(lifetime["prompt"])     + " tokens" + C.RESET)
    print("  " + C.DIM  + "  Completion : " + str(lifetime["completion"]) + " tokens" + C.RESET)
    print("  " + C.DIM  + "  Total      : " + str(lifetime["total"])      + " tokens" + C.RESET)
    print()
    print("  " + C.DIM + "Note: All models used are FREE — $0.00 cost." + C.RESET)


# Recipe Menu
def select_recipe():
    section("Available Installation Recipes")
    grouped = get_recipes_by_category()
    numbered = []

    for cat_key, cat_label in CATEGORIES.items():
        recipes_in_cat = grouped.get(cat_key, {})
        if not recipes_in_cat:
            continue
        print("\n  " + C.BOLD + cat_label + C.RESET)
        for key, recipe in recipes_in_cat.items():
            num = len(numbered) + 1
            numbered.append(key)
            name_padded = recipe["name"].ljust(30)
            print(
                "    " + C.YELLOW + str(num).rjust(2) + C.RESET + ". "
                + name_padded + "  " + C.DIM + recipe["description"] + C.RESET
            )

    print("\n    " + C.YELLOW + " 0" + C.RESET + ". <- Back")

    while True:
        raw = input("\n" + C.BOLD + "  Enter number: " + C.RESET).strip()
        if raw == "0":
            return None
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(numbered):
                return numbered[idx]
        print("  " + C.RED + "Invalid choice." + C.RESET)


# Custom Task Input
def get_custom_task():
    section("Custom Task")
    print("  " + C.DIM + "Describe what you want to install or configure in plain English." + C.RESET)
    print("  " + C.DIM + "Examples:" + C.RESET)
    print("  " + C.DIM + "  * Install Jenkins CI server" + C.RESET)
    print("  " + C.DIM + "  * Install and configure a LAMP stack" + C.RESET)
    print("  " + C.DIM + "  * Set up a Python Flask app with Gunicorn and Nginx" + C.RESET + "\n")

    while True:
        task = input("  " + C.BOLD + "Your task: " + C.RESET).strip()
        if task:
            return task
        print("  " + C.RED + "Task cannot be empty." + C.RESET)
