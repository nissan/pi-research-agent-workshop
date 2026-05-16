# Facilitator Guide — Build Your First Specialist Agent

## Primary promise

Participants leave with a local specialist-agent proof point and a concrete mental model for monetizing expertise through Reddi Agent Protocol.

## Run-of-show

1. Opening hook — 5 min
2. Agent anatomy examples — 15 min
3. Harness and telemetry lessons — 10 min
4. Pi setup and generic run — 10 min
5. Specialization challenge — 20 min
6. Monetization bridge — 10 min
7. Share-out and close — 5–10 min

## Facilitation principles

- Do not let setup eat the workshop. Use the fallback screenshots/starter outputs if Pi install fails.
- Keep specialization to exactly one layer. Depth beats breadth.
- Push every participant to name a buyer. “Useful to me” is not yet a marketplace service.
- Treat private expertise as the value source, but warn against pasting confidential data.
- Keep the Reddi Agent Protocol bridge practical: input, output, price, proof, reputation.

## Instructor demo commands

```bash
cd pi-research-agent-proof
python3 tools/collect_local_sources.py
pi
```

Baseline prompt:

```text
Read the project instructions and generate the research brief requested in inputs/generic-brief-request.md. Use sources/source-notes.md. Write the result to outputs/research-brief-generic.md.
```

Specialized rerun prompt:

```text
Use sources/example-domain-notes.md as a grant-evaluator specialization. Rerun the same research task, write outputs/research-brief-specialized.md, and write outputs/delta-notes.md explaining what improved and whether this could become a paid Reddi Agent Protocol specialist.
```

## Reliability layer after loops 11–20

Use these supporting files before running the workshop live:

- `scripts/workshop-preflight.py` — run before sending participant links and again before the session.
- `rehearsal/TIMED-REHEARSAL-PLAN.md` — 30-minute timing script.
- `fallback/INSTALL-AUTH-FALLBACK.md` — what to do if Pi/npm/auth fails.
- `fallback/sample-research-brief-generic.md` — generic output fallback.
- `fallback/sample-research-brief-specialized.md` — specialized output fallback.
- `fallback/sample-delta-notes.md` — comparison fallback.
- `conversion/MONETIZATION-RUBRIC.md` — score whether a specialist is sellable.
- `conversion/REDdi-PROTOCOL-BRIDGE-SCRIPT.md` — concise bridge into Reddi Agent Protocol.
- `risk-register/WORKSHOP-RISK-REGISTER.md` — known risks and mitigations.

Facilitator rule: preserve the learning arc. If setup breaks or a live model run shows no progress after 3-5 minutes, switch to fallback artifacts and keep participants moving. Restart Docker only if the UI or Docker CLI itself stops responding.
