#!/usr/bin/env python3
"""Rank arXiv results with a transparent workshop rubric."""
from __future__ import annotations
import argparse, json, re, time
from pathlib import Path


def tokenize(s: str) -> set[str]:
    return {w.lower() for w in re.findall(r"[a-zA-Z][a-zA-Z0-9-]{2,}", s)}


def score(result: dict, criteria: str) -> tuple[int, list[str]]:
    crit = tokenize(criteria)
    hay = tokenize(' '.join([result.get('title',''), result.get('abstract',''), ' '.join(result.get('categories', []))]))
    overlap = sorted(crit & hay)
    recency = 0
    year = 0
    m = re.match(r"(\d{4})", result.get('published',''))
    if m:
        year = int(m.group(1)); recency = max(0, min(5, year - 2019))
    topic = min(10, len(overlap) * 2)
    pdf = 2 if result.get('pdf_url') else 0
    total = topic + recency + pdf
    reasons = []
    if overlap: reasons.append('keyword overlap: ' + ', '.join(overlap[:8]))
    if year: reasons.append(f'published {year}')
    if pdf: reasons.append('PDF available')
    if not reasons: reasons.append('weak rubric match; inspect manually')
    return total, reasons


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--infile', default='outputs/arxiv-results.json')
    ap.add_argument('--criteria', required=True)
    ap.add_argument('--out', default='outputs/arxiv-ranked-results.json')
    args = ap.parse_args()
    payload = json.load(open(args.infile, encoding='utf-8'))
    ranked = []
    for r in payload.get('results', []):
        s, reasons = score(r, args.criteria)
        ranked.append({**r, 'workshop_score': s, 'ranking_reasons': reasons})
    ranked.sort(key=lambda r: r['workshop_score'], reverse=True)
    out = {'criteria': args.criteria, 'ranked_at_unix': int(time.time()), 'ranked_results': ranked}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=2), encoding='utf-8')
    print(json.dumps(out, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
