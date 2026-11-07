---
name: agentmeter
description: Reports how much Claude Code and Codex usage is left on this computer (5-hour and weekly limits, reset times and how fresh the numbers are) by running the open-source AgentMeter CLI locally. Use when the user asks "how much Claude Code usage do I have left?", "check my Codex limits", "when does my Claude quota reset?", "am I close to my limit?" or "show my agent usage", or wants an example or demo of an AgentMeter usage report.
---

# AgentMeter: usage left for Claude Code and Codex

Answer questions about remaining coding-agent quota by running the AgentMeter CLI that is installed on the user's computer. AgentMeter is free and open source (MIT): https://github.com/SaeedNoshadi89/agentmeter

This skill needs an agent that can run local commands, such as Claude Code or Codex CLI. It answers in chat. Rex, the terminal app with an AgentMeter popup, is optional and not needed.

## Steps

1. Run the report script in this skill's folder:

   ```sh
   python3 scripts/usage.py
   ```

   Run it from this skill's base directory, or use its full path. Add `--only claude` or `--only codex` when the user asks about just one agent.

2. Answer from the script's output only. Do not run `agentmeter` directly, and do not read `~/.cache/agentmeter*`, Claude Code's config, the Keychain or any credentials. The script exists so that account emails, file paths and tokens are removed on the user's computer before you see the output.

3. Reply in this format, keeping it short:

   - One line per limit: agent, limit, **percent left**, and when it resets, for example "Claude Code, 5-hour limit: **64% left**, resets today 16:30 (in 1h 39m)".
   - The `data:` freshness for each agent, in plain words. Say "current" when it was checked within the last minute.
   - Pass on any `note:` line.
   - If any limit is under 30% left, mention it first.
   - With several Claude accounts, keep the script's labels ("account 1 of 2"). Never ask for or guess emails.

## When something isn't normal

- **AgentMeter isn't installed** (the script says so): tell the user, and show the install commands from the output. Do not install it yourself; let the user choose.
- **`stale, last good numbers from …`**: give those numbers, say they are from that time, and give the reason, for example "rate limited, retrying soon". AgentMeter retries by itself.
- **`unavailable`**: say that agent's numbers can't be read right now, and give the reason. If it mentions logging in, suggest the user run `claude` and sign in.
- **Codex `from today 14:48 (… ago)`**: Codex only writes these numbers when it runs, so they can be older. Say how old.
- **100% left with no reset time** means that window is unused or has started over. Just report it as 100% left; don't guess why.
- **Blocked by the sandbox** (the output says so): AgentMeter needs to read local agent data and contact the usage services, which a read-only or offline sandbox stops. Ask the user to approve running the script outside the sandbox, or to allow network access, then run it again. In Codex CLI that means approving the command, or starting Codex with a sandbox that allows it.
- **No supported agents found**: say so. AgentMeter supports Claude Code, Codex and OpenCode, and lists other agents without numbers.

## Examples

See `references/examples.md` for example questions and answers made with AgentMeter's demo data (`python3 scripts/usage.py --demo`). Use `--demo` only when the user asks for an example or a screenshot, never for real answers.
