# Harnessed Research Agent Prompt

Use the workshop harness.

Steps:

1. Read `harness/HARNESS-POLICY.md`.
2. Read `inputs/generic-brief-request.md`, `sources/source-notes.md`, and relevant skills.
3. If the run is a specialist/domain run, read exactly one relevant file under `sources/domain-packs/`.
4. Identify a research keyword.
5. Use `arxiv_search`.
6. Use `rank_arxiv_results`.
7. Use `read_pdf` if a PDF URL is available.
8. Write `outputs/research-brief-specialized.md`.
9. In the final brief, include:
   - provider/model used, such as `openai / gpt-5.5` or `huggingface / Qwen/Qwen2.5-7B-Instruct`;
   - domain pack used, or `none` for the generic baseline;
   - arXiv evidence vs domain-pack context vs assumptions.
10. Write `outputs/delta-notes.md`, explicitly comparing unharnessed vs harnessed behavior.
11. Run `harness_check_brief` on `outputs/research-brief-specialized.md`.
12. If the harness report fails, revise and rerun the check.

The point is to show that the harness changes agent behavior: safer tool use, better evidence boundaries, model provenance, specialization provenance, and machine-checkable proof.
