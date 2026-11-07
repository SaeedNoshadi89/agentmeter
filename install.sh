#!/bin/sh
# agentmeter installer
#   curl -fsSL https://raw.githubusercontent.com/SaeedNoshadi89/agentmeter/main/install.sh | sh
#
# Options (environment variables):
#   AGENTMETER_BIN_DIR   where to put the command   (default: ~/.local/bin)
#   AGENTMETER_NO_REX=1  skip the Rex popup setup
#   AGENTMETER_KEY       Rex shortcut                (default: shift+cmd+u)
#   AGENTMETER_UNINSTALL=1  remove agentmeter and its Rex block
set -eu

REPO="SaeedNoshadi89/agentmeter"
REF="${AGENTMETER_REF:-main}"
RAW="https://raw.githubusercontent.com/$REPO/$REF"
BIN_DIR="${AGENTMETER_BIN_DIR:-$HOME/.local/bin}"
KEY="${AGENTMETER_KEY:-shift+cmd+u}"
BIN="$BIN_DIR/agentmeter"
REX_CONFIG="${REX_CONFIG:-${XDG_CONFIG_HOME:-$HOME/.config}/rex/init.lua}"
BEGIN="-- >>> agentmeter >>>"
END="-- <<< agentmeter <<<"

say() { printf '  %s\n' "$*"; }

# Remove a previously installed agentmeter block from the Rex config.
strip_rex_block() {
  [ -f "$REX_CONFIG" ] || return 0
  tmp="$REX_CONFIG.agentmeter.tmp"
  awk -v b="$BEGIN" -v e="$END" '$0==b{skip=1} !skip{print} $0==e{skip=0}' "$REX_CONFIG" > "$tmp"
  mv "$tmp" "$REX_CONFIG"
}

reload_rex() {
  command -v rex >/dev/null 2>&1 && rex config reload >/dev/null 2>&1 || true
}

if [ "${AGENTMETER_UNINSTALL:-}" = 1 ]; then
  rm -f "$BIN"
  strip_rex_block
  reload_rex
  say "agentmeter removed."
  exit 0
fi

command -v python3 >/dev/null 2>&1 || { say "agentmeter needs python3."; exit 1; }

# 1. The command. Use the local checkout when run from one, else download.
mkdir -p "$BIN_DIR"
here=$(cd "$(dirname "$0")" 2>/dev/null && pwd || true)
if [ -n "$here" ] && [ -f "$here/agentmeter" ] && [ -f "$here/integrations/rex/init.lua" ]; then
  cp "$here/agentmeter" "$BIN"
  snippet=$(cat "$here/integrations/rex/init.lua")
else
  curl -fsSL "$RAW/agentmeter" -o "$BIN"
  snippet=$(curl -fsSL "$RAW/integrations/rex/init.lua")
fi
chmod +x "$BIN"
say "installed $BIN"

case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *) say "note: $BIN_DIR is not on your PATH; add it to run \`agentmeter\` directly." ;;
esac

# 2. The Rex popup (only if Rex is installed).
if [ "${AGENTMETER_NO_REX:-}" != 1 ] && command -v rex >/dev/null 2>&1; then
  mkdir -p "$(dirname "$REX_CONFIG")"
  [ -f "$REX_CONFIG" ] && cp "$REX_CONFIG" "$REX_CONFIG.bak"
  strip_rex_block
  {
    printf '\n%s\n' "$BEGIN"
    printf '%s\n' "$snippet" | sed -e "s|@AGENTMETER_BIN@|$BIN|" -e "s|@AGENTMETER_KEY@|$KEY|"
    printf '%s\n' "$END"
  } >> "$REX_CONFIG"
  if rex config check >/dev/null 2>&1; then
    reload_rex
    say "Rex popup ready: press $KEY (or run \`rex do agent_usage\`)."
  else
    [ -f "$REX_CONFIG.bak" ] && mv "$REX_CONFIG.bak" "$REX_CONFIG"
    say "Rex config check failed; your init.lua was restored. Run \`rex config check\` for details."
  fi
fi

say "try it: agentmeter"
