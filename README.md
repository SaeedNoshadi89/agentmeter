# agentmeter

See how much of your **5-hour** and **weekly** limits is left for your coding agents, **Claude Code** and **Codex**, from the terminal or as a popup in [Rex](https://www.superlogical.com/rex).

```
  claude  5h  ━━━━━━━━━━━━━━━━━━  100%
          wk  ━━━───────────────   15%  2d 20h

  codex   5h  ━━━━━━━━━━━━━━━━━━  100%
          wk  ━━━━━━━━━─────────   49%  5d 2h
          as of 12:31
```

Each bar shows the share left in that window. It's green at 50% or more, yellow from 20%, and red below. Colors use the basic ANSI palette, so they follow your terminal theme.

## Install

```sh
curl -fsSL https://raw.githubusercontent.com/SaeedNoshadi89/agentmeter/main/install.sh | sh
```

The installer:
- puts `agentmeter` in `~/.local/bin`
- if Rex is installed, adds a **Show Agent Usage** action to `~/.config/rex/init.lua`, bound to **Shift+Cmd+U**, and reloads the config. It backs up your config to `init.lua.bak` first and restores it if the check fails.

The only requirement is `python3`, with no extra packages.

| Variable | Effect |
| --- | --- |
| `AGENTMETER_BIN_DIR=/usr/local/bin` | Install somewhere else |
| `AGENTMETER_KEY=alt+cmd+u` | Use a different Rex shortcut |
| `AGENTMETER_NO_REX=1` | Skip the Rex setup |
| `AGENTMETER_UNINSTALL=1` | Remove the command and its Rex block |

Set a variable on the `sh` side of the pipe, for example `curl -fsSL …/install.sh | AGENTMETER_KEY=alt+cmd+u sh`.

From a clone, run `./install.sh` instead.

## Usage

```sh
agentmeter           # print usage
agentmeter --json    # machine-readable output
agentmeter --popup   # print, then wait for a key (used by the Rex popup)
```

In Rex, press **Shift+Cmd+U**, search for "Show Agent Usage" in the command palette, or run `rex do agent_usage`.

## Where the numbers come from

| Agent | Source |
| --- | --- |
| Claude Code | `GET https://api.anthropic.com/api/oauth/usage`, using the token Claude Code saved when you logged in. On macOS that is the Keychain item `Claude Code-credentials`; on Linux it's `~/.claude/.credentials.json`. |
| Codex | The last `rate_limits` entry in `~/.codex/sessions/**/rollout-*.jsonl`. This is read locally, with no network call. The `primary` entry is the 5h window and `secondary` is the weekly one. |

Notes:
- **Codex** only updates these numbers when it runs, so they are as fresh as your last Codex turn. If a window's reset time has passed, it's shown as 100% left.
- **Claude's usage endpoint is undocumented** and may change.
- Results are cached for 60 seconds in `~/.cache/agentmeter.json`.

## Privacy

Your Claude token is sent only to `api.anthropic.com`. agentmeter never logs it, stores it or sends it anywhere else. Nothing else leaves your machine.

## Adding another agent

Write a function that returns `{"five_hour": window(used_pct, resets_at_epoch), "weekly": ...}`, then add it to `PROVIDERS` in `agentmeter`.

## License

MIT
