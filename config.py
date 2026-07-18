"""
Configuration manager for Linux Agentic Tool.
Stores OS type, API key, model choice, and settings permanently
in ~/.linux_agent/config.json

Improvements:
  - In-memory cache: config is only read from disk once per session
  - OPENROUTER_API_KEY env var is checked before the config file
  - LINUX_AGENT_MODEL env var can override the stored model
  - Cache is invalidated whenever save_config() is called
"""

import json
import os
from pathlib import Path

CONFIG_DIR  = Path.home() / ".linux_agent"
CONFIG_FILE = CONFIG_DIR / "config.json"

# ── In-memory cache ─────────────────────────────────────────────────────────────
_cache: dict | None = None  # None means "not loaded yet"


def _invalidate_cache():
    """Drop the in-memory copy so next get() re-reads from disk."""
    global _cache
    _cache = None


def ensure_config_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    """
    Load config from disk (or return the cached copy).
    Environment-variable overrides are applied on top:
      OPENROUTER_API_KEY → api_key
      LINUX_AGENT_MODEL  → model
    """
    global _cache
    if _cache is not None:
        return _cache

    ensure_config_dir()
    data: dict = {}
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            data = {}

    # Apply environment-variable overrides (never persisted to disk)
    env_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if env_key:
        data["api_key"] = env_key

    env_model = os.environ.get("LINUX_AGENT_MODEL", "").strip()
    if env_model:
        data["model"] = env_model

    _cache = data
    return _cache


def save_config(data: dict):
    """Merge *data* into the on-disk config, then invalidate the cache."""
    ensure_config_dir()
    existing = {}
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except (json.JSONDecodeError, IOError):
            existing = {}

    existing.update(data)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)

    # Restrict permissions so API key is not world-readable
    try:
        os.chmod(CONFIG_FILE, 0o600)
    except Exception:
        pass  # Windows does not support chmod

    _invalidate_cache()


def get(key: str, default=None):
    return load_config().get(key, default)


def set_value(key: str, value):
    save_config({key: value})


# ── Supported OS list ────────────────────────────────────────────────────────────
SUPPORTED_OS = [
    "Ubuntu 20.04",
    "Ubuntu 22.04",
    "Ubuntu 24.04 LTS",
    "Debian 11",
    "Debian 12",
    "CentOS 7",
    "CentOS Stream 8",
    "CentOS Stream 9",
    "Rocky Linux 8",
    "Rocky Linux 9",
    "AlmaLinux 8",
    "AlmaLinux 9",
    "Fedora 38+",
    "RHEL 8",
    "RHEL 9",
    "Arch Linux",
    "openSUSE Leap",
]

# ── Package manager map ──────────────────────────────────────────────────────────
OS_PACKAGE_MANAGER = {
    "ubuntu":    "apt",
    "debian":    "apt",
    "centos":    "yum",
    "rocky":     "dnf",
    "almalinux": "dnf",
    "fedora":    "dnf",
    "rhel":      "dnf",
    "arch":      "pacman",
    "opensuse":  "zypper",
}


def get_package_manager(os_name: str) -> str:
    lower = os_name.lower()
    for family, pm in OS_PACKAGE_MANAGER.items():
        if family in lower:
            return pm
    return "apt"


# ── Available models ─────────────────────────────────────────────────────────────
# All are FREE on OpenRouter (no credits consumed).
# Format: (display_name, model_id, description)
AVAILABLE_MODELS = [
    (
        "openrouter/auto  [DEFAULT]",
        "openrouter/auto",
        "OpenRouter auto-selects the best free model for each request",
    ),
    (
        "deepseek/deepseek-r1:free",
        "deepseek/deepseek-r1:free",
        "DeepSeek R1 — strong reasoning, great for complex Linux tasks",
    ),
    (
        "deepseek/deepseek-chat:free",
        "deepseek/deepseek-chat:free",
        "DeepSeek V3 Chat — fast, good for general tasks",
    ),
    (
        "meta-llama/llama-3.3-70b-instruct:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "Llama 3.3 70B — Meta's latest large open model",
    ),
    (
        "meta-llama/llama-3.1-8b-instruct:free",
        "meta-llama/llama-3.1-8b-instruct:free",
        "Llama 3.1 8B — lightweight, fast responses",
    ),
    (
        "google/gemma-3-27b-it:free",
        "google/gemma-3-27b-it:free",
        "Google Gemma 3 27B — strong instruction-following",
    ),
    (
        "mistralai/mistral-7b-instruct:free",
        "mistralai/mistral-7b-instruct:free",
        "Mistral 7B — fast and capable for scripting tasks",
    ),
    (
        "qwen/qwen-2.5-72b-instruct:free",
        "qwen/qwen-2.5-72b-instruct:free",
        "Qwen 2.5 72B — excellent at code and commands",
    ),
    (
        "microsoft/phi-3-medium-128k-instruct:free",
        "microsoft/phi-3-medium-128k-instruct:free",
        "Microsoft Phi-3 Medium — 128K context window",
    ),
]

DEFAULT_MODEL = "openrouter/auto"


def get_model() -> str:
    """Return the currently configured model ID, defaulting to openrouter/auto."""
    return get("model", DEFAULT_MODEL)


def set_model(model_id: str):
    set_value("model", model_id)


# ── Token usage tracking ─────────────────────────────────────────────────────────
# Accumulated across the session in memory; also persisted to config.

_session_tokens = {"prompt": 0, "completion": 0, "total": 0, "calls": 0}


def record_usage(prompt_tokens: int, completion_tokens: int, total_tokens: int):
    """Called after every API call to accumulate token counts."""
    _session_tokens["prompt"]     += prompt_tokens
    _session_tokens["completion"] += completion_tokens
    _session_tokens["total"]      += total_tokens
    _session_tokens["calls"]      += 1

    # Persist lifetime totals (load from disk directly, bypassing cache)
    existing = {}
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    lifetime = existing.get(
        "lifetime_tokens", {"prompt": 0, "completion": 0, "total": 0, "calls": 0}
    )
    lifetime["prompt"]     += prompt_tokens
    lifetime["completion"] += completion_tokens
    lifetime["total"]      += total_tokens
    lifetime["calls"]      += 1

    ensure_config_dir()
    existing["lifetime_tokens"] = lifetime
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)
    # Do NOT invalidate cache here — avoids re-reading just for usage counters


def get_session_usage() -> dict:
    return dict(_session_tokens)


def get_lifetime_usage() -> dict:
    return load_config().get(
        "lifetime_tokens", {"prompt": 0, "completion": 0, "total": 0, "calls": 0}
    )
