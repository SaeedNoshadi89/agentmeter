#!/bin/sh
# Release agentmeter and update the Homebrew tap.
#   scripts/release.sh 0.2.1 "One-line summary of the release"
#
# Before running: set VERSION in ./agentmeter to the same number, commit and push.
# Needs: gh (logged in), and the tap cloned at ~/homebrew-tap (or set TAP_DIR).
set -eu

version="${1:?usage: scripts/release.sh VERSION [\"summary\"]}"
summary="${2:-agentmeter $version}"
repo="SaeedNoshadi89/agentmeter"
tap_dir="${TAP_DIR:-$HOME/homebrew-tap}"
cd "$(dirname "$0")/.."

# 1. Checks
grep -q "^VERSION = \"$version\"" agentmeter || { echo "VERSION in ./agentmeter is not $version"; exit 1; }
[ -z "$(git status --porcelain)" ] || { echo "Commit your changes first."; exit 1; }
git fetch -q origin
[ "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)" ] || { echo "Push main first."; exit 1; }
tests/cli.sh ./agentmeter | tail -1

# 2. Tag and GitHub release
git tag "v$version"
git push -q origin "v$version"
gh release create "v$version" --verify-tag --title "agentmeter $version" --notes "$summary

\`\`\`sh
brew install SaeedNoshadi89/tap/agentmeter     # or: brew upgrade agentmeter
\`\`\`"

# 3. Homebrew formula (Git sources are pinned to the release commit).
revision=$(git rev-parse "v$version^{commit}")
cd "$tap_dir"
git pull -q
if grep -q 'agentmeter.git"' Formula/agentmeter.rb; then
  sed -i '' -E "s/tag: \"v[0-9.]+\"/tag: \"v$version\"/; s/revision: \"[0-9a-f]{40}\"/revision: \"$revision\"/; s/^  version \"[0-9.]+\"/  version \"$version\"/" Formula/agentmeter.rb
else
  archive=$(mktemp)
  trap 'rm -f "$archive"' EXIT
  curl -fsSL "https://github.com/$repo/archive/refs/tags/v$version.tar.gz" -o "$archive"
  sha=$(shasum -a 256 "$archive" | cut -d' ' -f1)
  sed -i '' -E "s|archive/refs/tags/v[0-9.]+\.tar\.gz|archive/refs/tags/v$version.tar.gz|; s/sha256 \"[0-9a-f]{64}\"/sha256 \"$sha\"/" Formula/agentmeter.rb
fi
git commit -qam "agentmeter $version"
git push -q

# 4. Check it installs
brew update -q >/dev/null 2>&1 || true
HOMEBREW_NO_AUTO_UPDATE=1 brew upgrade agentmeter || HOMEBREW_NO_AUTO_UPDATE=1 brew install SaeedNoshadi89/tap/agentmeter
"$(brew --prefix)/bin/agentmeter" --version
echo "Released $version."
