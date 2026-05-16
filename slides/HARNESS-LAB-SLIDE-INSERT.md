# Slide Insert — Harness Lab

## Slide: Prompts Ask. Harnesses Enforce.

**Prompt-only agent**

- Can sound correct.
- May skip evidence boundaries.
- May use tools inconsistently.
- Produces prose, not proof.

**Harnessed specialist**

- Tool policy constrains actions.
- Evidence gate validates output.
- Trace artifacts show what happened.
- Harness report becomes a trust artifact.

Speaker note:

> This is the moment the agent becomes packageable. A buyer or another agent cannot trust vibes; they need boundaries, traces, and validation.

## Slide: Live Harness Demo

1. Run loose agent.
2. Run harnessed agent.
3. Build scorecard.
4. Compare outputs.
5. Inspect `harness-report.json`.

Speaker note:

> Watch for the difference between a model choosing to behave and a harness making certain behaviors impossible or inspectable.

## Slide: Reddi Agent Protocol Bridge

A specialist listing should include:

- input contract;
- allowed tools;
- evidence policy;
- validation report;
- trace/audit artifact;
- human-review boundaries;
- price/usage assumptions.

Speaker note:

> The harness is part of the product. Without it, this is just a prompt someone hopes will work.
