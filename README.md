# agentmeter

See how much of your **5-hour** and **weekly** limits is left for your coding agents, **Claude Code** and **Codex**, from the terminal or as a popup in [Rex](https://www.superlogical.com/rex).

<img src="docs/screenshot.png" alt="agentmeter popup in Rex" width="640">

Each bar shows the share left in that window. It's green at 50% or more, yellow from 20%, and red below. The dot beside each agent takes the color of its lower window. Colors use the basic ANSI palette, so they follow your terminal theme. In the popup, press **r** to refresh and any other key to close.

## Install

**Homebrew**

```sh
brew install SaeedNoshadi89/tap/agentmeter
agentmeter setup-rex        # optional: add the Rex popup (Shift+Cmd+U)
```

**Script**

```sh
curl -fsSL https://raw.githubusercontent.com/SaeedNoshadi89/agentmeter/main/install.sh | sh
```

The script puts `agentmeter` in `~/.local/bin` and, if Rex is installed, runs `agentmeter setup-rex` for you.

The only requirement is `python3`, with no extra packages.

| Variable (script only) | Effect |
| --- | --- |
| `AGENTMETER_BIN_DIR=/usr/local/bin` | Install somewhere else |
| `AGENTMETER_KEY=alt+cmd+u` | Use a different Rex shortcut |
| `AGENTMETER_NO_REX=1` | Skip the Rex setup |
| `AGENTMETER_UNINSTALL=1` | Remove the command and its Rex popup |

Set a variable on the `sh` side of the pipe, for example `curl -fsSL …/install.sh | AGENTMETER_KEY=alt+cmd+u sh`.

## Rex popup

`agentmeter setup-rex [--key shift+cmd+u]` adds a **Show Agent Usage** action to `~/.config/rex/init.lua` and reloads Rex. It sits between `-- >>> agentmeter >>>` markers, so running it again replaces the old block instead of adding a second one. If Rex rejects the new config, your file is left as it was. `agentmeter remove-rex` takes the block out.

## Usage

```sh
agentmeter           # print usage
agentmeter --json    # machine-readable output
agentmeter --popup   # full-screen view: r refreshes, any other key closes (used by the Rex popup)
agentmeter --version
```

In Rex, press **Shift+Cmd+U**, search for "Show Agent Usage" in the command palette, or run `rex do agent_usage`.

## Several Claude accounts

Claude Code keeps each login in a config folder: `~/.claude` by default, or whatever `CLAUDE_CONFIG_DIR` points to. agentmeter finds every logged-in folder (`~/.claude`, `~/.claude-*` and `~/.config/claude*`) and labels each one with its account email.

- **Rex popup:** if the pane you're in is running Claude Code, the popup shows only that pane's account. It reads the `CLAUDE_CONFIG_DIR` of the `claude` process in that pane. From any other pane, it shows every account.
- **Terminal:** `agentmeter` shows every account. `agentmeter --claude-config ~/.claude-work` shows one.

## Where the numbers come from

| Agent | Source |
| --- | --- |
| Claude Code | `GET https://api.anthropic.com/api/oauth/usage`, using the token Claude Code saved when you logged in. On macOS that's the Keychain item `Claude Code-credentials`. For a custom config folder, the item name gets `-` plus the first 8 hex characters of the SHA-256 of the folder path. On Linux it's `<config folder>/.credentials.json`. |
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
