# Domain Pack: Database Development Research Specialist

Use this pack when the agent is asked to produce a database systems, data infrastructure, or storage-engine research brief.

## Specialist lens

Focus on workload fit, correctness, latency/throughput tradeoffs, operational ergonomics, and data integrity. Explain which assumptions must hold before adopting a technique.

## Useful arXiv query seeds

- `vector database indexing approximate nearest neighbor benchmark`
- `learned indexes database systems evaluation`
- `transaction processing concurrency control performance`
- `database query optimization machine learning cardinality estimation`
- `distributed database consistency latency tradeoff`

## Evidence checklist

For every important claim, capture:

1. workload shape: OLTP, OLAP, vector search, streaming, mixed;
2. dataset size and skew;
3. consistency/isolation guarantees;
4. latency, throughput, storage, or memory metric;
5. comparison baseline and tuning assumptions.

## Synthesis heuristics

- Treat microbenchmark wins cautiously unless workload shape matches the target use case.
- Separate correctness guarantees from performance optimizations.
- Flag operational burden: compaction, reindexing, backups, migrations, hot partitions.
- Identify when “faster” sacrifices recall, consistency, or maintainability.

## Output additions

Add a short section titled **Data architecture implication** with:

- best-fit workload;
- correctness risk;
- benchmark the team should run before adoption.
