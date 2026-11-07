# agentmeter

See how much of your coding agents' usage limits is left, from the terminal or as a popup in [Rex](https://www.superlogical.com/rex). agentmeter finds the agents installed on your machine and lists each one: Claude Code and Codex with their **5-hour** and **weekly** limits, OpenCode with its provider's budget, and more.

<img src="docs/screenshot.png" alt="agentmeter popup in Rex" width="640">

Each bar shows the share left. Every agent and every window uses the same colors:

| Left | Color |
| --- | --- |
| 50% or more | green |
| under 50% | orange |
| under 30% | red |

In the popup, press **r** to refresh and any other key to close.

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

## Supported agents

An agent is listed when its command is installed or its data folder exists.

| Agent | What's shown |
| --- | --- |
| ✻ Claude Code | 5-hour and weekly limits, for each account |
| >_ Codex | 5-hour and weekly limits, from its last run |
| ▣ OpenCode | One row for each provider it's signed in to. An OpenRouter key shows its budget, for example "Monthly $250 of $250". A Claude subscription login shows 5-hour and weekly limits. An API key is marked pay-as-you-go. |
| Gemini CLI, Cursor Agent, Amp, Copilot CLI, Qwen Code, Crush, Factory Droid, Aider | Listed when installed. Usage isn't available yet. |

To add an agent, add a row to `AGENTS` in `agentmeter`. Each row needs a check for whether the agent is installed, and a function that returns its meters.

## Several Claude accounts

Claude Code keeps each login in a config folder: `~/.claude` by default, or whatever `CLAUDE_CONFIG_DIR` points to. agentmeter finds every logged-in folder (`~/.claude`, `~/.claude-*` and `~/.config/claude*`) and labels each one with its account email.

- **Rex popup:** if the pane you're in is running Claude Code, the popup shows only that pane's account. It reads the `CLAUDE_CONFIG_DIR` of the `claude` process in that pane. From any other pane, it shows every account.
- **Terminal:** `agentmeter` shows every account. `agentmeter --claude-config ~/.claude-work` shows one.

## Where the numbers come from

| Agent | Source |
| --- | --- |
| Claude Code | `GET https://api.anthropic.com/api/oauth/usage`, using the token Claude Code saved when you logged in. On macOS that's the Keychain item `Claude Code-credentials`. For a custom config folder, the item name gets `-` plus the first 8 hex characters of the SHA-256 of the folder path. On Linux it's `<config folder>/.credentials.json`. |
| OpenCode | `~/.local/share/opencode/auth.json`. OpenRouter keys are checked with `GET https://openrouter.ai/api/v1/key`, and Claude logins with the same usage check as Claude Code. |
| Codex | The last `rate_limits` entry in `~/.codex/sessions/**/rollout-*.jsonl`. This is read locally, with no network call. The `primary` entry is the 5h window and `secondary` is the weekly one. |

Notes:
- **Codex** only updates these numbers when it runs, so they are as fresh as your last Codex turn. If a window's reset time has passed, it's shown as 100% left.
- **Claude's usage endpoint is undocumented** and may change.
- Results are cached for 60 seconds in `~/.cache/agentmeter.json`.

## Privacy

Each token or key is sent only to its own service: Claude tokens to `api.anthropic.com` and OpenRouter keys to `openrouter.ai`. agentmeter never logs or stores them, and never sends them anywhere else. Nothing else leaves your machine.

## License

MIT
