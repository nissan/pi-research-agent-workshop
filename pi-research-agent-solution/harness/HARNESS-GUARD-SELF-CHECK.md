# Harness Guard Self-Check

Use this checklist before publishing the workshop image.

## Guard expectations

- `harness-guard.ts` registers `harness_check_brief`.
- The guard logs to `outputs/traces/harness-events.jsonl`.
- The guard blocks dangerous shell patterns.
- The guard blocks non-arXiv network shell commands.
- The guard blocks write/edit attempts outside `outputs/`, `listing/`, and `harness/` when surfaced through Pi tool events.

## Known limitation

The guard enforces through Pi tool-call events. It is a workshop harness demonstration, not a container sandbox or kernel-level security boundary. Docker still provides the outer isolation layer.

## Teaching line

A production harness layers controls: prompt policy, tool policy, runtime isolation, audit traces, and output validation.
