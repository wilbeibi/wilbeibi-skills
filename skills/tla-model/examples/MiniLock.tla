---------------------------- MODULE MiniLock ----------------------------
\* Worked example: every action names the implementation event it models,
\* every property names the requirement it enforces, every fairness term names
\* the mechanism that justifies it. See ../SKILL.md.
EXTENDS FiniteSets, Naturals
CONSTANTS Clients, None
VARIABLES status, lock
vars == <<status, lock>>

Init == /\ status = [c \in Clients |-> "idle"]
        /\ lock = None

\* impl: client calls lock.Acquire(); request enters the wait queue
Request(c) == /\ status[c] = "idle"
              /\ status' = [status EXCEPT ![c] = "want"]
              /\ UNCHANGED lock

\* impl: server grants the free lock to a waiter (one atomic CAS on the owner field)
Grant(c) == /\ status[c] = "want"
            /\ lock = None
            /\ status' = [status EXCEPT ![c] = "crit"]
            /\ lock' = c

\* impl: owner calls lock.Release()
Release(c) == /\ status[c] = "crit"
              /\ lock = c
              /\ status' = [status EXCEPT ![c] = "idle"]
              /\ lock' = None

Next == \E c \in Clients : Request(c) \/ Grant(c) \/ Release(c)

TypeOK == /\ status \in [Clients -> {"idle", "want", "crit"}]
          /\ lock \in Clients \cup {None}

\* R1: at most one client in the critical section
Mutex == Cardinality({c \in Clients : status[c] = "crit"}) <= 1
\* R2: the owner field agrees with who is in the critical section
Consistency == /\ (lock = None) = ({c \in Clients : status[c] = "crit"} = {})
               /\ \A c \in Clients : lock = c => status[c] = "crit"

\* WF Release: owners do not crash holding the lock (crash is out of scope, see brief).
\* SF Grant: the wait queue is FIFO, so a waiter enabled infinitely often is served.
Fairness == \A c \in Clients : WF_vars(Release(c)) /\ SF_vars(Grant(c))
Spec == Init /\ [][Next]_vars /\ Fairness

\* R3: every waiter eventually gets the lock
StarvationFree == \A c \in Clients : status[c] = "want" ~> status[c] = "crit"
=============================================================================
