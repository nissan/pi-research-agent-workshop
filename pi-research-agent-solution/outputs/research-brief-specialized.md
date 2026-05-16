# Specialized research brief: Grant-evaluator agent for grant-opportunity triage

## 1. Executive summary

**Decision question:** Is grant-opportunity triage repeatable enough to package as a specialist agent that other agents or operators would pay to use?

**Recommendation:** Proceed to a focused pilot for a grant-evaluator specialist, not a broad autonomous grant-advice product. The generic workflow is repeatable, and the grant-evaluator lens improves it by adding practical reject/flag criteria: matched-funding feasibility, deadline execution risk, sector-relevance quality, admin burden, evidence burden, and funding-to-effort ratio. This makes the proposed agent more decision-ready for consultants because it can explain not only whether an opportunity appears eligible, but whether it is practical and worth pursuing.

The opportunity is promising enough to test as a paid Reddi Agent Protocol specialist if the pilot proves measurable time savings, consistent scoring, and strong evidence-quality handling. It should remain a triage and recommendation-support agent with human review for final eligibility, legal, accounting, and client-specific funding strategy decisions.

## 2. Key findings

1. **Fact — The workflow is repeatable and rules-based enough for first-pass automation.** Source notes describe recurring checks across deadline, eligibility, funding amount, sector fit, geography, required documents, and likelihood of success. This supports a structured scoring agent.

2. **Fact — The grant-evaluator specialization adds higher-value judgment criteria.** Participant-supplied domain notes add scoring dimensions for eligibility certainty, strategic fit, deadline urgency, evidence burden, admin/reporting burden, and funding-to-effort ratio.

3. **Recommendation — The specialist should downgrade opportunities that are eligible but impractical.** Participant-supplied grant-evaluator red flags indicate that matched funding without cash runway, short deadlines with partner-letter requirements, indirect sector fit, and heavy reporting obligations should reduce practicality or evidence-quality scores.

4. **Fact — The agent’s proposed outputs match consultant and client pain points.** Source notes say clients want concise recommendations, not link dumps; the candidate agent would produce a shortlist, scores, next actions, document requirements, and a proof bundle.

5. **Assumption — A paid specialist may be viable if it proves time savings and consistency.** The source notes state a monetization hypothesis of saving consultants 1–3 hours per client scan and improving consistency. This is plausible but not validated by customer interviews, usage data, or pricing tests.

6. **Recommendation — Package trust artifacts as core functionality.** Because grant criteria can change and public pages may be incomplete, the specialist should include source list, timestamp, rubric, evidence-quality labels, and output hash in every result.

## 3. Evidence notes

- **Workflow evidence:** Consultants manually scan grant portals, newsletters, incubator announcements, and government sites.
- **Repeatability evidence:** The team often repeats the same first-pass triage across similar clients.
- **Pain-point evidence:** Manual tracking can miss deadlines; eligibility details are easy to misread; irrelevant opportunities waste consultant time; junior staff struggle to judge strategic fit.
- **Candidate value evidence:** The proposed agent accepts a company profile and opportunity list, scores each opportunity, produces a shortlist, identifies next actions and document requirements, and creates a proof bundle.
- **Specialist judgment evidence:** Participant-supplied grant-evaluator notes identify red flags around matched funding, tight deadlines with partner letters, indirect sector relevance, and heavy reporting obligations.
- **Evidence quality:** The sources are synthetic classroom-safe notes plus participant-supplied example domain notes. They are adequate for a product-design hypothesis, but weak for market-size, pricing, legal, accounting, or actual buyer-demand claims.

## 4. Risks and uncertainties

- **Changing requirements:** Grant criteria can change after triage, so outputs need timestamps and recheck prompts.
- **Incomplete public sources:** Public grant pages may omit details that affect eligibility or reporting burden.
- **False precision:** Numeric scores could imply certainty where evidence is weak, especially for sector fit or eligibility interpretation.
- **Human review dependency:** Legal/accounting claims, final eligibility calls, and funding-strategy advice require human review.
- **Unvalidated willingness to pay:** The 1–3 hour savings hypothesis is not yet proven with real users or buyer behavior.
- **Specialist boundary risk:** The agent must not overclaim as a grant evaluator making final award-probability judgments; it should present triage rationale and practical risk flags.

## 5. Recommended next action

Run a pilot using 10–20 representative grant opportunities and 3–5 company profiles. Compare the specialist against the current manual process on time saved, shortlist quality, missed red flags, evidence-quality labeling, and senior-consultant acceptance. Use the grant-evaluator rubric as the pilot scoring model, especially eligibility certainty, deadline urgency, evidence burden, admin burden, and funding-to-effort ratio.

If the pilot demonstrates consistent 1–3 hour savings per scan and senior consultants trust the shortlist, prepare a limited paid Reddi Agent Protocol specialist listing positioned as **grant-opportunity triage with evaluator-style practicality flags**, not as final grant advice.

## 6. Open questions

1. How often do target consultants perform grant scans, and how much time do they currently spend?
2. Which grant types most often create matched-funding, partner-letter, or reporting-burden problems?
3. What minimum evidence-quality threshold should trigger human recheck before recommending pursuit?
4. What output format would other agents or operators pay to consume: ranked JSON, brief memo, proof bundle, or all three?
5. What price is justified if the agent reliably saves 1–3 hours per scan?
6. Who is the first paying user: boutique consultants, startup operators, incubators, or other research agents?
