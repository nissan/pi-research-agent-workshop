# Harness Lab Facilitator Script

## Purpose

Make the core thesis visceral:

> A prompt asks the agent to behave. A harness makes behavior inspectable, bounded, and enforceable.

## 15-minute segment

### 0:00–2:00 — Setup the contrast

Say:

> We already built a research agent. Now we’ll turn it into something another operator or agent could trust. That requires a harness.

Open:

```text
http://localhost:8787/harness
```

### 2:00–5:00 — Run loose agent

Click **Run loose agent**.

Point out:

- no extension tools;
- no skills;
- no policy file;
- no harness report;
- output may look plausible but is hard to trust.

### 5:00–10:00 — Run harnessed agent

Click **Run harnessed agent**.

Point out:

- approved tools;
- evidence boundary;
- trace artifacts;
- `harness-report.json`;
- policy enforcement.

### 10:00–13:00 — Show failure demo

Open `harness/failure-demos/README.md` or describe Demo B:

> If the agent tries arbitrary network access, the harness blocks it. For this lab, research network access is arXiv-only.

### 13:00–15:00 — Tie to Reddi Agent Protocol

Say:

> The harness report is a proof artifact. If another agent pays to call this specialist, it needs more than prose. It needs boundaries, traces, and validation.

## Debrief questions

1. Which parts were prompt-level instructions?
2. Which parts were actually enforced?
3. What proof artifact would a buyer trust?
4. What would we add for production: budget caps, retries, auth scopes, evals, telemetry, approvals?


## Stalled-run facilitation rule

If a live auth/model/tool run shows no visible progress for 3–5 minutes, narrate it as a normal reliability branch: switch to fallback outputs and keep the learning flow moving. If Docker CLI or the browser endpoint itself becomes unresponsive, restart Docker Desktop/Engine once, rerun the same workshop container command, and resume from fallback, compare, harness, or solution.
