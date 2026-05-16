# Full Solution — Pi Research Agent Workshop

This is the completed reference implementation for the workshop.

Use it when:

- your auth is not working;
- you want to compare your folder layout;
- you want to see the expected final artifacts;
- you finished early and want to inspect the arXiv/PDF extension path.

Do not copy blindly during the first 20 minutes. Try the starter path first, then peek here if blocked.


## Hugging Face model swap

After the OpenAI baseline works, use `HUGGINGFACE-MODEL-SWAP.md` to rerun the same specialist agent with `--provider huggingface --model Qwen/Qwen2.5-7B-Instruct`.

Use one of the sample domain packs in `sources/domain-packs/`:

- Artificial Intelligence
- Blockchain Development
- Cloud Computing
- Database Development

The harness changes for this run: the final brief must name the provider/model and the domain pack used, and must label arXiv evidence, domain-pack context, and assumptions separately.
