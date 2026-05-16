#!/usr/bin/env python3
"""Workshop-safe PDF reader for arXiv PDFs.

Usage:
  python tools/pdf_read.py https://arxiv.org/pdf/2401.00001 --max-pages 3

Writes:
  outputs/pdf-evidence-notes.md
"""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

ALLOWED_HOSTS = {"arxiv.org", "www.arxiv.org"}
MAX_BYTES = 8 * 1024 * 1024


def fetch_pdf(url_or_path: str) -> tuple[Path, str]:
    parsed = urllib.parse.urlparse(url_or_path)
    if parsed.scheme in {"http", "https"}:
        if parsed.netloc not in ALLOWED_HOSTS:
            raise ValueError(f"Blocked non-arXiv host: {parsed.netloc}")
        req = urllib.request.Request(url_or_path, headers={"User-Agent": "redditech-pi-workshop/1.0"})
        with urllib.request.urlopen(req, timeout=25) as resp:
            ctype = resp.headers.get("content-type", "")
            data = resp.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError("PDF too large for workshop reader")
        if b"%PDF" not in data[:2048] and "pdf" not in ctype.lower():
            raise ValueError("URL did not look like a PDF")
        h = hashlib.sha256(data).hexdigest()[:12]
        outdir = Path("outputs/pdfs")
        outdir.mkdir(parents=True, exist_ok=True)
        path = outdir / f"arxiv-{h}.pdf"
        path.write_bytes(data)
        return path, url_or_path
    path = Path(url_or_path)
    if not path.exists():
        raise FileNotFoundError(url_or_path)
    if path.stat().st_size > MAX_BYTES:
        raise ValueError("PDF too large for workshop reader")
    return path, str(path)


def extract_text(pdf: Path, max_pages: int) -> str:
    max_pages = max(1, min(max_pages, 8))
    with tempfile.NamedTemporaryFile(suffix=".txt") as tmp:
        cmd = ["pdftotext", "-f", "1", "-l", str(max_pages), str(pdf), tmp.name]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
            return Path(tmp.name).read_text(encoding="utf-8", errors="replace")
        except FileNotFoundError:
            raise RuntimeError("pdftotext is not installed; install poppler-utils in the Docker image")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("url_or_path")
    ap.add_argument("--max-pages", type=int, default=3)
    ap.add_argument("--out", default="outputs/pdf-evidence-notes.md")
    args = ap.parse_args()
    try:
        pdf, source = fetch_pdf(args.url_or_path)
        text = extract_text(pdf, args.max_pages)
    except Exception as e:
        print(f"PDF read failed: {e}", file=sys.stderr)
        return 2
    excerpt = "\n".join(line.rstrip() for line in text.splitlines() if line.strip())[:12000]
    content = f"""# PDF Evidence Notes

- Source: {source}
- Local file: `{pdf}`
- Pages requested: {max(1, min(args.max_pages, 8))}

## Extracted text excerpt

```text
{excerpt}
```
"""
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")
    print(content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
