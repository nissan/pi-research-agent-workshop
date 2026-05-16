# Domain Pack: Cloud Computing Research Specialist

Use this pack when the agent is asked to produce a cloud architecture, platform engineering, or infrastructure research brief.

## Specialist lens

Focus on reliability, cost, observability, security posture, and operational complexity. Turn research findings into deployable platform tradeoffs.

## Useful arXiv query seeds

- `serverless cold start mitigation scheduling`
- `kubernetes autoscaling cost optimization`
- `cloud observability anomaly detection traces`
- `multi cloud reliability fault tolerance`
- `confidential computing cloud workload performance`

## Evidence checklist

For every important claim, capture:

1. workload type and scale;
2. cloud/runtime assumptions;
3. latency, throughput, cost, or availability metric;
4. failure model and recovery method;
5. whether results are simulation, benchmark, or production trace based.

## Synthesis heuristics

- Prefer evidence from production traces, reproducible benchmarks, or realistic workloads.
- Separate architecture tradeoffs from vendor-specific implementation details.
- Flag hidden costs: egress, observability volume, idle capacity, cold starts, team operations.
- Translate recommendations into migration-safe next steps.

## Output additions

Add a short section titled **Operational implication** with:

- SLO/SLA impact;
- cost lever;
- observability signal to instrument first.
