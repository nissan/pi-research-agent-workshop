#!/usr/bin/env python3
"""List local markdown sources and basic metadata for the Pi research-agent workshop."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
for path in sorted((root / "sources").glob("*.md")):
    text = path.read_text(encoding="utf-8")
    headings = [line.strip() for line in text.splitlines() if line.startswith("#")]
    print(f"{path.relative_to(root)}")
    print(f"  chars: {len(text)}")
    print(f"  headings: {', '.join(headings[:6]) if headings else 'none'}")
