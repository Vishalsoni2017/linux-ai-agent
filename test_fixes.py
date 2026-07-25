#!/usr/bin/env python3
"""Quick unit tests for the fixed Linux Agent modules."""
import sys
sys.path.insert(0, r'c:\Users\visha\OneDrive\Desktop\linux-agentic\linux-agent\src')

PASS = 0
FAIL = 0

def check(name, result, expected=True):
    global PASS, FAIL
    ok = result == expected if expected is not True else bool(result)
    status = "[OK]  " if ok else "[FAIL]"
    print(f"  {status} {name}")
    if ok:
        PASS += 1
    else:
        FAIL += 1
        print(f"         Expected: {expected!r}")
        print(f"         Got:      {result!r}")

# ── Test 1: _strip_markdown_fences ────────────────────────────────────────────
print("\n=== ai_engine: _strip_markdown_fences ===")
from ai_engine import _strip_markdown_fences

check(
    "plain JSON passthrough",
    _strip_markdown_fences('{"a":1}'),
    '{"a":1}',
)
check(
    "backtick-json block",
    _strip_markdown_fences("```json\n{\"a\":1}\n```"),
    '{"a":1}',
)
check(
    "backtick block (no lang)",
    _strip_markdown_fences("```\n{\"a\":1}\n```"),
    '{"a":1}',
)
check(
    "trailing newline after fence",
    _strip_markdown_fences("```json\n{\"a\":1}\n```\n"),
    '{"a":1}',
)
check(
    "leading/trailing whitespace only",
    _strip_markdown_fences("  {\"a\":1}  "),
    '{"a":1}',
)

# ── Test 2: config cache ──────────────────────────────────────────────────────
print("\n=== config: in-memory cache ===")
from config import load_config, set_value, _invalidate_cache

_invalidate_cache()
cfg1 = load_config()
cfg2 = load_config()
check("cache hit returns same object", id(cfg1) == id(cfg2))

set_value("_test_cache_key", "hello")
cfg3 = load_config()
check("write invalidates cache (new object)", id(cfg1) != id(cfg3))
check("new value visible after write", cfg3.get("_test_cache_key") == "hello")

# ── Test 3: config env var override ──────────────────────────────────────────
print("\n=== config: env var overrides ===")
import os
from config import _invalidate_cache

os.environ["OPENROUTER_API_KEY"] = "sk-test-envkey-999"
_invalidate_cache()
from config import get
check("OPENROUTER_API_KEY env var overrides stored key", get("api_key") == "sk-test-envkey-999")
del os.environ["OPENROUTER_API_KEY"]
_invalidate_cache()

# ── Test 4: executor DRY_RUN ──────────────────────────────────────────────────
print("\n=== executor: DRY_RUN mode ===")
os.environ["LINUX_AGENT_DRY_RUN"] = "1"

# We must reimport executor AFTER setting the env var
import importlib
import executor
importlib.reload(executor)
check("DRY_RUN is True when env var set", executor.DRY_RUN is True)

success, stdout, stderr = executor.run_command("echo hello", use_sudo=False)
check("DRY_RUN run_command returns success=True", success is True)
check("DRY_RUN run_command stdout is empty", stdout == "")

del os.environ["LINUX_AGENT_DRY_RUN"]
importlib.reload(executor)
check("DRY_RUN is False after env var removed", executor.DRY_RUN is False)

# ── Test 5: executor dangerous command detection ──────────────────────────────
print("\n=== executor: dangerous command detection ===")
importlib.reload(executor)
check("rm -rf / detected", executor._is_dangerous("rm -rf /"))
check("rm -rf /* detected", executor._is_dangerous("rm -rf /*"))
check("dd if= detected",     executor._is_dangerous("dd if=/dev/zero of=/dev/sda"))
check("normal command safe",  executor._is_dangerous("apt install nginx") is False)
check("echo safe",           executor._is_dangerous("echo hello") is False)

# ── Test 6: script_manager base64 encoding ────────────────────────────────────
print("\n=== script_manager: base64 write commands ===")
from script_manager import _make_write_commands
import base64

content = "#!/usr/bin/env bash\necho 'it\\'s working'\necho \"quotes\"\n"
cmds = _make_write_commands(content, "/tmp/test.sh")
check("returns 3 commands (including mkdir)", len(cmds) == 3)
check("third command is chmod +x", "chmod +x" in cmds[2])

# Verify round-trip
write_cmd = cmds[1]
# Extract base64 string from the command
b64_start = write_cmd.index("'") + 1
b64_end   = write_cmd.rindex("'", 0, write_cmd.rindex("|"))
b64_str   = write_cmd[b64_start:b64_end]
decoded   = base64.b64decode(b64_str.encode()).decode("utf-8")
check("base64 round-trip preserves content", decoded == content)

# ── Test 7: audit logging ──────────────────────────────────────────────────────
print("\n=== config: audit logging ===")
from config import log_audit, CONFIG_DIR
import os

log_file = CONFIG_DIR / "audit.log"
if log_file.exists():
    os.remove(log_file)

log_audit("TEST_EVENT", "This is an audit test message details")
check("audit.log file was created", log_file.exists())
with open(log_file, "r", encoding="utf-8") as f:
    content = f.read()
check("audit.log contains event type", "[TEST_EVENT]" in content)
check("audit.log contains details", "This is an audit test message details" in content)

# ── Test 8: robust JSON extraction ────────────────────────────────────────────
print("\n=== ai_engine: robust JSON extraction ===")
from ai_engine import _extract_json

plain_json = '{"diagnosis": "ok", "fix_commands": ["echo 1"]}'
conversational_json = 'Sure! Here is the JSON:\n```json\n{"diagnosis": "ok", "fix_commands": ["echo 1"]}\n```\nHope this helps!'

check("plain JSON parsed", _extract_json(plain_json) == {"diagnosis": "ok", "fix_commands": ["echo 1"]})
check("conversational JSON parsed", _extract_json(conversational_json) == {"diagnosis": "ok", "fix_commands": ["echo 1"]})

# ── Summary ───────────────────────────────────────────────────────────────────
print(f"\n{'='*50}")
print(f"  RESULTS: {PASS} passed, {FAIL} failed")
print('='*50)
sys.exit(0 if FAIL == 0 else 1)
