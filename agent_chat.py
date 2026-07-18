# -*- coding: utf-8 -*-
"""
agent_chat.py
=============
Conversational AI agent with persistent multi-turn history.

Features:
  - Full conversation history sent to the AI on every turn
  - Context continuity: AI remembers what was said earlier in the session
  - Special commands:
      history   — show conversation so far
      clear     — start a fresh conversation
      save      — save conversation to a file
      load      — load a previous conversation
      help      — show commands
      exit/back — return to the main menu
  - Conversation saved as JSON (role/content pairs)

Usage from main.py:
    from agent_chat import run_agent_chat
    run_agent_chat()
"""

import json
import os
from datetime import datetime
from pathlib import Path

import config
import ui
from ai_engine import ask_ai_with_history

# Directory to save conversation logs
CHAT_LOG_DIR = Path.home() / ".linux_agent" / "chats"
CHAT_LOG_DIR.mkdir(parents=True, exist_ok=True)

_SPECIAL_COMMANDS = {
    "help":    "Show available commands",
    "history": "Print conversation history",
    "clear":   "Start a new conversation (clears history)",
    "save":    "Save conversation to ~/.linux_agent/chats/<name>.json",
    "load":    "Load a saved conversation",
    "exit":    "Return to main menu",
    "back":    "Return to main menu",
    "quit":    "Return to main menu",
}


def _print_help():
    print(f"\n  {ui.C.BOLD}Special commands:{ui.C.RESET}")
    for cmd, desc in _SPECIAL_COMMANDS.items():
        print(f"  {ui.C.YELLOW}{cmd:<10}{ui.C.RESET} — {desc}")
    print()


def _print_history(history: list):
    if not history:
        print(f"  {ui.C.DIM}No conversation history yet.{ui.C.RESET}\n")
        return
    print()
    for msg in history:
        role = msg["role"]
        content = msg["content"]
        if role == "user":
            print(f"  {ui.C.BOLD}{ui.C.YELLOW}You:{ui.C.RESET}  {content}")
        else:
            print(f"  {ui.C.CYAN}AI:{ui.C.RESET}   {content}")
        print()


def _save_conversation(history: list):
    if not history:
        ui.warn("Nothing to save.")
        return
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    default_name = f"chat_{timestamp}"
    name = input(
        f"  {ui.C.BOLD}Save as [{default_name}]: {ui.C.RESET}"
    ).strip() or default_name

    if not name.endswith(".json"):
        name += ".json"

    path = CHAT_LOG_DIR / name
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    ui.success(f"Conversation saved to {path}")


def _load_conversation() -> list:
    files = sorted(CHAT_LOG_DIR.glob("*.json"))
    if not files:
        ui.warn("No saved conversations found.")
        return []

    print(f"\n  {ui.C.BOLD}Saved conversations:{ui.C.RESET}")
    for i, f in enumerate(files, 1):
        print(f"  {ui.C.YELLOW}{i}{ui.C.RESET}. {f.name}")
    print(f"  {ui.C.YELLOW}0{ui.C.RESET}. Cancel\n")

    while True:
        raw = input(f"  {ui.C.BOLD}Load number: {ui.C.RESET}").strip()
        if raw == "0":
            return []
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(files):
                with open(files[idx], "r", encoding="utf-8") as f:
                    history = json.load(f)
                ui.success(f"Loaded {files[idx].name} ({len(history)} messages)")
                return history
        print("  Invalid choice.")


# ── Main chat loop ─────────────────────────────────────────────────────────────

def run_agent_chat():
    """
    Start an interactive multi-turn conversation with the Linux AI agent.
    Maintains full message history so the AI has context from previous turns.
    """
    ui.section("Conversational AI Agent")
    os_name = config.get("os_name", "Linux")
    model   = config.get_model()

    print(f"  {ui.C.DIM}Multi-turn Linux AI assistant. OS: {os_name}  |  model: {model}{ui.C.RESET}")
    print(f"  {ui.C.DIM}Type your question or command. Type 'help' for special commands.{ui.C.RESET}\n")

    history: list = []  # list of {"role": "user"|"assistant", "content": str}

    while True:
        try:
            user_input = input(
                f"  {ui.C.BOLD}{ui.C.GREEN}You{ui.C.RESET}{ui.C.BOLD} > {ui.C.RESET}"
            ).strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n  {ui.C.DIM}Returning to main menu.{ui.C.RESET}")
            return

        if not user_input:
            continue

        lower = user_input.lower()

        # ── Special commands ───────────────────────────────────────────────
        if lower in ("exit", "back", "quit"):
            print(f"\n  {ui.C.DIM}Returning to main menu.{ui.C.RESET}\n")
            return

        elif lower == "help":
            _print_help()
            continue

        elif lower == "history":
            _print_history(history)
            continue

        elif lower == "clear":
            history = []
            ui.success("Conversation cleared. Starting fresh.")
            continue

        elif lower == "save":
            _save_conversation(history)
            continue

        elif lower == "load":
            loaded = _load_conversation()
            if loaded:
                history = loaded
                print(f"\n  {ui.C.DIM}Conversation loaded. Continuing from where it left off.{ui.C.RESET}\n")
                _print_history(history)
            continue

        # ── Regular AI turn ────────────────────────────────────────────────
        history.append({"role": "user", "content": user_input})

        print(f"\n  {ui.C.DIM}Thinking...{ui.C.RESET}")
        try:
            reply = ask_ai_with_history(history, os_name)
        except Exception as e:
            ui.error(f"AI error: {e}")
            # Remove the last user message so the user can retry
            history.pop()
            continue

        history.append({"role": "assistant", "content": reply})

        print(f"\n  {ui.C.CYAN}{ui.C.BOLD}AI:{ui.C.RESET}")
        # Word-wrap the reply for narrow terminals
        for line in reply.split("\n"):
            print(f"  {ui.C.CYAN}{line}{ui.C.RESET}")
        print()
