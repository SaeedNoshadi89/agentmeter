# Examples

All numbers and accounts below are **demo data** from `python3 scripts/usage.py --demo`. They are made up and belong to no real account.

## Example prompts

- How much Claude Code usage do I have left?
- Check my Codex limits.
- When does my Claude quota reset?
- Am I close to my limit?
- Show my agent usage.
- How much of my weekly Claude limit is left on each account?

## Script output (demo)

```
Usage left, checked 2026-11-07 14:51 +0330 (DEMO DATA)

Claude Code (account 1 of 2)
  5-hour limit: 100% left
  weekly limit: 22% left, resets Mon Nov 09 19:51 (in 2d 4h)
  data: current (checked within the last minute)

Claude Code (account 2 of 2)
  5-hour limit: 64% left, resets today 16:30 (in 1h 39m)
  weekly limit: 88% left, resets Fri Nov 13 17:51 (in 6d 2h)
  data: current (checked within the last minute)

Codex
  5-hour limit: 91% left, resets today 18:02 (in 3h 11m)
  weekly limit: 41% left, resets Wed Nov 11 16:51 (in 4d 1h)
  data: current (checked within the last minute)
```

## Example answer (demo)

> **Heads-up:** Claude Code account 1 has only **22%** of its weekly limit left. It resets Mon Nov 09 19:51 (in 2d 4h).
>
> - Claude Code (account 1 of 2), 5-hour limit: **100% left**
> - Claude Code (account 1 of 2), weekly limit: **22% left**, resets Mon Nov 09 19:51 (in 2d 4h)
> - Claude Code (account 2 of 2), 5-hour limit: **64% left**, resets today 16:30 (in 1h 39m)
> - Claude Code (account 2 of 2), weekly limit: **88% left**, resets Fri Nov 13 17:51 (in 6d 2h)
> - Codex, 5-hour limit: **91% left**, resets today 18:02 (in 3h 11m)
> - Codex, weekly limit: **41% left**, resets Wed Nov 11 16:51 (in 4d 1h)
>
> All numbers are current (checked within the last minute).

## Less usual cases (demo)

**Stale numbers after a rate limit**

```
Claude Code
  5-hour limit: 55% left, resets today 17:10 (in 2h 00m)
  data: stale, last good numbers from today 14:36
  note: rate limited, retrying soon
```

Answer: "Claude Code had **55%** of its 5-hour limit left as of 14:36. The usage service is rate-limiting right now; AgentMeter retries by itself."

**Codex numbers from its last run**

```
Codex
  5-hour limit: 30% left, resets today 15:01 (in 10m)
  data: from today 12:51 (2h 00m ago)
  note: Codex only updates these numbers when it runs.
```

**AgentMeter not installed**

```
AgentMeter is not installed on this computer, so usage can't be checked.

To install AgentMeter, the user can run one of:
  brew install SaeedNoshadi89/tap/agentmeter   (macOS, Homebrew)
  curl -fsSL https://raw.githubusercontent.com/SaeedNoshadi89/agentmeter/main/install.sh | sh   (macOS or Linux)
  Source and docs: https://github.com/SaeedNoshadi89/agentmeter
```
