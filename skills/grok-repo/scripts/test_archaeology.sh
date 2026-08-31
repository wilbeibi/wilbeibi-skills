#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
fixture_dir=$(mktemp -d)
trap 'rm -rf -- "$fixture_dir"' EXIT

# Isolate from the developer's git setup: a global commit.gpgsign, a hooksPath,
# or GIT_AUTHOR_* in the environment would break the fixture before any assertion.
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null
unset GIT_AUTHOR_NAME GIT_AUTHOR_EMAIL GIT_COMMITTER_NAME GIT_COMMITTER_EMAIL

git -C "$fixture_dir" init -q
git -C "$fixture_dir" config user.name Alice
git -C "$fixture_dir" config user.email alice@example.test

printf 'initial\n' >"$fixture_dir/current.txt"
printf 'temporary\n' >"$fixture_dir/deleted.txt"
git -C "$fixture_dir" add current.txt deleted.txt
git -C "$fixture_dir" commit -qm 'Initial import'

printf 'discussion\n' >"$fixture_dir/not-a-fix.txt"
git -C "$fixture_dir" add not-a-fix.txt
git -C "$fixture_dir" commit -qm 'Discuss fix-prone files and reverts'

git -C "$fixture_dir" config user.name Bob
git -C "$fixture_dir" config user.email bob@example.test
printf 'repaired\n' >>"$fixture_dir/current.txt"
git -C "$fixture_dir" add current.txt
git -C "$fixture_dir" commit -qm 'fix: repair current behavior'

printf 'crash\n' >"$fixture_dir/bug-report.txt"
git -C "$fixture_dir" add bug-report.txt
git -C "$fixture_dir" commit -qm 'Bug: crash on empty input'

printf 'migration\n' >"$fixture_dir/bug-tracker.txt"
git -C "$fixture_dir" add bug-tracker.txt
git -C "$fixture_dir" commit -qm 'Bug tracker migration'

git -C "$fixture_dir" rm -q deleted.txt
git -C "$fixture_dir" commit -qm 'Remove temporary file'
git -C "$fixture_dir" commit --allow-empty -qm 'Revert broken direction'

report=$(bash "$script_dir/archaeology.sh" "$fixture_dir")
authors=$(awk '/^== COMMIT AUTHORS/{keep=1; next} /^==/{keep=0} keep' <<<"$report")
hot=$(awk '/^== MOST-TOUCHED/{keep=1; next} /^==/{keep=0} keep' <<<"$report")
fixes=$(awk '/^== CURRENT FILES TOUCHED BY FIX/{keep=1; next} /^==/{keep=0} keep' <<<"$report")
reverts=$(awk '/^== REVERT\/ROLLBACK/{keep=1; next} /^==/{keep=0} keep' <<<"$report")

assert_contains() {
  local haystack=$1 needle=$2
  grep -qF -- "$needle" <<<"$haystack" || {
    printf 'expected report section to contain: %s\n' "$needle" >&2
    exit 1
  }
}

assert_omits() {
  local haystack=$1 needle=$2
  if grep -qF -- "$needle" <<<"$haystack"; then
    printf 'expected report section to omit: %s\n' "$needle" >&2
    exit 1
  fi
}

assert_contains "$authors" 'Alice'
assert_contains "$authors" 'Bob'
assert_contains "$hot" 'current.txt'
assert_omits "$hot" 'deleted.txt'
assert_contains "$fixes" 'current.txt'
assert_contains "$fixes" 'bug-report.txt'
assert_omits "$fixes" 'not-a-fix.txt'
assert_omits "$fixes" 'bug-tracker.txt'
assert_contains "$reverts" 'Revert broken direction'
assert_omits "$reverts" 'Discuss fix-prone files and reverts'

printf 'archaeology behavior: ok\n'
