#!/usr/bin/env python3
"""Compare loose vs harnessed workshop outputs and produce a simple proof scorecard."""
from __future__ import annotations
import json, re, time
from pathlib import Path

LOOSE = Path('outputs/research-brief-unharnessed.md')
HARNESSED = Path('outputs/research-brief-specialized.md')
REPORT = Path('outputs/harness-report.json')
OUT = Path('outputs/harness-delta-scorecard.json')

SIGNALS = {
    'mentions_arxiv_or_pdf': r'arxiv|pdf|paper|abstract',
    'labels_assumptions': r'assumption|participant-supplied|source notes',
    'has_human_review_boundary': r'human review|not final advice|legal|financial|eligibility',
    'mentions_evidence_quality': r'evidence quality|weak evidence|limitations|uncertain|confidence',
    'has_next_action': r'next action|recommend|pilot|should',
}


def read(p: Path) -> str:
    return p.read_text(encoding='utf-8') if p.exists() else ''


def score(text: str) -> dict:
    return {name: bool(re.search(pattern, text, re.I)) for name, pattern in SIGNALS.items()}


def main() -> int:
    loose = read(LOOSE)
    harnessed = read(HARNESSED)
    harness_report = json.loads(read(REPORT) or '{}')
    loose_score = score(loose)
    harnessed_score = score(harnessed)
    payload = {
        'generated_at_unix': int(time.time()),
        'loose_path': str(LOOSE),
        'harnessed_path': str(HARNESSED),
        'harness_report_path': str(REPORT),
        'loose_signals': loose_score,
        'harnessed_signals': harnessed_score,
        'loose_signal_count': sum(loose_score.values()),
        'harnessed_signal_count': sum(harnessed_score.values()),
        'harness_check_pass': harness_report.get('pass'),
        'thesis': 'Prompts ask; harnesses enforce tool boundaries, evidence gates, traceability, and output validation.',
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    print(json.dumps(payload, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
