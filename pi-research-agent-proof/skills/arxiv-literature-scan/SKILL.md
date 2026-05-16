---
name: arxiv-literature-scan
description: Use when a research brief would benefit from recent academic evidence. Identifies keywords, searches arXiv, ranks papers, and records evidence.
---

# arXiv Literature Scan

## Steps

1. Identify 1–3 search keywords from the decision question.
2. Call `arxiv_search` with the best keyword and `max_results` 5.
3. Rank papers by topic match, recency, method relevance, evidence usefulness, and actionability.
4. Call `rank_arxiv_results` with the decision question as criteria; it writes `outputs/arxiv-ranked-results.json`.
5. Use `read_pdf` on the best PDF if available.
6. Label arXiv evidence separately from participant-provided notes.

## Guardrails

- Do not invent citations.
- If arXiv or PDF reading fails, continue with local notes and say evidence is limited.
- Keep claims proportional to abstracts/excerpts read.
