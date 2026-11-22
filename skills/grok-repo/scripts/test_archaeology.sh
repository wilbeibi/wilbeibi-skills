#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
fixture_dir=$(mktemp -d)
squash_dir=$(mktemp -d)
trap 'rm -rf -- "$fixture_dir" "$squash_dir"' EXIT

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

# Fix evidence beyond the subject prefix: a component-prefixed verb, a body naming the root
# cause, and a negative whose long body uses the house-style opener "Before this change".
printf 'fence\n' >"$fixture_dir/fence.txt"
git -C "$fixture_dir" add fence.txt
git -C "$fixture_dir" commit -qm 'node: prevent stale writes after restore'

printf 'guard\n' >"$fixture_dir/guard.txt"
git -C "$fixture_dir" add guard.txt
git -C "$fixture_dir" commit -q -m 'Add a database guard' -m 'Root cause: the check ran before the row existed.'

printf 'feature\n' >"$fixture_dir/feature.txt"
git -C "$fixture_dir" add feature.txt
git -C "$fixture_dir" commit -q -m 'Add a list endpoint' \
  -m 'Before this change the API returned nothing for lists. This change adds the endpoint and its tests.'

printf 'cache\n' >"$fixture_dir/cache.txt"
git -C "$fixture_dir" add cache.txt
git -C "$fixture_dir" commit -q -m 'perf(cache): skip publish-time rehash' -m 'Cold resume p99 80 ms -> 8 ms (#449); lz4 +18%, zstd +106% vs raw 63.8 ms.'

printf 'index\n' >"$fixture_dir/index.txt"
git -C "$fixture_dir" add index.txt
git -C "$fixture_dir" commit -q -m 'Speed up index lookup' -m 'Binary search replaces the scan: p99 4 ms -> 0.3 ms.'

# Raw length must not win: a pasted stack trace and a squash-merge list are not post-mortems.
printf 'race\n' >"$fixture_dir/race.txt"
git -C "$fixture_dir" add race.txt
trace=$(for i in {1..40}; do printf '3:     #%d N2::Net2::onMainThread(Promise<Void>&&, TaskPriority) /home/dev/flow/Net2.actor.cpp:%d:6 (libfdb_c.so)\n' "$i" "$i"; done)
git -C "$fixture_dir" commit -q -m 'fix: data race in cancel' -m "TSAN output:" -m "$trace"
printf 'squash\n' >"$fixture_dir/squash.txt"
git -C "$fixture_dir" add squash.txt
git -C "$fixture_dir" commit -q -m 'fix: squashed review rounds (#9)' \
  -m "$(printf '* address the first round of review comments on the tracker\n* address the second round of review comments on the tracker\n* address the third round of review comments on the tracker\n')"

printf 'pool\n' >"$fixture_dir/pool.txt"
git -C "$fixture_dir" add pool.txt
git -C "$fixture_dir" commit -q -m 'fix: move slot setup to the blocking pool (#12)' \
  -m "$(printf '* fix: run slot setup on the blocking pool\n\nSlot setup used blocking syscalls on async workers; a burst stalled the runtime.\n\n* test: cover the lease\n')"

printf 'notes\n' >"$fixture_dir/notes.txt"
git -C "$fixture_dir" add notes.txt
git -C "$fixture_dir" commit -q -m 'docs: correct claims contradicted by the code' \
  -m 'The guide said writes were durable before fsync; the code has never promised that, and the root cause was copied prose.'

git -C "$fixture_dir" rm -q deleted.txt
git -C "$fixture_dir" commit -qm 'Remove temporary file'
git -C "$fixture_dir" commit --allow-empty -qm 'Revert broken direction'

# Rank churn, not file count; include insertion-only, deletion-only, mixed,
# binary-only, and a subject containing the old parser's delimiter.
for i in {1..8}; do
  printf 'small\n' >"$fixture_dir/small-$i.txt"
done
git -C "$fixture_dir" add .
git -C "$fixture_dir" commit -qm 'Touch many files'
many_files_sha=$(git -C "$fixture_dir" rev-parse --short HEAD)

for i in {1..100}; do printf 'line %s\n' "$i"; done >"$fixture_dir/large.txt"
git -C "$fixture_dir" add large.txt
git -C "$fixture_dir" commit -qm 'Add many lines | preserve subject'
large_sha=$(git -C "$fixture_dir" rev-parse --short HEAD)

head -30 "$fixture_dir/large.txt" >"$fixture_dir/remaining.txt"
mv "$fixture_dir/remaining.txt" "$fixture_dir/large.txt"
git -C "$fixture_dir" commit -qam 'Delete seventy lines'
delete_sha=$(git -C "$fixture_dir" rev-parse --short HEAD)

for i in {1..30}; do printf 'replacement %s\n' "$i"; done >"$fixture_dir/large.txt"
git -C "$fixture_dir" commit -qam 'Replace thirty lines'
mixed_sha=$(git -C "$fixture_dir" rev-parse --short HEAD)

printf '\0binary\0payload\n' >"$fixture_dir/blob.bin"
git -C "$fixture_dir" add blob.bin
git -C "$fixture_dir" commit -qm 'Add binary payload'

report=$(bash "$script_dir/archaeology.sh" "$fixture_dir")
history=$(awk '/^== HISTORY DEPTH/{keep=1; next} /^==/{keep=0} keep' <<<"$report")
bodies=$(awk '/^== COMMIT BODY YIELD/{keep=1; next} /^==/{keep=0} keep' <<<"$report")
authors=$(awk '/^== COMMIT AUTHORS/{keep=1; next} /^==/{keep=0} keep' <<<"$report")
hot=$(awk '/^== MOST-TOUCHED/{keep=1; next} /^==/{keep=0} keep' <<<"$report")
fixes=$(awk '/^== CURRENT FILES TOUCHED BY FIX/{keep=1; next} /^==/{keep=0} keep' <<<"$report")
reverts=$(awk '/^== REVERT\/ROLLBACK/{keep=1; next} /^==/{keep=0} keep' <<<"$report")
pitfalls=$(awk '/^== LONGEST FIX\/PERF BODIES/{keep=1; next} /^==/{keep=0} keep' <<<"$report")
biggest=$(awk '/^== BIGGEST COMMITS/{keep=1; next} /^==/{keep=0} keep && NF' <<<"$report")

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
assert_contains "$fixes" 'fence.txt'
assert_contains "$fixes" 'guard.txt'
assert_omits "$fixes" 'not-a-fix.txt'
assert_omits "$fixes" 'bug-tracker.txt'
assert_omits "$fixes" 'feature.txt'
assert_contains "$history" 'HISTORY: incremental'
assert_contains "$bodies" 'median body'
assert_contains "$reverts" 'Revert broken direction'
assert_omits "$reverts" 'Discuss fix-prone files and reverts'
assert_contains "$pitfalls" 'Add a database guard'
assert_contains "$pitfalls" 'perf(cache): skip publish-time rehash'
assert_contains "$pitfalls" 'Speed up index lookup'
assert_omits "$pitfalls" 'Add a list endpoint'
assert_contains "$pitfalls" 'fix: move slot setup to the blocking pool'
assert_omits "$pitfalls" 'docs: correct claims'
assert_omits "$pitfalls" 'fix: data race in cancel'
assert_omits "$pitfalls" 'fix: squashed review rounds'
assert_omits "$pitfalls" 'fix: repair current behavior'
ranked_shas=$(awk 'NR <= 4 {print $1}' <<<"$biggest")
expected_shas=$(printf '%s\n' "$large_sha" "$delete_sha" "$mixed_sha" "$many_files_sha")
if [[ "$ranked_shas" != "$expected_shas" ]]; then
  printf 'expected churn order (100, 70, 60, 8 lines):\n%s\nactual:\n%s\n' \
    "$expected_shas" "$biggest" >&2
  exit 1
fi
assert_contains "$biggest" 'Add many lines | preserve subject'
assert_omits "$biggest" 'Add binary payload'
assert_omits "$biggest" 'Revert broken direction'

# A root commit holding most lines ever added is a squash import, whatever its subject says.
git -C "$squash_dir" init -q
git -C "$squash_dir" config user.name Alice
git -C "$squash_dir" config user.email alice@example.test
for i in {1..100}; do printf 'imported %s\n' "$i"; done >"$squash_dir/import.txt"
git -C "$squash_dir" add import.txt
git -C "$squash_dir" commit -qm 'Add the platform'
printf 'one\n' >"$squash_dir/after.txt"
git -C "$squash_dir" add after.txt
git -C "$squash_dir" commit -qm 'Add one line'
squash_report=$(bash "$script_dir/archaeology.sh" "$squash_dir")
assert_contains "$squash_report" 'HISTORY: squash import'
assert_contains "$squash_report" '1 commits since'

printf 'archaeology behavior: ok\n'
