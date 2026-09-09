#!/usr/bin/env bash
# archaeology.sh [repo-dir] — one-shot git history digest for understanding a codebase.
# Prints: founding commits, recent direction, authors, frequently touched current files,
# files touched by fix commits, reverts, and the largest commits by lines touched.
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

section "COMMIT AUTHORS (activity distribution, not bus factor)"
git shortlog -sn --no-merges HEAD | head -12

section "MOST-TOUCHED CURRENT FILES (reading candidates, not line churn)"
awk '
    NR == FNR { current[$0] = 1; next }
    current[$0] { touches[$0]++ }
    END { for (path in touches) print touches[path], path }
  ' <(git ls-files) <(git log --no-merges --name-only --pretty=format:) \
  | sort -rn | head -20

section "CURRENT FILES TOUCHED BY FIX COMMITS (investigation candidates)"
awk '
    NR == FNR { current[$0] = 1; next }
    /^@@SUBJECT@@/ {
      subject = tolower(substr($0, 12))
      keep = subject ~ /^(fix|fixes|fixed|bugfix|hotfix|repair|repairs|correct|corrects)(\([^)]*\))?!?([:[:space:]])/ ||
             subject ~ /^bug(\([^)]*\))?!?:/ ||
             subject ~ /(^|[^[:alnum:]_])(fixed|fixes|bugfix|hotfix)([^[:alnum:]_]|$)/
      next
    }
    keep && current[$0] { touches[$0]++ }
    END { for (path in touches) print touches[path], path }
  ' <(git ls-files) <(git log --no-merges --format='@@SUBJECT@@%s' --name-only) \
  | sort -rn | head -15

section "REVERT/ROLLBACK SUBJECTS (possible abandoned directions)"
git log --no-merges --format='%h%x09%s' \
  | awk -F '\t' '
      {
        subject = tolower($2)
        if (subject ~ /^(revert(ed|s|ing)?|roll[ -]?back)([^[:alnum:]_]|$)/) print
      }' \
  | head -10

section "BIGGEST COMMITS (by lines touched — likely rewrites/redesigns)"
git log --no-merges --pretty='%h|%ad|%s' --date=short --shortstat \
  | awk -F'|' '
      NF==3 { h=$1; d=$2; s=$3; next }
      /files? changed/ {
        n=0; for(i=1;i<=NF;i++) if ($i ~ /insertion|deletion/) { split($i,a," "); n+=a[1] }
        printf "%08d\t%s %s %s\n", n, h, d, s
      }' \
  | sort -rn | head -12 | cut -f2-

section "ISSUE TRACKER (optional: needs gh, a GitHub remote, and auth)"
# Every failure here is expected on a local, non-GitHub, or unauthenticated repo:
# say why the section is empty rather than letting `set -e` kill the git digest.
gh_issues() {
  command -v gh >/dev/null 2>&1 || { echo "skipped: gh not installed"; return 0; }
  git remote -v 2>/dev/null | grep -q 'github\.com' \
    || { echo "skipped: no github.com remote — check this project's own tracker by hand"; return 0; }
  gh auth status >/dev/null 2>&1 || { echo "skipped: gh not authenticated (gh auth login)"; return 0; }

  printf -- '-- oldest open (long-lived soft spots) --\n'
  gh issue list --state open --limit 10 --search 'sort:created-asc' 2>&1 | head -12
  printf -- '\n-- most discussed, any state (contested decisions) --\n'
  gh issue list --state all --limit 10 --search 'sort:comments-desc' 2>&1 | head -12
  printf -- '\n-- closed as not-planned (stated non-goals) --\n'
  gh issue list --state closed --limit 10 --search 'reason:not-planned sort:updated-desc' 2>&1 | head -12
}
gh_issues

section "NEXT: read the big ones in full"
echo "git show --stat <sha>        # commit messages often contain the design doc"
echo "git log --follow --oneline -- <hot-file>"
echo "git log -S '<symbol>' --oneline   # when a concept appeared or died"
echo "gh issue list --search '<term>' --state all   # the pressure behind the commit"
echo "gh issue view <n> --comments      # read closed ones too: rejections explain designs"
