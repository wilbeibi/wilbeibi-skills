#!/usr/bin/env bash
# Self-test for tlc.py against examples/MiniLock. Parser cases need only uv; the rest need java
# and tla2tools.jar (see tlc.py) and print SKIP when either is missing. Exits 1 on any FAIL.
set -uo pipefail

here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
tlc="$here/tlc.py"
ex="$here/../examples"
work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT

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

# Parser checks need no java. A zero exit without TLC's verdict (truncated output, a broken java
# wrapper) is not clean; coverage repeats every minute on long runs, and only the last report counts.
parse() { uv run -q --no-project --python '>=3.10' python -c \
  "import runpy, sys; p = runpy.run_path(sys.argv[1])['parse']; out = sys.argv[2]; $1" "$tlc" "$2"; }
cov='@!@!@STARTMSG 2772:0 @!@!@\n<A line 3, col 1 to line 4, col 2 of module M>: %s\n@!@!@ENDMSG 2772 @!@!@\n'
expect 0 '^incomplete$' 'zero exit without a verdict is incomplete' -- parse "print(p(out, 0)['kind'])" ''
expect 0 "^\{\('A', 3\): \(5, 9\)\}$" 'repeated coverage keeps the last report' -- \
  parse "print(p(out, 0)['coverage'])" "$(printf "$cov" 0:0 5:9)"

if ! "$tlc" check "$ex/MiniLock.tla" -c "$ex/MiniLock.cfg" >"$work/out" 2>&1; then
  if grep -qE 'java not found|tla2tools.jar not found' "$work/out"; then
    echo "SKIP: $(cat "$work/out")"; exit $fail
  fi
fi

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

# TLC stops at Mutex, listed first, so Consistency was never checked on every state.
expect 2 'INCONCLUSIVE' 'mutant stopped by another invariant is inconclusive' -- "$tlc" mutant "$ex/MiniLock.tla" -c "$ex/MiniLock.cfg" \
  --replace $'            /\\ lock = None\n' '' --expect Consistency

# An MC wrapper runs the base module, so the edit lands in MiniLock.tla; the cfg sits in models/.
mkdir -p "$work/mc/models"; cp "$ex/MiniLock.tla" "$work/mc/"; cp "$ex/MiniLock.cfg" "$work/mc/models/MC.cfg"
printf -- '---- MODULE MCMiniLock ----\nEXTENDS MiniLock\n====\n' >"$work/mc/MCMiniLock.tla"
expect 0 'KILLED' 'mutant edits the base module of an MC wrapper' -- "$tlc" mutant "$work/mc/MCMiniLock.tla" \
  -c "$work/mc/models/MC.cfg" --replace $'            /\\ lock = None\n' '' --expect Mutex
# A sibling the root never loads must not take the edit, or the mutant "survives" unchanged.
printf -- '---- MODULE Other ----\nOtherGuard == TRUE\n====\n' >"$work/mc/Other.tla"
expect 3 'matched nowhere \(also in Other.tla, which it does not load\)' 'mutant ignores modules the root does not load' -- \
  "$tlc" mutant "$work/mc/MCMiniLock.tla" -c "$work/mc/models/MC.cfg" --replace 'OtherGuard == TRUE' 'OtherGuard == FALSE' --expect Mutex

# Simulation explores random behaviors, so its clean result must not read as exhaustive.
expect 0 'result: clean \(simulation, not exhaustive\)' 'simulation is not reported as exhaustive' -- \
  "$tlc" check "$ex/MiniLock.tla" -c "$ex/MiniLock.cfg" --tlc-args -simulate num=50 -depth 20

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

# A cfg may declare an action off on purpose; a declared action that fires, or does not exist, is flagged.
off() { { printf '\\* disabled: %s\n' "$1"; cat "$work/MiniLock.cfg"; } >"$work/Off.cfg"; }
off 'Steal'
expect 0 'Steal .*\(disabled in cfg\)' 'declared disabled action accepted' -- "$tlc" check "$work/MiniLock.tla" -c "$work/Off.cfg"
off 'Steal, Release'
expect 2 'declares disabled, but these fired: Release' 'declared action that fires is flagged' -- \
  "$tlc" check "$work/MiniLock.tla" -c "$work/Off.cfg"
off 'Steal Stael'
expect 2 'declares disabled, but no such action: Stael' 'misspelled disabled action is flagged' -- \
  "$tlc" check "$work/MiniLock.tla" -c "$work/Off.cfg"

# Removing Release deadlocks the system.
# -i.bak, not bare -i: BSD sed (macOS) takes the next argument as the backup suffix.
sed -i.bak 's|^Next == .*|Next == \\E c \\in Clients : Request(c) \\/ Grant(c)|' "$work/MiniLock.tla" && rm -f "$work/MiniLock.tla.bak"
expect 1 'result: deadlock' 'deadlock reported with trace' -- "$tlc" check "$work/MiniLock.tla" -c "$work/MiniLock.cfg"

# A spec that already fails its cfg cannot show that a mutant is caught.
expect 3 'BASELINE NOT CLEAN' 'mutant refuses a failing baseline' -- "$tlc" mutant "$work/MiniLock.tla" -c "$work/MiniLock.cfg" \
  --replace $'            /\\ lock = None\n' '' --expect Mutex

exit $fail
