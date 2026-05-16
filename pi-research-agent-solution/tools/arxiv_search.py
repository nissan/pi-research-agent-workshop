#!/usr/bin/env python3
"""Small, workshop-safe arXiv search helper.

Usage:
  python tools/arxiv_search.py "multi agent systems" --max-results 5

Writes:
  outputs/arxiv-results.json
"""
from __future__ import annotations

import argparse
import html
import json
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ARXIV_API = "https://export.arxiv.org/api/query"
NS = {"a": "http://www.w3.org/2005/Atom"}


def text(el, path: str) -> str:
    node = el.find(path, NS)
    return " ".join((node.text or "").split()) if node is not None else ""


def search(query: str, max_results: int = 5, year_from: int | None = None) -> list[dict]:
    max_results = max(1, min(max_results, 10))
    terms = f'all:"{query}"'
    if year_from:
        terms += f" AND submittedDate:[{year_from}01010000 TO 299912312359]"
    params = urllib.parse.urlencode({
        "search_query": terms,
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    })
    url = f"{ARXIV_API}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "redditech-pi-workshop/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = resp.read()
    root = ET.fromstring(data)
    results = []
    for entry in root.findall("a:entry", NS):
        links = entry.findall("a:link", NS)
        pdf_url = ""
        abs_url = ""
        for link in links:
            href = link.attrib.get("href", "")
            title = link.attrib.get("title", "")
            typ = link.attrib.get("type", "")
            if title == "pdf" or typ == "application/pdf":
                pdf_url = href
            if not abs_url and "/abs/" in href:
                abs_url = href
        authors = [text(a, "a:name") for a in entry.findall("a:author", NS)]
        categories = [c.attrib.get("term", "") for c in entry.findall("a:category", NS)]
        results.append({
            "id": text(entry, "a:id"),
            "title": html.unescape(text(entry, "a:title")),
            "authors": authors,
            "published": text(entry, "a:published"),
            "updated": text(entry, "a:updated"),
            "categories": categories,
            "abstract": html.unescape(text(entry, "a:summary")),
            "abstract_url": abs_url,
            "pdf_url": pdf_url,
        })
    return results


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("--max-results", type=int, default=5)
    ap.add_argument("--year-from", type=int)
    ap.add_argument("--out", default="outputs/arxiv-results.json")
    args = ap.parse_args()
    try:
        results = search(args.query, args.max_results, args.year_from)
    except Exception as e:
        print(f"arXiv search failed: {e}", file=sys.stderr)
        return 2
    payload = {
        "query": args.query,
        "year_from": args.year_from,
        "fetched_at_unix": int(time.time()),
        "count": len(results),
        "results": results,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
