#!/usr/bin/env bash
# archaeology.sh [repo-dir] — one-shot git history digest for understanding a codebase.
# Prints: founding commits, recent direction, authors, hot (most-churned) files,
# fix-prone files, reverts, and the largest commits by lines touched.
# Read-only; stdlib git only.
# No pipefail: every pipeline ends in head/sort/cut, and upstream git/grep
# legitimately exit non-zero on SIGPIPE or empty match sets.
set -eu
cd "${1:-.}"
git rev-parse --is-inside-work-tree >/dev/null

section() { printf '\n== %s ==\n' "$1"; }

section "FOUNDING COMMITS (original intent)"
git log --oneline --reverse | head -15

section "RECENT DIRECTION (last 30, no merges)"
git log --oneline --no-merges | head -30

section "AUTHORS (bus factor)"
git shortlog -sn --no-merges | head -12

section "HOT FILES (most-churned = load-bearing; blame-worthy)"
git log --no-merges --name-only --pretty=format: \
  | grep -v '^$' | sort | uniq -c | sort -rn | head -20

section "FIX-PRONE FILES (named in fix/bug commits — where invariants bite)"
git log --no-merges -i -E --grep='fix|bug|regress' --name-only --pretty=format: \
  | grep -v '^$' | sort | uniq -c | sort -rn | head -15

section "ABANDONED DIRECTIONS (reverts/rollbacks — designs that didn't survive)"
git log --oneline --no-merges -i -E --grep='revert|roll ?back' | head -10

section "BIGGEST COMMITS (by lines touched — likely rewrites/redesigns)"
git log --no-merges --pretty='%h|%ad|%s' --date=short --shortstat \
  | awk -F'|' '
      NF==3 { h=$1; d=$2; s=$3; next }
      /files? changed/ {
        n=0; for(i=1;i<=NF;i++) if ($i ~ /insertion|deletion/) { split($i,a," "); n+=a[1] }
        printf "%08d\t%s %s %s\n", n, h, d, s
      }' \
  | sort -rn | head -12 | cut -f2-

section "NEXT: read the big ones in full"
echo "git show --stat <sha>        # commit messages often contain the design doc"
echo "git log --follow --oneline -- <hot-file>"
echo "git log -S '<symbol>' --oneline   # when a concept appeared or died"
