#!/usr/bin/env bash
# archaeology.sh [repo-dir] — one-shot git history digest for understanding a codebase.
# Prints: founding commits, history depth (squash/import detection), recent direction, authors,
# frequently touched current files, files touched by fix commits, reverts, the largest commits,
# commit-body yield and, when gh can reach GitHub, issue-tracker usage and PR review threads.
# Read-only; stdlib git only.
# No pipefail: every pipeline ends in head/sort/cut, and upstream git/grep
# legitimately exit non-zero on SIGPIPE or empty match sets.
set -eu
cd "${1:-.}"
git rev-parse --is-inside-work-tree >/dev/null

section() { printf '\n== %s ==\n' "$1"; }

section "FOUNDING COMMITS (original intent)"
git log --oneline --reverse | head -15

section "HISTORY DEPTH (is the why in git at all?)"
# A root commit holding most of the lines ever added means public history starts with an
# import: `git log -S` and blame stop there, and older rationale lives in PR threads and
# commit bodies. A shallow clone hides everything below its cutoff.
root=$(git rev-list --max-parents=0 HEAD | tail -1)
commits=$(git rev-list --count HEAD)
root_date=$(git log -1 --format=%ad --date=short "$root")
root_added=$(git show --numstat --format= "$root" | awk -F '\t' '$1 ~ /^[0-9]+$/ { n += $1 } END { print n + 0 }')
all_added=$(git log --numstat --format= | awk -F '\t' '$1 ~ /^[0-9]+$/ { n += $1 } END { print n + 0 }')
root_share=0
if [ "$all_added" -gt 0 ]; then root_share=$(( root_added * 100 / all_added )); fi
printf 'root %s (%s) added %s of the %s text lines ever added (%s%%); %s commits in total\n' \
  "$(git rev-parse --short "$root")" "$root_date" "$root_added" "$all_added" "$root_share" "$commits"
if [ "$(git rev-parse --is-shallow-repository)" = true ]; then
  echo "HISTORY: shallow clone — git fetch --unshallow before reading any of this as history"
elif [ "$root_share" -gt 50 ]; then
  echo "HISTORY: squash import on $root_date; $((commits - 1)) commits since. Older rationale is not in git: read PR threads, commit bodies and status-headed docs"
else
  echo "HISTORY: incremental since $root_date; git log -S and blame reach the origin of most lines"
fi

section "RECENT DIRECTION (last 30, no merges)"
git log --oneline --no-merges | head -30

section "COMMIT AUTHORS (activity distribution, not bus factor)"
# HEAD stays explicit: without a revision, shortlog reads a log from stdin when stdin is not a tty.
git shortlog -sn --no-merges HEAD | head -12

section "MOST-TOUCHED CURRENT FILES (reading candidates, not line churn)"
awk '
    NR == FNR { current[$0] = 1; next }
    current[$0] { touches[$0]++ }
    END { for (path in touches) print touches[path], path }
  ' <(git ls-files) <(git log --no-merges --name-only --pretty=format:) \
  | sort -rn | head -20

section "CURRENT FILES TOUCHED BY FIX COMMITS (investigation candidates)"
# Fix evidence: conventional subject prefixes, "<component>: fix|repair|stop|prevent|restore|correct",
# fix words anywhere in the subject, and body phrases (regression, root cause, fails closed,
# "Fixes #n", "reverts"). "Before this change" is deliberately not one: some projects open
# every body with it.
fix_shas=$(git log --no-merges --format='%H%x1f%s%x1f%b%x1e' \
  | awk '
      BEGIN { RS = "\x1e"; FS = "\x1f" }
      {
        sha = $1; gsub(/[[:space:]]/, "", sha)
        subject = tolower($2); body = tolower($3)
        keep = subject ~ /^(fix|fixes|fixed|bugfix|hotfix|repair|repairs|correct|corrects)(\([^)]*\))?!?([:[:space:]])/ ||
               subject ~ /^bug(\([^)]*\))?!?:/ ||
               subject ~ /^[a-z0-9_.-]+(\([^)]*\))?!?: (fix|fixes|repair|repairs|stop|stops|prevent|prevents|restore|restores|correct|corrects)([^[:alnum:]_]|$)/ ||
               subject ~ /(^|[^[:alnum:]_])(fixed|fixes|bugfix|hotfix)([^[:alnum:]_]|$)/ ||
               body ~ /(^|[^[:alnum:]_])(regression|root cause|fails? closed|fixes #[0-9]+|reverts)([^[:alnum:]_]|$)/
        if (keep && sha != "") print sha
      }')
awk '
    FNR == 1 { file++ }
    file == 1 { current[$0] = 1; next }
    file == 2 { fix[$0] = 1; next }
    /^@@SHA@@/ { on = (substr($0, 8) in fix); next }
    on && current[$0] { touches[$0]++ }
    END { for (path in touches) print touches[path], path }
  ' <(git ls-files) <(printf '%s\n' "$fix_shas") <(git log --no-merges --format='@@SHA@@%H' --name-only) \
  | sort -rn | head -15

section "REVERT/ROLLBACK SUBJECTS (possible abandoned directions)"
git log --no-merges --format='%h%x09%s' \
  | awk -F '\t' '
      {
        subject = tolower($2)
        if (subject ~ /^(revert(ed|s|ing)?|roll[ -]?back)([^[:alnum:]_]|$)/) print
      }' \
  | head -10

section "BIGGEST COMMITS (text lines added + deleted; binaries excluded — reading candidates)"
git log --no-merges --pretty='@@COMMIT@@%h %ad %s' --date=short --numstat \
  | awk -F '\t' '
      function emit() { if (n > 0) printf "%012d\t%s\n", n, header }
      /^@@COMMIT@@/ {
        emit()
        sub(/^@@COMMIT@@/, "")
        header=$0; n=0
        next
      }
      $1 ~ /^[0-9]+$/ && $2 ~ /^[0-9]+$/ { n += $1 + $2 }
      END { emit() }' \
  | sort -rn | head -12 | cut -f2-

section "COMMIT BODY YIELD (median body length, last 100 non-merge commits)"
# Long bodies mean the design notes travel with the diff; short ones push the why to PR threads.
git log --no-merges -100 --format='%x1e%b' \
  | awk 'BEGIN { RS = "\x1e" } NR > 1 { gsub(/^\n+|\n+$/, ""); print length($0) }' \
  | sort -n \
  | awk '
      { len[NR] = $1 }
      END {
        if (NR == 0) { print "no commits"; exit }
        median = len[int((NR + 1) / 2)]
        printf "median body: %d chars over %d commits\n", median, NR
        if (median > 300) print "BODIES: long — read them in full: git log --format=\"%h %s%n%b\""
        else print "BODIES: short — rationale is in PR threads or the tracker, not in git log"
      }'

section "ISSUE TRACKER (optional: needs gh, a GitHub remote, and auth)"
# Every failure here is expected on a local, non-GitHub, or unauthenticated repo:
# say why the section is empty rather than letting `set -e` kill the git digest.
gh_ready() {
  command -v gh >/dev/null 2>&1 || { echo "skipped: gh not installed"; return 1; }
  git remote -v 2>/dev/null | grep -q 'github\.com' \
    || { echo "skipped: no github.com remote — check this project's own tracker by hand"; return 1; }
  gh auth status >/dev/null 2>&1 || { echo "skipped: gh not authenticated (gh auth login)"; return 1; }
}
gh_issues() {
  gh_ready || return 0
  printf -- '-- usage --\n'
  # GitHub logins and git authors do not match reliably, so count issues and distinct filers only.
  total=$(gh issue list --state all --limit 1000 --json number --jq 'length' 2>/dev/null || echo '?')
  open=$(gh issue list --state open --limit 1000 --json number --jq 'length' 2>/dev/null || echo '?')
  filers=$(gh issue list --state all --limit 1000 --json author --jq '[.[].author.login] | unique | length' 2>/dev/null || echo '?')
  if [ "$total" = 1000 ]; then total='1000+'; fi
  echo "issues: $total total, $open open, $filers distinct filers"
  if [ "$total" != '?' ] && [ "$total" != '1000+' ] && [ "$total" -lt 10 ]; then
    echo "TRACKER: barely used — treat PR review threads as the tracker (next section)"
  fi

  printf -- '\n-- oldest open (long-lived soft spots) --\n'
  gh issue list --state open --limit 10 --search 'sort:created-asc' 2>&1 | head -12
  printf -- '\n-- most discussed, any state (contested decisions) --\n'
  gh issue list --state all --limit 10 --search 'sort:comments-desc' 2>&1 | head -12
  printf -- '\n-- closed as not-planned (stated non-goals) --\n'
  gh issue list --state closed --limit 10 --search 'reason:not-planned sort:updated-desc' 2>&1 | head -12
}
gh_issues

section "PR REVIEW THREADS (optional: where review-driven repos argue)"
gh_prs() {
  gh_ready || return 0
  printf -- '-- most discussed merged PRs --\n'
  gh pr list --state merged --limit 200 --json number,title,comments \
    --jq 'sort_by(-(.comments | length))[:10][] | "#\(.number)\t\(.comments | length) comments\t\(.title)"' 2>&1 | head -12
  printf -- '\n-- closed without merging (rejected directions; the not-planned issues of a PR-driven repo) --\n'
  gh pr list --state closed --search 'is:unmerged' --limit 10 2>&1 | head -12
}
gh_prs

section "NEXT: read the big ones in full"
echo "git show --stat <sha>        # commit messages often contain the design doc"
echo "git log --follow --oneline -- <hot-file>"
echo "git log -S '<symbol>' --oneline   # when a concept appeared or died"
echo "gh issue list --search '<term>' --state all   # the pressure behind the commit"
echo "gh issue view <n> --comments      # read closed ones too: rejections explain designs"
echo "gh pr view <n> --json body,comments,reviews   # the review thread (--comments cannot combine with --json)"
