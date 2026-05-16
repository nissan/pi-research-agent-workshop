# Domain Pack: Blockchain Development Research Specialist

Use this pack when the agent is asked to produce a blockchain or smart-contract engineering brief.

## Specialist lens

Focus on protocol assumptions, security boundaries, developer experience, and operational risk. Avoid price speculation and investment advice.

## Useful arXiv query seeds

- `smart contract vulnerability detection large language models`
- `zero knowledge proof systems developer tooling`
- `account abstraction security usability`
- `blockchain transaction fee mechanism analysis`
- `decentralized identity verifiable credentials agents`

## Evidence checklist

For every important claim, capture:

1. chain/protocol or virtual machine targeted;
2. threat model and adversary assumptions;
3. empirical dataset, audit corpus, or formal proof basis;
4. gas/cost/performance impact if reported;
5. whether the finding applies to production systems or toy contracts only.

## Synthesis heuristics

- Prioritize security analysis, formal verification, and postmortem-backed evidence.
- Treat “trustless” or “decentralized” as claims that need mechanism-level explanation.
- Distinguish L1, L2, application, wallet, and oracle risks.
- Flag regulatory or compliance uncertainty without giving legal advice.

## Output additions

Add a short section titled **Security implication** with:

- the main failure mode;
- the control or harness that would reduce it;
- what a developer should test before mainnet deployment.
