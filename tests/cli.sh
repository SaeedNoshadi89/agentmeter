#!/bin/bash
# Full CLI test for agentmeter:  tests/cli.sh ./agentmeter
# Every command that writes config runs against a temporary REX_CONFIG and HOME,
# so your real Rex and Claude Code settings are never changed.
# Some checks read your real agent logins, so sign in to Claude Code and Codex first.
A="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"; T=$(mktemp -d); pass=0; fail=0
REAL_REX="${XDG_CONFIG_HOME:-$HOME/.config}/rex/init.lua"
before=$(cat "$REAL_REX" 2>/dev/null)
ok(){ printf '  ok    %s\n' "$1"; pass=$((pass+1)); }
no(){ printf '  FAIL  %s\n        %s\n' "$1" "$2"; fail=$((fail+1)); }
t(){ name="$1"; shift; out=$("$@" 2>&1); code=$?; }
strip(){ sed 's/\x1b\[[0-9;?]*[A-Za-z]//g; s/\x1b_G[^\x1b]*\x1b\\//g'; }

echo "basics"
t v "$A" --version; [[ $code == 0 && $out == agentmeter\ * ]] && ok "--version ($out)" || no --version "$out"
t h "$A" --help; [[ $code == 0 && $out == *statusline* && $out == *shortcut* ]] && ok "--help lists commands" || no --help "$out"
t d "$A"; s=$(echo "$out" | strip); [[ $code == 0 && $s == *"Claude Code"* && $s == *Codex* ]] && ok "default view shows agents" || no default "$s"
[[ "$out" != *$'\e_G'* ]] && ok "no image codes when output isn't a terminal" || no "piped output" "has kitty codes"
t j "$A" --json; echo "$out" | python3 -c 'import json,sys;d=json.load(sys.stdin);assert d and all("agent" in v for v in d.values())' && ok "--json is valid ($(echo "$out" | python3 -c 'import json,sys;print(len(json.load(sys.stdin)))') entries)" || no --json "$out"
t n "$A" --no-icons; [[ $code == 0 && $(echo "$out"|strip) == *"✻"* ]] && ok "--no-icons uses text marks" || no --no-icons "$out"
t dm "$A" --demo; [[ $(echo "$out"|strip) == *work@example.com* && $(echo "$out"|strip) == *personal@example.com* ]] && ok "--demo shows made-up accounts" || no --demo "$out"
t dj "$A" --demo --json; echo "$out" | python3 -c 'import json,sys;json.load(sys.stdin)' && ok "--demo --json is valid" || no "--demo --json" "$out"
[[ "$(echo "$out")" != *gmail* ]] && ok "--demo contains no real emails" || no "--demo privacy" "found gmail"

echo "accounts"
t c1 "$A" --claude-config "$HOME/.claude-personal" --json; n=$(echo "$out" | python3 -c 'import json,sys;print(sum(k.startswith("claude:") for k in json.load(sys.stdin)))'); [[ $n == 1 ]] && ok "--claude-config picks one account" || no --claude-config "$n entries"
t c2 "$A" --claude-config /nonexistent --json; [[ $out == *"not logged in"* ]] && ok "--claude-config with no login says so" || no "--claude-config bad" "$out"

echo "status line"
t s1 sh -c "echo '{}' | env -u CLAUDE_CONFIG_DIR '$A' statusline"; [[ $code == 0 && $(echo "$out"|strip) == *"✻"* ]] && ok "statusline prints a line" || no statusline "$out"
a=$(echo '{}' | env -u CLAUDE_CONFIG_DIR "$A" statusline --only claude | strip); b=$(echo '{}' | CLAUDE_CONFIG_DIR="$HOME/.claude-personal" "$A" statusline --only claude | strip)
e1=$(python3 -c 'import json,os;print((json.load(open(os.path.expanduser("~/.claude.json"))).get("oauthAccount") or {}).get("emailAddress"))' 2>/dev/null)
e2=$(python3 -c 'import json,os;print((json.load(open(os.path.expanduser("~/.claude-personal/.claude.json"))).get("oauthAccount") or {}).get("emailAddress"))' 2>/dev/null)
if [[ $a == *retrying* || $b == *retrying* || $a == *"not logged in"* || $e1 == "$e2" ]]; then
  printf '  skip  %s\n' "statusline follows the session's account (needs two different accounts with numbers)"
else
  [[ -n $a && -n $b && $a != "$b" ]] && ok "statusline follows the session's account" || no "statusline account" "default=$a personal=$b"
fi
t s2 sh -c "echo '{}' | '$A' statusline --only codex"; s=$(echo "$out"|strip); [[ $s == ">_"* && $s != *"✻"* ]] && ok "statusline --only codex" || no "--only codex" "$s"
t s3 sh -c "echo '{}' | '$A' statusline --demo --only claude,codex"; [[ $(echo "$out"|strip) == *"5h 64%"* ]] && ok "statusline --demo" || no "statusline --demo" "$out"
ms=$(python3 -c "
import subprocess,time;t=time.time()
for _ in range(5): subprocess.run(['$A','statusline'],input=b'{}',capture_output=True)
print(int((time.time()-t)/5*1000))"); [[ $ms -lt 300 ]] && ok "statusline is fast (${ms} ms)" || no "statusline speed" "${ms} ms"
t r "$A" --refresh; [[ $code == 0 ]] && ok "--refresh" || no --refresh "$out"

echo "Rex setup (temp REX_CONFIG)"
export REX_CONFIG="$T/init.lua"; printf -- '-- my config\nrex.bind("cmd+k", "session.picker")\n' > "$REX_CONFIG"
t r1 "$A" setup-rex; [[ $code == 0 && $(grep -c 'agentmeter >>>' $REX_CONFIG) == 1 ]] && ok "setup-rex adds one block" || no setup-rex "$out"
grep -q 'cmd+k' $REX_CONFIG && ok "setup-rex keeps the user's own config" || no "keeps config" "lost"
"$A" setup-rex >/dev/null; [[ $(grep -c 'agentmeter >>>' $REX_CONFIG) == 1 ]] && ok "running setup-rex twice keeps one block" || no "idempotent" "dup"
t k1 "$A" shortcut; [[ $out == shift+cmd+u ]] && ok "shortcut shows default ($out)" || no shortcut "$out"
t k2 "$A" shortcut alt+cmd+u; [[ $("$A" shortcut) == alt+cmd+u ]] && ok "shortcut changes the key" || no "shortcut set" "$out"
"$A" setup-rex >/dev/null; [[ $("$A" shortcut) == alt+cmd+u ]] && ok "setup-rex keeps a custom key" || no "keep key" "$("$A" shortcut)"
t y1 "$A" style; [[ $out == float ]] && ok "style shows float" || no style "$out"
t y2 "$A" style pane; [[ $("$A" style) == pane ]] && ok "style pane" || no "style pane" "$out"
t y3 "$A" style bogus; [[ $code != 0 ]] && ok "style rejects a bad value" || no "style bogus" "$out"
"$A" style float >/dev/null
REX_BIN=$(command -v rex); if [[ -n $REX_BIN ]]; then rex config check >/dev/null 2>&1 && ok "rex config check passes on the generated block" || no "rex config check" "$(rex config check 2>&1 | tail -2)"; fi
t r2 "$A" remove-rex; [[ $(grep -c agentmeter $REX_CONFIG) == 0 ]] && grep -q 'cmd+k' $REX_CONFIG && ok "remove-rex removes only its block" || no remove-rex "$(cat $REX_CONFIG)"
unset REX_CONFIG

echo "status line setup (temp HOME, real login)"
H="$T/home"; mkdir -p "$H/.claude"; echo '{"model":"x"}' > "$H/.claude/settings.json"
run(){ HOME="$H" "$A" "$@" 2>&1; }
run statusline on --only claude >/dev/null; c=$(python3 -c "import json;print(json.load(open('$H/.claude/settings.json'))['statusLine']['command'])"); [[ $c == *"statusline --only claude" ]] && ok "statusline on writes settings" || no "statusline on" "$c"
python3 -c "import json;assert json.load(open('$H/.claude/settings.json'))['model']=='x'" && ok "statusline on keeps other settings" || no "keeps settings" ""
[[ -f "$H/.claude/settings.json.bak" ]] && ok "statusline on saves a backup" || no backup ""
[[ $(run statusline status) == "on (only: claude)" ]] && ok "statusline status: $(run statusline status)" || no status "$(run statusline status)"
run statusline off >/dev/null; [[ $(run statusline status) == off ]] && ok "statusline off" || no off "$(run statusline status)"
run statusline toggle >/dev/null; [[ $(run statusline status) == "on (only: claude)" ]] && ok "toggle on keeps --only" || no toggle "$(run statusline status)"
run statusline toggle >/dev/null; [[ $(run statusline status) == off ]] && ok "toggle off" || no "toggle off" "$(run statusline status)"
python3 -c "import json;p='$H/.claude/settings.json';d=json.load(open(p));d['statusLine']={'type':'command','command':'my-own-line'};json.dump(d,open(p,'w'))"
o=$(run statusline on); [[ $o == *skipped* && $(python3 -c "import json;print(json.load(open('$H/.claude/settings.json'))['statusLine']['command'])") == my-own-line ]] && ok "won't replace someone's own status line" || no "no clobber" "$o"
run statusline on --force >/dev/null; [[ $(python3 -c "import json;print(json.load(open('$H/.claude/settings.json'))['statusLine']['command'])") == *agentmeter* ]] && ok "--force replaces it" || no "--force" ""

echo "setup (temp HOME, temp REX_CONFIG, no terminal)"
H2="$T/home2"; mkdir -p "$H2/.claude"; echo '{}' > "$H2/.claude/settings.json"; R2="$T/init3.lua"; : > "$R2"
o=$(HOME="$H2" REX_CONFIG="$R2" "$A" setup < /dev/null 2>&1)
[[ $o == *"Agents found"* && $o == *"Done."* ]] && ok "setup runs and lists agents" || no setup "$o"
[[ $(grep -c 'agentmeter >>>' "$R2") == 1 ]] && ok "setup adds the Rex popup" || no "setup rex" "$(cat $R2)"
[[ $(HOME="$H2" "$A" statusline status) == off ]] && ok "setup without a terminal leaves Claude settings alone" || no "setup unattended" "$(HOME="$H2" "$A" statusline status)"
HOME="$H2" REX_CONFIG="$R2" "$A" setup --yes >/dev/null 2>&1; [[ $(HOME="$H2" "$A" statusline status) == on* && $(grep -c 'agentmeter >>>' "$R2") == 1 ]] && ok "setup --yes turns on the status line, no duplicates" || no "setup --yes" "$(HOME="$H2" "$A" statusline status)"
HOME="$H2" REX_CONFIG="$R2" "$A" statusline off >/dev/null; HOME="$H2" REX_CONFIG="$R2" "$A" setup --yes --no-statusline >/dev/null 2>&1; [[ $(HOME="$H2" "$A" statusline status) == off ]] && ok "setup --no-statusline" || no "--no-statusline" ""

echo "installer (temp dir, temp REX_CONFIG)"
export REX_CONFIG="$T/init2.lua"; : > "$REX_CONFIG"
B="$T/bin"; o=$(AGENTMETER_BIN_DIR=$B AGENTMETER_NO_REX=1 AGENTMETER_NO_STATUSLINE=1 sh "$(dirname "$A")/install.sh" < /dev/null 2>&1); [[ -x $B/agentmeter && $($B/agentmeter --version) == agentmeter* ]] && ok "install.sh installs" || no install "$o"
o=$(AGENTMETER_BIN_DIR=$B AGENTMETER_UNINSTALL=1 sh "$(dirname "$A")/install.sh" 2>&1); [[ ! -e $B/agentmeter ]] && ok "install.sh uninstalls" || no uninstall "$o"

unset REX_CONFIG

echo "your real config"
[[ "$(cat "$REAL_REX" 2>/dev/null)" == "$before" ]] && ok "real Rex config unchanged" || no "real Rex config" "changed by the tests"

rm -rf "$T"
echo; echo "$pass passed, $fail failed"; [[ $fail == 0 ]]
