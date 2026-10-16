---
name: create-verification-skill
description: Create a project-local skill for launching, driving, and collecting evidence from a real app, CLI, API, or library. Use when asked to create a reusable verification workflow or control skill for a project. Do NOT use for a one-off smoke check or ordinary unit-test writing.
---

# create-verification-skill

Generate a verification workflow another agent can run from a cold start, and execute it before delivery.

## Discover the real path

Read project instructions, run commands, routes or commands, and existing harnesses. Determine the primary user interface, required build and seed steps, authentication, readiness signal, observable effects, and how to isolate instances. Ask only for facts the repository and environment cannot establish.

Reuse a working harness before introducing a new dependency. Suitable choices include browser/CDP automation for web apps, an existing PTY harness for TUIs, direct CLI invocations, HTTP for APIs, and public entry points for libraries. Commands must match this project. Readiness means a user can complete a mapped action, not just that a process or database responds.

Confirm the base builds and starts before encoding its instructions. If that is blocked, report the blocker and keep any generated workflow clearly marked as a draft. Do not silently fix unrelated startup problems or invent missing credentials.

## Generate the project skill

Honor an explicit destination and existing project conventions. Otherwise use `.agents/skills/verify-<app>/SKILL.md`, with matching `name` and a task-specific `description` in YAML frontmatter. Keep tool names and harness configuration appropriate to the current environment. Declare any concrete dependency the next agent needs.

Include these operational sections, with no placeholders:

| Section | What the next agent must be able to do |
|---|---|
| **Launch** | Build and start from the declared initial state, migrate or seed only isolated verification data, observe usable readiness, and record the instance it owns. |
| **Doctor** | Check process/build identity, port ownership, authentication, and readiness without changing the instance. Run this before driving an existing instance or when anything looks wrong. |
| **Drive** | Exercise a real user path with stable selectors, commands, arguments, or API calls. Identify preconditions and completion signals. |
| **Evidence** | Capture the action and resulting state, including important side effects, with expected results grounded in the feature contract. Name a durable evidence location. |
| **Cleanup** | Stop only instances created by this run using recorded ownership. Remove scratch state while preserving evidence. Run cleanup after failed attempts too. |

Include executable helpers only when they remove repeated mechanics; document their invocation. A helper must work from the declared working directory, fail visibly, and preserve evidence through cleanup.

## Map the features

Add `features/README.md` as an index and one short file per selected user journey, starting with a few important ones. Each file names the feature, prerequisites, user entry points, drive steps, expected observable state, and known gaps. Mark the mapped scope so a partial map cannot be read as whole-app coverage.

Cover alternate entry points when they are part of the selected feature's contract. Missing seed data is a failed prerequisite to report, not a reason to weaken the journey. Expected results must come from the requirement or contract, not a snapshot of whatever the app happens to do.

## Execute the generated workflow

Follow its instructions as written: launch, doctor, drive one mapped feature, capture evidence, clean up, and confirm the evidence survives. Fix failures within the authorized scope and rerun the affected path. Record which feature and environment actually passed; unexecuted journeys remain unverified.

A stand-in environment proves only its exercised path. List setup performed by the stand-in that the real target still needs. Without a successful end-to-end run, deliver a draft with the exact blocker rather than claim a working verification skill.

## Boundaries

- Existing session and host policy govern browsers, process supervision, containers, and permissions. Generated instructions preserve those constraints.
- Prefer an isolated instance with task-owned ports, profiles, and data. Reusing a shared instance requires known ownership and non-conflicting access.
- Real user paths can send messages, charge money, or alter shared data. Identify those effects and preserve their approval requirements; use an established test environment where appropriate.
- Verify what a dry-run or test mode skips before relying on it. Mock only at an existing external-system boundary, and label what the mock leaves unproven.
- Creating a reusable skill does not authorize installing it globally, enabling tools, scheduling upkeep, or publishing artifacts.

## Output

Link the generated skill, feature index, and proof artifacts. State the executed journey and environment, cleanup result, dependencies, unverified journeys, and blockers. Keep recurring maintenance optional unless requested.

Adapted from [pstack/create-verification-skill](https://github.com/cursor/plugins/blob/850d7f2e9f5e55dff7eb00a0a479337fe79eb22f/pstack/skills/create-verification-skill/SKILL.md), under the [MIT license](LICENSE.pstack).
