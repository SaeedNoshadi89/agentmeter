# AgentMeter skill

Ask your coding agent "How much Claude Code or Codex usage do I have left?" and get the answer in chat: how much of each 5-hour and weekly limit is left, when each one resets, and how fresh the numbers are.

Free and open source (MIT). Source: https://github.com/SaeedNoshadi89/agentmeter

## Requirements

- **AgentMeter installed on the same computer:**
  - macOS (Homebrew): `brew install SaeedNoshadi89/tap/agentmeter`
  - macOS or Linux: `curl -fsSL https://raw.githubusercontent.com/SaeedNoshadi89/agentmeter/main/install.sh | sh`
- **An agent that can run local commands**, such as Claude Code or Codex CLI. The skill runs AgentMeter on your computer and reports in chat, so it can't work in a chat-only app.
- **`python3`**, which AgentMeter needs too.
- **In Codex's sandbox**, Codex's own numbers work directly. Claude Code and other numbers come from AgentMeter's last check, marked with their time, because the sandbox blocks live checks. Approve running the command outside the sandbox for fresh ones.
- **Rex is optional.** AgentMeter also has a popup for the Rex terminal, but this skill doesn't need it.

## What it reports

- Percent left for each limit: Claude Code and Codex 5-hour and weekly limits, and OpenCode budgets
- When each limit resets, as a time and a countdown
- How fresh the numbers are: current, stale with the reason (for example rate limited), or, for Codex, the time of its last run
- Each Claude account separately, labelled "account 1 of 2" and so on

## Privacy

- **The agent never sees your account emails.** `scripts/usage.py` runs AgentMeter and removes emails, home-folder paths and anything that looks like a token on your computer before printing.
- **It reads no credentials and makes no network calls itself.** AgentMeter does the checking, as it does from your terminal. See AgentMeter's README for exactly what it reads and where it connects.

## Files

| File | Purpose |
| --- | --- |
| `SKILL.md` | Instructions for the agent |
| `scripts/usage.py` | Runs `agentmeter --json` and prints a filtered report (`--json`, `--demo`, `--only claude,codex`) |
| `references/examples.md` | Example prompts and answers, made with demo data |
| `LICENSE` | MIT |

## Try it without real data

```sh
python3 scripts/usage.py --demo
```

## License

MIT, Copyright (c) 2026 Saeed Noshadi. See `LICENSE`.
