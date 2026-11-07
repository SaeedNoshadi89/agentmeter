#!/usr/bin/env python3
"""Report how much coding-agent usage is left, using the AgentMeter CLI on this computer.

This script never reads credentials, tokens or keychains itself and makes no network
calls of its own. It runs the locally installed `agentmeter --json`, then removes account
emails and anything else that looks personal before printing, so the agent only sees
quota numbers, reset times and freshness.

Usage:
  usage.py            plain-text report for the agent to relay
  usage.py --json     the same report as JSON
  usage.py --demo     made-up accounts and numbers (for examples and screenshots)
  usage.py --only claude,codex   limit to some agents

Exit code is always 0 so the agent can read the report; problems are described in it.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time

# Where AgentMeter is usually installed, in case it isn't on the agent's PATH.
CANDIDATES = [
    "/opt/homebrew/bin/agentmeter",
    "/usr/local/bin/agentmeter",
    os.path.expanduser("~/.local/bin/agentmeter"),
]
INSTALL_HELP = [
    "brew install SaeedNoshadi89/tap/agentmeter   (macOS, Homebrew)",
    "curl -fsSL https://raw.githubusercontent.com/SaeedNoshadi89/agentmeter/main/install.sh | sh   (macOS or Linux)",
    "Source and docs: https://github.com/SaeedNoshadi89/agentmeter",
]
SANDBOX_HELP = ("AgentMeter was blocked by this agent's sandbox. It needs to read your agents' local "
                "data and contact their usage services. Allow this command to run outside the "
                "sandbox (approve it, or give the session network access), then ask again.")
OFFLINE = re.compile(r"offline|Operation not permitted|Permission", re.I)
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# Long opaque strings (tokens, keys, ids) and home-folder paths never reach the agent.
OPAQUE = re.compile(r"\b(?:sk|pk|rk|gho|ghp|xox[abp])[-_][A-Za-z0-9_-]{8,}\b|\b[A-Za-z0-9_-]{32,}\b")
HOME_PATH = re.compile(r"(?:" + re.escape(os.path.expanduser("~")) + r"|/Users/[^/\s]+|/home/[^/\s]+|~)(?:/[^\s'\"]*)?")
LABELS = {"5-hour": "5-hour limit", "Weekly": "weekly limit", "Monthly": "monthly budget",
          "Daily": "daily budget", "Budget": "budget"}


def clean(text):
    """Remove anything personal from a free-text field."""
    if not text:
        return text
    text = EMAIL.sub("[account]", str(text))
    text = HOME_PATH.sub("[path]", text)
    return OPAQUE.sub("[hidden]", text)


def find_agentmeter():
    found = shutil.which("agentmeter")
    if found:
        return found
    return next((p for p in CANDIDATES if os.access(p, os.X_OK)), None)


def run_agentmeter(binary, demo):
    args = [binary, "--json"] + (["--demo"] if demo else [])
    try:
        out = subprocess.run(args, capture_output=True, text=True, timeout=30,
                             stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return None, "AgentMeter took too long to answer (over 30 seconds)."
    except OSError as e:
        return None, f"AgentMeter could not be started: {clean(e)}"
    if out.returncode != 0:
        err = out.stderr.strip()
        if re.search(r"PermissionError|Operation not permitted|Read-only file system", err):
            return None, SANDBOX_HELP
        return None, f"AgentMeter failed: {clean(err.splitlines()[-1] if err else 'no details')}"
    try:
        return json.loads(out.stdout), None
    except ValueError:
        return None, "AgentMeter's output could not be read. Try upgrading it: brew upgrade agentmeter"


def human_delta(seconds):
    seconds = int(seconds)
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes = rem // 60
    if days:
        return f"{days}d {hours}h"
    if hours:
        return f"{hours}h {minutes:02d}m"
    return f"{minutes}m"


def local_time(ts):
    lt = time.localtime(ts)
    if time.strftime("%Y-%m-%d", lt) == time.strftime("%Y-%m-%d"):
        return time.strftime("today %H:%M", lt)
    return time.strftime("%a %b %d %H:%M", lt)


def build_report(data, only):
    now = time.time()
    claude_total = sum(1 for k in data if k.startswith("claude:"))
    claude_seen = 0
    agents = []
    for key, entry in data.items():
        agent_id = entry.get("agent") or key.split(":")[0]
        if only and agent_id not in only:
            continue
        name = entry.get("label") or agent_id
        account = None
        if agent_id == "claude":
            claude_seen += 1
            if claude_total > 1:
                account = f"account {claude_seen} of {claude_total}"   # never the email
        elif entry.get("account") and not EMAIL.search(entry["account"]):
            account = clean(entry["account"])                           # e.g. "via OpenRouter"

        limits = []
        for m in entry.get("meters") or []:
            left, resets = m.get("left"), m.get("resets_at")
            if resets and resets <= now:          # the window has already started over
                left, resets = 100.0, None
            limits.append({
                "limit": LABELS.get(m.get("label"), m.get("label") or "limit"),
                "left_percent": None if left is None else round(left),
                "resets_at": local_time(resets) if resets else None,
                "resets_in": human_delta(resets - now) if resets else None,
                "budget_left": clean(m.get("detail")),
            })

        if entry.get("error"):
            freshness = "unavailable"
            note = clean(entry["error"])
        elif entry.get("stale"):
            freshness = f"stale, last good numbers from {local_time(entry['as_of'])}"
            note = clean(entry["stale"])
        elif entry.get("as_of"):
            age = now - entry["as_of"]
            freshness = f"from {local_time(entry['as_of'])} ({human_delta(age)} ago)"
            note = "Codex only updates these numbers when it runs." if agent_id == "codex" else None
        elif limits:
            freshness = "current (checked within the last minute)"
            note = None
        else:
            freshness = "no limits reported"
            note = clean(entry.get("note"))
        agents.append({"agent": name, "account": account, "limits": limits,
                       "freshness": freshness, "note": note})
    return agents


def blocked(agents):
    """True when every agent failed to connect, which usually means a sandbox without network."""
    failed = [a for a in agents if a["freshness"] == "unavailable" or a["freshness"].startswith("stale")]
    return bool(agents) and len(failed) == len([a for a in agents if a["agent"] != "Codex"]) and \
        all(OFFLINE.search(a["note"] or "") for a in failed)


def text_report(report):
    if report["status"] != "ok":
        lines = [report["message"]]
        if report.get("install"):
            lines += ["", "To install AgentMeter, the user can run one of:"] + [f"  {c}" for c in report["install"]]
        return "\n".join(lines)
    if report.get("hint"):
        hint = ["", "note: " + report["hint"]]
    else:
        hint = []
    if not report["agents"]:
        return "AgentMeter is installed but found no supported agents (Claude Code, Codex, OpenCode, ...) on this computer."
    lines = [f"Usage left, checked {report['checked_at']}" + (" (DEMO DATA)" if report["demo"] else ""), ""]
    for a in report["agents"]:
        lines.append(a["agent"] + (f" ({a['account']})" if a["account"] else ""))
        for lim in a["limits"]:
            parts = [f"  {lim['limit']}: {lim['left_percent']}% left"]
            if lim["budget_left"]:
                parts.append(lim["budget_left"])
            if lim["resets_at"]:
                parts.append(f"resets {lim['resets_at']} (in {lim['resets_in']})")
            lines.append(", ".join(parts))
        lines.append(f"  data: {a['freshness']}")
        if a["note"]:
            lines.append(f"  note: {a['note']}")
        lines.append("")
    return "\n".join(lines + hint).rstrip()


def main():
    demo = "--demo" in sys.argv
    only = []
    if "--only" in sys.argv[:-1]:
        only = [a.strip() for a in sys.argv[sys.argv.index("--only") + 1].split(",") if a.strip()]
    report = {"checked_at": time.strftime("%Y-%m-%d %H:%M %Z"), "demo": demo}

    binary = find_agentmeter()
    if not binary:
        report.update(status="not_installed", install=INSTALL_HELP,
                      message="AgentMeter is not installed on this computer, so usage can't be checked.")
    else:
        data, problem = run_agentmeter(binary, demo)
        if problem:
            report.update(status="error", message=problem)
        else:
            agents = build_report(data, only)
            report.update(status="ok", agents=agents)
            if blocked(agents):
                report["hint"] = SANDBOX_HELP

    if "--json" in sys.argv:
        print(json.dumps(report, indent=2))
    else:
        print(text_report(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
