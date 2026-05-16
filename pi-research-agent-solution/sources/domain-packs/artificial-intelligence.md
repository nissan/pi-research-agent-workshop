# Domain Pack: Artificial Intelligence Research Specialist

Use this pack when the agent is asked to produce an AI research brief.

## Specialist lens

Focus on whether a technique is deployable, benchmark-grounded, and safe enough for a product team to test. Separate model capability claims from infrastructure, data, and evaluation requirements.

## Useful arXiv query seeds

- `retrieval augmented generation evaluation`
- `agentic AI tool use benchmark`
- `LLM hallucination mitigation citations`
- `small language model domain adaptation`
- `LLM evaluation harness reproducibility`

## Evidence checklist

For every important claim, capture:

1. task or benchmark used;
2. model family and size if stated;
3. baseline compared against;
4. whether code/data is available;
5. limitations or failure modes reported by the authors.

## Synthesis heuristics

- Prefer papers with ablations, error analysis, and reproducible benchmarks.
- Treat leaderboard-only gains as weak until the evaluation setup is clear.
- Flag when a result depends on proprietary training data or closed models.
- Explain product relevance in terms of latency, cost, reliability, and governance.

## Output additions

Add a short section titled **Implementation implication** with:

- smallest experiment the team can run this week;
- required data/eval harness;
- one risk that could invalidate the result.
