---
name: harness-evidence-gate
description: Use before finalizing a workshop research brief. Enforces evidence labels, risk boundaries, and harness validation.
---

# Harness Evidence Gate

Before finalizing a specialized research brief:

1. Read `harness/HARNESS-POLICY.md`.
2. Confirm the brief separates participant notes, arXiv/PDF evidence, and assumptions.
3. Confirm risky advice is bounded as human-review-required.
4. Call `harness_check_brief` with `outputs/research-brief-specialized.md`.
5. If the harness report fails, revise the brief and run the check again.

The lab thesis is: prompts ask, harnesses enforce.
