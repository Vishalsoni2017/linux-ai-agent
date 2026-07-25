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


def _extract_json(text: str) -> dict | None:
    """
    Robustly extract the first JSON object from the response string,
    even if surrounded by markdown fences or introductory/conversational text.
    """
    text_stripped = _strip_markdown_fences(text)
    
    # Try direct parse first
    try:
        return json.loads(text_stripped)
    except json.JSONDecodeError:
        pass

    # Try finding outermost braces
    start = text_stripped.find('{')
    end = text_stripped.rfind('}')
    if start != -1 and end != -1 and end > start:
        candidate = text_stripped[start:end+1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    return None


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
        f"You are a senior Linux DevOps engineer. Target OS: {os_name}. Package manager: {package_manager}.\n\n"
        "Produce a one-shot installation plan that succeeds the FIRST time with ZERO manual input.\n\n"
        "Return ONLY a JSON object with these exact keys:\n"
        '- "description": one-line summary\n'
        '- "commands": array of shell command strings to execute IN ORDER\n'
        '- "warnings": notes (empty string if none)\n\n'

        "╔══════════════════════════════════════════════════════════════════╗\n"
        "║  CRITICAL SHELL RULES — violating these WILL break execution     ║\n"
        "╚══════════════════════════════════════════════════════════════════╝\n\n"

        "RULE A — NO STANDALONE VARIABLE ASSIGNMENTS:\n"
        "  Each command in the list runs in its own subprocess. Shell variables DO NOT\n"
        "  persist between commands. NEVER do this across two list entries:\n"
        "    ✗ BAD:  commands = ['VER=$(curl ...)', 'curl .../terraform_${VER}...']\n"
        "  If you need a variable, merge everything into ONE bash -c block:\n"
        '    ✓ GOOD: commands = ["bash -c \'VER=$(curl ...); curl .../terraform_${VER}...\'"]\n\n'

        "RULE B — DYNAMIC OS CODENAME:\n"
        "  NEVER hardcode 'bullseye', 'bookworm', 'focal', 'jammy', 'bionic'.\n"
        "  Use: $(. /etc/os-release && echo $VERSION_CODENAME)\n\n"

        "RULE C — PREREQUISITES FIRST:\n"
        "  If you need curl, wget, gpg, unzip, tar — install them in the FIRST command.\n\n"

        "RULE D — NO BLOAT PACKAGES:\n"
        "  Never install 'software-properties-common', 'python-apt'. Use echo|tee for sources.\n\n"

        "RULE E — COMBINE RELATED apt-get CALLS:\n"
        "  'apt-get install -y curl gpg unzip' — one call, not three.\n\n"

        "RULE F — NO SUDO PREFIX:\n"
        "  The executor adds sudo automatically. Never write 'sudo' in your commands.\n\n"

        "RULE G — MERGE MULTI-STEP LOGIC:\n"
        "  If an install needs: add key → add repo → apt update → apt install,\n"
        "  merge into the FEWEST possible commands using && chains.\n\n"

        "╔══════════════════════════════════════════════════════════════════╗\n"
        "║  OFFICIAL INSTALL RECIPES — use EXACTLY these approaches         ║\n"
        "╚══════════════════════════════════════════════════════════════════╝\n\n"

        "DOCKER (Ubuntu & Debian — official apt method, single block):\n"
        "  Use these EXACT commands, in this EXACT order (all as one bash -c block):\n"
        "  bash -c '\n"
        "    apt-get update -y && apt-get install -y ca-certificates curl;\n"
        "    install -m 0755 -d /etc/apt/keyrings;\n"
        "    curl -fsSL https://download.docker.com/linux/$(. /etc/os-release && echo $ID)/gpg -o /etc/apt/keyrings/docker.asc;\n"
        "    chmod a+r /etc/apt/keyrings/docker.asc;\n"
        "    echo \"deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/$(. /etc/os-release && echo $ID) $(. /etc/os-release && echo ${UBUNTU_CODENAME:-$VERSION_CODENAME}) stable\" | tee /etc/apt/sources.list.d/docker.list > /dev/null;\n"
        "    apt-get update -y && apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin;\n"
        "    systemctl enable docker && systemctl start docker\n"
        "  '\n"
        "  IMPORTANT: The $(. /etc/os-release && echo $ID) detects ubuntu vs debian automatically.\n"
        "  IMPORTANT: /etc/apt/keyrings MUST be created with 'install -m 0755 -d' BEFORE curl writes to it.\n"
        "  IMPORTANT: Use '.asc' extension (not '.gpg') — saves the raw PEM key, no gpg --dearmor needed.\n\n"

        "TERRAFORM (latest, single block):\n"
        "  bash -c '\n"
        "    apt-get install -y curl unzip python3;\n"
        '    TF_VER=$(curl -fsSL https://checkpoint-api.hashicorp.com/v1/check/terraform | python3 -c \'import sys,json;d=json.load(sys.stdin);print(d["current_version"])\');\n'
        "    curl -fsSL https://releases.hashicorp.com/terraform/${TF_VER}/terraform_${TF_VER}_linux_amd64.zip -o /tmp/terraform.zip;\n"
        "    unzip -o /tmp/terraform.zip -d /usr/local/bin terraform;\n"
        "    rm -f /tmp/terraform.zip;\n"
        "    chmod +x /usr/local/bin/terraform\n"
        "  '\n\n"

        "JENKINS (single logical flow):\n"
        "  1. apt-get install -y openjdk-17-jre curl gnupg\n"
        "  2. bash -c '\n"
        "       install -m 0755 -d /usr/share/keyrings;\n"
        "       curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key -o /usr/share/keyrings/jenkins-keyring.asc;\n"
        "       echo \"deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] https://pkg.jenkins.io/debian-stable binary/\" | tee /etc/apt/sources.list.d/jenkins.list > /dev/null;\n"
        "       apt-get update && apt-get install -y jenkins\n"
        "     '\n"
        "  3. systemctl enable jenkins && systemctl start jenkins && systemctl status jenkins\n\n"

        "NODE.JS (latest LTS, NodeSource):\n"
        "  bash -c 'curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - && apt-get install -y nodejs'\n\n"

        "KUBECTL (latest stable binary):\n"
        "  bash -c 'curl -fsSL https://dl.k8s.io/release/$(curl -fsSL https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl -o /usr/local/bin/kubectl && chmod +x /usr/local/bin/kubectl'\n\n"

        "WORDPRESS (latest, Apache + MySQL + PHP):\n"
        "  1. DEBIAN_FRONTEND=noninteractive apt-get install -y apache2 mysql-server php php-mysql php-curl php-gd php-mbstring php-xml php-xmlrpc libapache2-mod-php curl\n"
        "  2. bash -c 'curl -fsSL https://wordpress.org/latest.tar.gz | tar -xz -C /var/www/html --strip-components=1'\n"
        "  3. bash -c 'chown -R www-data:www-data /var/www/html && chmod -R 755 /var/www/html && systemctl enable apache2 && systemctl restart apache2'\n\n"

        "NGINX:\n"
        "  bash -c 'apt-get install -y nginx && systemctl enable nginx && systemctl start nginx && nginx -v'\n\n"

        "MYSQL / MARIADB:\n"
        "  bash -c 'DEBIAN_FRONTEND=noninteractive apt-get install -y mysql-server && systemctl enable mysql && systemctl start mysql && mysql --version'\n\n"

        "ANSIBLE:\n"
        "  bash -c 'apt-get install -y ansible && ansible --version'\n\n"

        "PYTHON3/PIP:\n"
        "  apt-get install -y python3 python3-pip python3-venv && python3 --version\n\n"

        "CERTBOT / SSL:\n"
        "  bash -c 'apt-get install -y certbot python3-certbot-nginx && certbot --version'\n\n"

        "Always end with a verification command. Return ONLY valid JSON. No markdown. No text outside the JSON object."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": f"Task: {task}"},
    ]

    raw = _call_api(messages)
    parsed = _extract_json(raw)
    if parsed is not None:
        result = parsed
    else:
        result = {
            "description": task,
            "commands":    [raw],
            "warnings":    "AI returned unstructured output — review carefully before executing",
        }

    return result


def fix_error(
    command: str,
    error_output: str,
    os_name: str,
    package_manager: str,
    previous_steps: list | None = None,
) -> dict:
    """
    Diagnose a failed command and return the minimal, correct fix commands.
    previous_steps: list of (cmd, success: bool) tuples showing what ran before this failure.
    Returns: {"diagnosis": str, "fix_commands": [str]}
    """
    context_block = ""
    if previous_steps:
        lines = []
        for step_cmd, step_ok in previous_steps:
            status = "✓ succeeded" if step_ok else "✗ failed"
            lines.append(f"  [{status}] {step_cmd}")
        context_block = "\nPrevious steps in this session:\n" + "\n".join(lines) + "\n"

    system_prompt = (
        f"You are a senior Linux troubleshooting engineer.\n"
        f"Target OS: {os_name}\n"
        f"Package manager: {package_manager}\n\n"
        "A command failed during an automated installation. Analyse the EXACT error, consider\n"
        "what already succeeded, and return the minimal correct fix to unblock progress.\n\n"
        "Return a JSON object with EXACTLY:\n"
        '- "diagnosis": concise explanation of the root cause (1-2 sentences)\n'
        '- "fix_commands": array of shell command strings to fix the issue, then\n'
        '  re-attempt the failed step if needed. Must be non-interactive.\n\n'
        "=== STRICT RULES ===\n"
        "- NEVER hardcode OS codenames. Use $(. /etc/os-release && echo $VERSION_CODENAME).\n"
        "- If the error is 'Unable to locate package X', do NOT retry the same command.\n"
        "  Instead find the correct repo/source for X on this OS and add it first.\n"
        "- If the error is a GPG/signature issue, fetch the correct key from the official source.\n"
        "- If the error is 'command not found', install the missing package first.\n"
        "- Do NOT add 'software-properties-common' — it often fails. Use direct tee approach.\n"
        "- Do NOT use sudo. Do NOT use markdown. Return ONLY valid JSON."
    )

    user_content = (
        f"Failed command:\n{command}\n"
        f"{context_block}"
        f"\nError output:\n{error_output[:3000]}"  # cap to avoid token overflow
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_content},
    ]

    raw = _call_api(messages)
    parsed = _extract_json(raw)
    if parsed is not None:
        result = parsed
    else:
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
