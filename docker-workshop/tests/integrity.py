#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[2]
starter = root / 'pi-research-agent-proof'
solution = root / 'pi-research-agent-solution'
lf_only_patterns = [
    '*.sh',
    '*.py',
    '*.ts',
]
required_both = [
    'AGENTS.md',
    '.pi/extensions/workshop-tools.ts',
    '.pi/extensions/harness-guard.ts',
    'harness/HARNESS-POLICY.md',
    'tools/arxiv_search.py',
    'tools/pdf_read.py',
    'tools/rank_papers.py',
    'tools/harness_compare.py',
    'prompts/harnessed-research-agent.md',
    'prompts/unharnessed-research-agent.md',
    'skills/harness-evidence-gate/SKILL.md',
]
required_solution = [
    'outputs/research-brief-unharnessed.md',
    'outputs/research-brief-specialized.md',
    'outputs/harness-report.json',
    'outputs/harness-delta-scorecard.json',
]
for rel in required_both:
    for base in [starter, solution]:
        if not (base / rel).exists():
            print(f'MISSING {base.name}/{rel}')
            sys.exit(1)
for rel in required_solution:
    if not (solution / rel).exists():
        print(f'MISSING solution/{rel}')
        sys.exit(1)
for forbidden in ['outputs/research-brief-generic.md', 'outputs/research-brief-specialized.md', 'outputs/harness-report.json']:
    if (starter / forbidden).exists():
        print(f'STARTER_SHOULD_NOT_INCLUDE {forbidden}')
        sys.exit(1)
for pattern in lf_only_patterns:
    for path in root.rglob(pattern):
        if '.git' in path.parts:
            continue
        if b'\r\n' in path.read_bytes():
            print(f'CRLF_LINE_ENDINGS {path.relative_to(root)}')
            sys.exit(1)
print('INTEGRITY_OK')
