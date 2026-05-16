# Research Agent Harness Policy

This harness turns a loose research assistant into a safer specialist agent.

## Enforced rules

1. **Filesystem boundary** — write outputs only under:
   - `outputs/`
   - `listing/`
   - `harness/`
2. **Network boundary** — workshop research tools may use arXiv only. Non-arXiv curl/wget/fetch requests are blocked.
3. **Evidence boundary** — a specialist brief must separate:
   - participant-provided notes;
   - arXiv abstract/PDF evidence;
   - assumptions.
4. **Output boundary** — before claiming completion, run `harness_check_brief` on the final brief.
5. **Model provenance boundary** — when the agent is run with a non-default model, the final brief must state the provider/model ID and the domain pack used.
6. **Open-model caution boundary** — when using a smaller open Hugging Face model, prefer fewer high-quality sources, label assumptions clearly, and do not overclaim parity with the OpenAI baseline.
7. **Human review boundary** — no legal, medical, financial, grant-eligibility, or investment claims as final advice.

## Why this matters

Prompts ask. Harnesses enforce.

A prompt can request citations, safe file writes, and evidence quality. A harness can block unsafe actions, constrain tools, and produce a machine-checkable report that another agent or buyer can trust.


## Harness change for Hugging Face model swaps

The OpenAI baseline mainly tests evidence quality and output structure. The Hugging Face specialist run adds two extra harness concerns:

- **model provenance:** the report must name the provider and model, for example `huggingface / Qwen/Qwen2.5-7B-Instruct`;
- **specialization provenance:** the report must name the domain pack used, for example `sources/domain-packs/cloud-computing.md`.

This makes the before/after comparison honest: if quality changes, participants can see whether the difference came from the model, the specialization pack, or the harness.
