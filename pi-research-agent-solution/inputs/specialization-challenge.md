# Specialization challenge

You now have a generic research agent. Make it yours by adding exactly one specialization layer.

Choose one path:

## Path A — Prompt

Create `inputs/specialist-prompt.md` and define a role lens such as venture analyst, grant evaluator, cybersecurity reviewer, product marketer, or procurement analyst.

## Path B — Custom information

Create `sources/my-domain-notes.md` with experience-based notes, red flags, acronyms, customer objections, or evaluation criteria from your field.

## Path C — Skill

Create `skills/my-specialist-research-skill.md` with a repeatable domain workflow.

## Path D — Tool

Create or edit a small script in `tools/`, then ask Pi to use it. Keep it simple: inventory sources, count keywords, check dates, or summarize CSV rows.

## Path E — Harness customization

Copy `.pi/settings.example.json` to `.pi/settings.json`, change a setting, or add a project convention/checklist that changes how the agent runs.

## Rerun prompt

```text
Rerun the same research task, but include my specialization layer. Write the improved result to outputs/research-brief-specialized.md and write comparison notes to outputs/delta-notes.md.
```

## Reflection

In `outputs/delta-notes.md`, answer:

1. What changed?
2. What became more useful or specific?
3. Who would pay for this?
4. What proof would make another agent trust it?
