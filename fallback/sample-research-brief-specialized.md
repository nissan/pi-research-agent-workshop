# Research Brief — Specialized Grant Evaluator Run

## Executive summary

A grant-opportunity triage agent is a strong candidate for specialization if it goes beyond generic summarization and encodes grant-evaluator judgment: matched-funding practicality, partner-letter timing, sector-fit evidence, reporting burden, and funding-to-effort ratio. The sellable version is not “find grants”; it is “shortlist grants worth applying for, explain why, and flag execution risk before a consultant wastes time.”

## Key findings

1. **Fact — The workflow repeats across clients.** Consultants regularly check eligibility, deadlines, sector fit, geography, documents, and likelihood of success.
2. **Specialist judgment — Matched funding changes practicality.** If a grant requires matched funding and the client lacks runway, eligibility alone is misleading; practicality should drop.
3. **Specialist judgment — Deadline urgency must include document burden.** A deadline under 10 business days is high risk when partner letters are required.
4. **Specialist judgment — Sector fit needs evidence quality.** Indirect sector relevance should be labelled as weak, even if the opportunity looks attractive.
5. **Specialist judgment — Funding-to-effort ratio matters.** Heavy reporting obligations can make a small grant unattractive.
6. **Recommendation — Productize as a triage-and-shortlist specialist.** The agent should output eligibility certainty, strategic fit, deadline urgency, evidence burden, admin burden, and funding-to-effort ratio.

## Evidence notes

Evidence comes from `sources/source-notes.md` and participant-supplied grant evaluator notes in `sources/example-domain-notes.md`.

## Evidence quality

Medium. The general workflow notes are synthetic, and the evaluator rules are participant-supplied domain heuristics. The specialist logic is stronger than the generic run but still needs validation against real historical grant decisions.

## Risks and uncertainties

- Heuristics may vary by country, grant body, and sector.
- The agent could under-rank strategic long-shot grants that a senior consultant would pursue.
- Source pages may omit hidden eligibility or reporting requirements.
- Human review remains necessary for legal, accounting, and final submission advice.

## Recommended next action

Build a pilot scoring rubric with six dimensions: eligibility certainty, strategic fit, deadline urgency, evidence burden, admin/reporting burden, and funding-to-effort ratio. Test it on 20 past grant opportunities and compare against consultant decisions.

## Open questions

- Which red flags are universal versus firm-specific?
- What minimum evidence is required before recommending “apply”?
- How should the agent price urgent scans versus routine scans?
- What proof bundle would another agent or buyer trust?
