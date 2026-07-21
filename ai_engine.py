# -*- coding: utf-8 -*-
"""
AI Engine
=========
Talks to the OpenRouter API. Every call:
  - Uses the model stored in config (default: openrouter/auto — free)
  - Prints a token/credit usage line after the response
  - Accumulates session + lifetime token totals

Improvements:
  - Robust JSON / markdown-fence stripping with regex
  - Exponential-backoff retry (3 attempts) for transient network errors
  - max_tokens cap to avoid runaway usage on free models
  - Conversation-history-aware ask function
"""

import json
import re
import time
import requests
from config import get, get_model, record_usage, CREATOR_NAME, CREATOR_GITHUB

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# ANSI colours (kept here so ai_engine stays self-contained)
_CYAN   = "\033[96m"
_DIM    = "\033[2m"
_RESET  = "\033[0m"
_YELLOW = "\033[93m"
_RED    = "\033[91m"

# Maximum tokens to request per call (avoids runaway on free models)
MAX_TOKENS = 2048

# Retry settings
_MAX_RETRIES   = 3
_RETRY_BACKOFF = 2  # seconds (doubles each attempt)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _strip_markdown_fences(text: str) -> str:
    """
    Robustly strip leading/trailing markdown code fences.

    Handles all of:
      ```json\\n...\\n```
      ```\\n...\\n```
      ``` json ... ```   (single-line)
    Returns the inner content with surrounding whitespace stripped.
    """
    # Match an optional opening fence with optional language tag, capture inner content,
    # then an optional closing fence.
    pattern = re.compile(
        r"^\s*```[a-zA-Z]*\s*\n?(.*?)\n?\s*```\s*$",
        re.DOTALL,
    )
    m = pattern.match(text.strip())
    if m:
        return m.group(1).strip()
    return text.strip()


def _print_usage(usage: dict, model_used: str):
    """Print a compact token-usage line after every API call."""
    pt   = usage.get("prompt_tokens",     0)
    ct   = usage.get("completion_tokens", 0)
    tt   = usage.get("total_tokens",      0)
    cost = usage.get("total_cost",        None)

    cost_str = ""
    if cost is not None:
        if float(cost) == 0:
            cost_str = "  cost: $0.00 (free)"
        else:
            cost_str = f"  cost: ${float(cost):.6f}"

    print(
        f"\n  {_DIM}[tokens]  "
        f"prompt: {pt}  "
        f"completion: {ct}  "
        f"total: {tt}"
        f"{cost_str}  "
        f"model: {model_used}"
        f"{_RESET}"
    )


def _call_api(
    messages: list,
    temperature: float = 0.2,
    max_tokens: int = MAX_TOKENS,
) -> str:
    """
    Core API call with retry logic.
    Returns the assistant's reply text.
    Prints token usage and records it in config.
    """
    api_key = get("api_key")
    if not api_key:
        raise ValueError(
            "No API key configured. Run the tool and set your OpenRouter key first.\n"
            "You can also set the OPENROUTER_API_KEY environment variable."
        )

    model = get_model()

    headers = {
        "Authorization":  f"Bearer {api_key}",
        "Content-Type":   "application/json",
        "HTTP-Referer":   CREATOR_GITHUB,
        "X-Title":        f"Linux Agentic Tool by {CREATOR_NAME}",
    }

    payload = {
        "model":       model,
        "messages":    messages,
        "temperature": temperature,
        "max_tokens":  max_tokens,
    }

    last_error = RuntimeError("API request failed after all retries.")
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            resp = requests.post(
                OPENROUTER_API_URL,
                headers=headers,
                json=payload,
                timeout=90,
            )
            resp.raise_for_status()
            data = resp.json()
            break  # success — exit retry loop

        except requests.exceptions.HTTPError as e:
            status = e.response.status_code
            body   = e.response.text
            # 4xx errors are not retryable (bad key, bad model, etc.)
            if 400 <= status < 500:
                raise RuntimeError(
                    f"API request failed [{status}]: {body}"
                ) from e
            last_error = RuntimeError(f"API request failed [{status}]: {body}")

        except requests.exceptions.Timeout:
            last_error = RuntimeError(
                f"API request timed out (attempt {attempt}/{_MAX_RETRIES})"
            )

        except requests.exceptions.ConnectionError as e:
            last_error = RuntimeError(f"Network connection error: {e}")

        except Exception as e:
            raise RuntimeError(f"Unexpected API error: {e}") from e

        # Retryable error — wait and try again
        if attempt < _MAX_RETRIES:
            wait = _RETRY_BACKOFF * (2 ** (attempt - 1))
            print(
                f"  {_YELLOW}[!] API error — retrying in {wait}s "
                f"(attempt {attempt}/{_MAX_RETRIES})...{_RESET}"
            )
            time.sleep(wait)
    else:
        raise last_error  # all retries exhausted

    # ── Extract reply ──────────────────────────────────────────────────────
    choices = data.get("choices", [])
    if not choices:
        raise RuntimeError("API returned no choices in response.")

    reply = choices[0]["message"]["content"].strip()

    # ── Extract and display usage ──────────────────────────────────────────
    usage = data.get("usage", {})
    pt    = int(usage.get("prompt_tokens",     0))
    ct    = int(usage.get("completion_tokens", 0))
    tt    = int(usage.get("total_tokens", 0) or (pt + ct))

    # Actual model used (OpenRouter may route differently when using /auto)
    model_used = (
        data.get("model")
        or choices[0].get("model")
        or model
    )

    # Attach cost if returned at top level
    if "total_cost" not in usage and "cost" in data:
        usage["total_cost"] = data["cost"]

    _print_usage(
        {**usage, "prompt_tokens": pt, "completion_tokens": ct, "total_tokens": tt},
        model_used,
    )
    record_usage(pt, ct, tt)

    return reply


# ── Public API ─────────────────────────────────────────────────────────────────

def get_install_commands(task: str, os_name: str, package_manager: str) -> dict:
    """
    Ask AI to generate commands for a task.
    Returns: {"description": str, "commands": [str], "warnings": str}
    """
    system_prompt = (
        f"You are a Linux system administration expert.\n"
        f"The user is running: {os_name}\n"
        f"Package manager: {package_manager}\n\n"
        "Return a JSON object with these keys:\n"
        '- "description": short one-line summary of what will be done\n'
        '- "commands": array of shell command strings to execute IN ORDER\n'
        '- "warnings": any important notes (empty string if none)\n\n'
        "Rules:\n"
        "- Use the correct package manager for the OS\n"
        "- Include all dependencies needed. If the tool is a Java application (like Jenkins, Tomcat), "
        "always ensure a compatible, modern Java Runtime (like OpenJDK 17 or 11) is installed first.\n"
        "- If a specific version preference (LTS, latest, or specific version tag) is specified in the task, "
        "modify the repository settings or package names to install that specific version.\n"
        "- Commands must be non-interactive (-y flags, DEBIAN_FRONTEND=noninteractive, etc.)\n"
        "- Do NOT use sudo (the tool will prefix sudo when needed)\n"
        "- Return ONLY valid JSON, no markdown, no explanation outside JSON"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": f"Task: {task}"},
    ]

    raw = _call_api(messages)
    raw = _strip_markdown_fences(raw)

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {
            "description": task,
            "commands":    [raw],
            "warnings":    "AI returned unstructured output — review carefully before executing",
        }

    return result


def fix_error(command: str, error_output: str, os_name: str, package_manager: str) -> dict:
    """
    Diagnose a failed command and return fix commands.
    Returns: {"diagnosis": str, "fix_commands": [str]}
    """
    system_prompt = (
        f"You are a Linux troubleshooting expert.\n"
        f"The user is running: {os_name}\n"
        f"Package manager: {package_manager}\n\n"
        "A command failed. Return a JSON object with:\n"
        '- "diagnosis": short explanation of what went wrong\n'
        '- "fix_commands": array of shell commands to fix the issue (in order)\n\n'
        "Rules:\n"
        "- Use the correct package manager for the OS\n"
        "- Commands must be non-interactive\n"
        "- Do NOT use sudo (the tool will add it)\n"
        "- Return ONLY valid JSON"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": f"Failed command:\n{command}\n\nError output:\n{error_output}",
        },
    ]

    raw = _call_api(messages)
    raw = _strip_markdown_fences(raw)

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {"diagnosis": "Could not parse AI response", "fix_commands": []}

    return result


def ask_ai(question: str, os_name: str) -> str:
    """General Q&A — returns plain-text answer."""
    messages = [
        {
            "role":    "system",
            "content": (
                f"You are a helpful Linux expert. "
                f"The user is on {os_name}. Be concise and practical."
            ),
        },
        {"role": "user", "content": question},
    ]
    return _call_api(messages, temperature=0.4)


def ask_ai_with_history(history: list, os_name: str) -> str:
    """
    Multi-turn conversational AI call.

    `history` is a list of OpenAI-compatible message dicts:
      [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}, ...]

    A system message is prepended automatically.
    Returns the assistant's latest reply (plain text).
    """
    system_msg = {
        "role":    "system",
        "content": (
            f"You are an expert Linux system administrator and engineer. "
            f"The user is running {os_name}. "
            "Help them with any Linux administration, scripting, debugging, "
            "or configuration task. Be concise, accurate, and practical. "
            "When you suggest commands, explain briefly what each does."
        ),
    }
    messages = [system_msg] + history
    return _call_api(messages, temperature=0.5, max_tokens=2048)


def get_diagnostic_commands(issue: str, os_name: str, package_manager: str) -> list:
    """
    Ask AI what commands to run to inspect logs, configs, ports, or service status
    for a given issue.
    """
    system_prompt = (
        f"You are a Linux troubleshooting expert.\n"
        f"The user is running: {os_name}\n"
        f"Package manager: {package_manager}\n\n"
        "Recommend 2 to 4 non-interactive shell commands (e.g. journalctl -u service -n 50, "
        "cat /var/log/path, ss -tuln, service status) to inspect log files, check configuration files, "
        "or ports to troubleshoot the user's issue.\n"
        "Return ONLY a JSON array of strings containing the commands. No other text."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": f"Issue: {issue}"},
    ]

    raw = _call_api(messages, temperature=0.1)
    raw = _strip_markdown_fences(raw)

    try:
        commands = json.loads(raw)
        if not isinstance(commands, list):
            commands = [raw]
    except json.JSONDecodeError:
        commands = []
    return commands


def analyze_diagnostic_data(issue: str, gathered_data: str, os_name: str, package_manager: str) -> dict:
    """
    Analyze logs, configs, and output gathered on the server and return a diagnosis and fix plan.
    """
    system_prompt = (
        f"You are a Linux diagnostics expert.\n"
        f"The user is running: {os_name}\n"
        f"Package manager: {package_manager}\n\n"
        "Analyze the gathered server diagnostics data (command outputs, logs, configs) and return a JSON object with:\n"
        '- "diagnosis": clear, detailed explanation of the root cause\n'
        '- "fix_commands": array of shell command strings to run (in order) to solve the issue. Commands must be non-interactive. Do not use sudo.\n\n'
        "Return ONLY valid JSON, no markdown, no other text."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": f"User Issue:\n{issue}\n\nGathered Diagnostics Data:\n{gathered_data}"},
    ]

    raw = _call_api(messages, temperature=0.2)
    raw = _strip_markdown_fences(raw)

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {
            "diagnosis": "Failed to parse AI response. Raw response:\n" + raw,
            "fix_commands": []
        }
    return result
