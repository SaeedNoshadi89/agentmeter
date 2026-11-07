#!/usr/bin/env python3
"""Tests for the AgentMeter skill's report script:  python3 tests/skill.py

Uses fake AgentMeter output, so it needs no logins and changes nothing on the computer.
"""
import contextlib
import importlib.machinery
import importlib.util
import io
import json
import os
import sys
import time

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "..", "skills", "agentmeter", "scripts", "usage.py")
loader = importlib.machinery.SourceFileLoader("usage", PATH)
u = importlib.util.module_from_spec(importlib.util.spec_from_loader("usage", loader))
loader.exec_module(u)
passed = failed = 0


def ok(name, cond):
    global passed, failed
    passed, failed = passed + bool(cond), failed + (not cond)
    print(("  ok    " if cond else "  FAIL  ") + name)


def run(argv):
    sys.argv = ["usage.py"] + argv
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        u.main()
    return buf.getvalue()


now = time.time()
real_find, real_run = u.find_agentmeter, u.run_agentmeter

u.find_agentmeter = lambda: None
out = run([])
ok("not installed: says so and shows install commands", "not installed" in out and "brew install" in out)
ok("not installed: --json status", json.loads(run(["--json"]))["status"] == "not_installed")

FAKE = {
    "claude:/Users/someone/.claude-work": {"agent": "claude", "label": "Claude Code", "account": "boss@company.com",
        "meters": [{"label": "5-hour", "left": 0, "resets_at": now - 600, "detail": None},
                   {"label": "Weekly", "left": 12, "resets_at": now + 3600, "detail": None}]},
    "claude:default": {"agent": "claude", "label": "Claude Code", "account": "me@gmail.com",
        "stale": "rate limited, retrying soon", "as_of": now - 900,
        "meters": [{"label": "5-hour", "left": 55, "resets_at": now + 7200, "detail": None}]},
    "claude:/Users/someone/.claude-x": {"agent": "claude", "label": "Claude Code", "account": "x@y.org",
        "error": "login expired for x@y.org at /Users/someone/.claude-x token sk-ant-abcdefghijklmnop1234567890XYZ",
        "meters": []},
    "codex": {"agent": "codex", "label": "Codex", "account": None, "as_of": now - 7200,
        "meters": [{"label": "5-hour", "left": 30, "resets_at": now + 600, "detail": None}]},
    "opencode:openrouter": {"agent": "opencode", "label": "OpenCode", "account": "via OpenRouter",
        "meters": [{"label": "Monthly", "left": 76, "resets_at": now + 86400 * 20, "detail": "$38 of $50"}]},
}
u.find_agentmeter = lambda: "/fake/agentmeter"
u.run_agentmeter = lambda binary, demo: (FAKE, None)
out = run([]) + run(["--json"])
ok("no emails reach the agent", "@" not in out)
ok("no home paths reach the agent", "/Users/" not in out and "/home/" not in out)
ok("no tokens reach the agent", "sk-ant" not in out)
ok("multiple accounts are numbered, not named", "account 1 of 3" in out and "account 3 of 3" in out)
ok("a passed reset shows 100% left and no negative time", "5-hour limit: 100% left" in out and "in -" not in out)
ok("stale numbers are marked with their time and reason", "stale, last good numbers" in out and "rate limited" in out)
ok("unavailable account says why", "unavailable" in out and "login expired" in out)
ok("Codex freshness is explained", "Codex only updates" in out and "2h 00m ago" in out)
ok("budgets keep their amount", "$38 of $50" in out)
ok("--only filters agents", "Codex" not in run(["--only", "claude"]))

u.run_agentmeter = lambda binary, demo: (None, u.SANDBOX_HELP)
ok("sandbox block is explained", "sandbox" in run([]))
u.run_agentmeter = lambda binary, demo: ({"claude:default": {"agent": "claude", "label": "Claude Code",
    "account": "a@b.com", "error": "offline, retrying soon", "meters": []}}, None)
ok("no network looks like a sandbox and says so", "note: AgentMeter was blocked" in run([]))
u.run_agentmeter = lambda binary, demo: ({}, None)
ok("installed but no agents found", "found no supported agents" in run([]))

u.find_agentmeter, u.run_agentmeter = real_find, real_run
if u.find_agentmeter():
    demo = run(["--demo"])
    ok("demo data through the real AgentMeter", "DEMO DATA" in demo and "@" not in demo)

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
