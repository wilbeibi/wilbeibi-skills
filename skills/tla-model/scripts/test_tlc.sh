#!/usr/bin/env bash
# Self-test for tlc.py against examples/MiniLock. Needs java and tla2tools.jar (see tlc.py);
# exits 0 with SKIP when either is missing.
set -uo pipefail

here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
tlc="$here/tlc.py"
ex="$here/../examples"
work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT

if ! "$tlc" check "$ex/MiniLock.tla" -c "$ex/MiniLock.cfg" >"$work/out" 2>&1; then
  if grep -qE 'java not found|tla2tools.jar not found' "$work/out"; then
    echo "SKIP: $(cat "$work/out")"; exit 0
  fi
fi

fail=0
expect() { # expect <exit> <grep pattern> <label> -- cmd...
  local want=$1 pat=$2 label=$3; shift 4
  "$@" >"$work/out" 2>&1; local got=$?
  if [[ $got -ne $want ]] || ! grep -qE "$pat" "$work/out"; then
    echo "FAIL $label: exit $got (want $want), pattern '$pat'"; sed 's/^/  /' "$work/out"; fail=1
  else
    echo "ok   $label"
  fi
}

expect 0 'result: clean' 'clean safety run' -- "$tlc" check "$ex/MiniLock.tla" -c "$ex/MiniLock.cfg"
expect 0 'result: clean' 'clean liveness run' -- "$tlc" check "$ex/MiniLock.tla" -c "$ex/MiniLockLive.cfg"
expect 0 'KILLED' 'guard mutant kills Mutex' -- "$tlc" mutant "$ex/MiniLock.tla" -c "$ex/MiniLock.cfg" \
  --replace $'            /\\ lock = None\n' '' --expect Mutex
expect 0 'KILLED' 'fairness mutant kills StarvationFree' -- "$tlc" mutant "$ex/MiniLock.tla" -c "$ex/MiniLockLive.cfg" \
  --replace ' /\ SF_vars(Grant(c))' '' --expect StarvationFree
expect 1 'SURVIVED' 'unrelated property does not catch weakened Mutex' -- "$tlc" mutant "$ex/MiniLock.tla" -c "$ex/MiniLock.cfg" \
  --replace '"crit"}) <= 1' '"crit"}) <= 2' --expect Consistency
expect 3 'exactly once' 'ambiguous replace rejected' -- "$tlc" mutant "$ex/MiniLock.tla" -c "$ex/MiniLock.cfg" \
  --replace 'lock = None' 'TRUE' --expect Mutex
expect 3 'MUTANT INVALID' 'unparsable mutant reported' -- "$tlc" mutant "$ex/MiniLock.tla" -c "$ex/MiniLock.cfg" \
  --replace "lock' = c"$'\n' "lock' = c +"$'\n' --expect Mutex

# Mutants copy only .tla/.cfg files, so unrelated files beside the spec are ignored.
mkdir "$work/junk"; cp "$ex"/MiniLock.* "$work/junk/"; mkdir "$work/junk/node_modules"; : >"$work/junk/big.bin"
expect 0 'KILLED' 'mutant ignores non-spec files' -- "$tlc" mutant "$work/junk/MiniLock.tla" -c "$work/junk/MiniLock.cfg" \
  --replace $'            /\\ lock = None\n' '' --expect Mutex

# A dead action must be flagged even though every invariant holds.
cp "$ex"/MiniLock.* "$work/"
python3 - "$work/MiniLock.tla" <<'PY'
import sys
p = sys.argv[1]; s = open(p).read()
s = s.replace("Next ==", "Steal(c) == /\\ lock = c /\\ lock # c /\\ UNCHANGED vars\n\nNext ==", 1)
s = s.replace("\\/ Release(c)", "\\/ Release(c) \\/ Steal(c)", 1)
open(p, "w").write(s)
PY
expect 2 'NEVER FIRED' 'dead action flagged as vacuity' -- "$tlc" check "$work/MiniLock.tla" -c "$work/MiniLock.cfg"

# Removing Release deadlocks the system.
# -i.bak, not bare -i: BSD sed (macOS) takes the next argument as the backup suffix.
sed -i.bak 's|^Next == .*|Next == \\E c \\in Clients : Request(c) \\/ Grant(c)|' "$work/MiniLock.tla" && rm -f "$work/MiniLock.tla.bak"
expect 1 'result: deadlock' 'deadlock reported with trace' -- "$tlc" check "$work/MiniLock.tla" -c "$work/MiniLock.cfg"

exit $fail
