# Lab: Free OpenRouter Lane + Model Swap

The original workshop assumed participants could use a Pi-supported OpenAI/Codex login or bring their own OpenAI/Claude-style API access. That is still the strongest baseline, but it should not be the only path.

This version supports a **free OpenRouter lane**:

1. Start the first generic run with a hosted open OpenRouter model.
2. Build the same specialist agent shape: prompt + tools + sources + domain pack + harness.
3. In the later half of the lab, swap to a second model and compare behavior.

The teaching point stays the same: **the agent architecture should be portable, but trust comes from provenance, evidence, and harness checks.**

## Credential choices

### Option A — OpenAI/Claude-style baseline

Use this if you already have a Pi-supported login or API key. It gives a strong first comparison point.

### Option B — OpenRouter baseline

Use this if you do not have OpenAI/Claude API access.

Create an OpenRouter account and token:

```text
https://openrouter.ai/settings/keys
```

Use a read/inference token. Do not paste the token into project files.

> **OpenRouter workshop warning:** OpenRouter `:free` models are request-limited. Official docs describe a 20 requests/minute cap plus daily request caps that improve after buying credits; accounts with low/negative balance can also see `402 insufficient credits`. For a group workshop, recommend adding about **$5 credit** before class if live calls need to keep working.

> Note: OpenRouter model weights may be open, but the hosted Inference API/provider path can still have free-tier limits, cold starts, model availability differences, or rate limits.

## Recommended models

First OpenRouter pass:

```text
z-ai/glm-4.5-air:free
```

Later model-swap pass, if available:

```text
qwen/qwen3-next-80b-a3b-instruct:free
```

If the provider rejects a model ID, choose another open instruct model exposed by your OpenRouter provider/account. Good fallback families: GLM, Kimi, Qwen, DeepSeek, Mistral, or Gemma Instruct where available and license-appropriate.

## 1. Run the Docker workshop with a OpenRouter API key

```bash
export OPENROUTER_API_KEY="sk-or-your-key-here"

docker run --rm -it \
  --name pi-research-agent-workshop \
  -p 8787:8787 \
  -e OPENROUTER_API_KEY="$OPENROUTER_API_KEY" \
  nissan/pi-research-agent-workshop:latest
```

Or, inside the container terminal:

```bash
export OPENROUTER_API_KEY="sk-or-your-key-here"
```

## 2. First pass: generic research agent with OpenRouter

From the project folder:

```bash
cd /workshop/starter

pi -p \
  --provider openrouter \
  --model z-ai/glm-4.5-air:free \
  "Read AGENTS.md and inputs/generic-brief-request.md. Use sources/source-notes.md. Write outputs/research-brief-generic.md. Include provider/model used, source notes used, limitations, and open questions."
```

This is the baseline. It may be less polished than an OpenAI/Claude run, and that is fine: we need something to improve and constrain.

## 3. Specialize with a domain pack

The starter includes four domain packs:

- `sources/domain-packs/artificial-intelligence.md`
- `sources/domain-packs/blockchain-development.md`
- `sources/domain-packs/cloud-computing.md`
- `sources/domain-packs/database-development.md`

Example AI specialist run with the same first OpenRouter model:

```bash
pi -p \
  --provider openrouter \
  --model z-ai/glm-4.5-air:free \
  "Read AGENTS.md, inputs/generic-brief-request.md, sources/source-notes.md, and sources/domain-packs/artificial-intelligence.md. Use the domain pack's evidence checklist and output additions. Search arXiv if needed. Write outputs/research-brief-specialized.md and outputs/delta-notes.md. Include provider/model used, domain pack used, evidence labels, risks, and open questions."
```

## 4. Later half: swap to a second model

Now rerun the specialist with a different model. Keep the task, tools, and domain pack as stable as possible so the comparison is about model behavior.

```bash
pi -p \
  --provider openrouter \
  --model qwen/qwen3-next-80b-a3b-instruct:free \
  "Rerun the specialist brief with the same inputs and the Artificial Intelligence domain pack. Write outputs/research-brief-specialized.md and outputs/delta-notes.md. Compare against the first OpenRouter run. Include provider/model used, domain pack used, evidence labels, improvements, regressions, risks, and open questions. Run the harness check before completion."
```

If you started with OpenAI/Claude instead, this step can simply be OpenAI/Claude → OpenRouter using `z-ai/glm-4.5-air:free`.

## 5. What changes in the harness?

When the model changes, the harness should become **more explicit**, not less.

Add these checks to the research harness run:

1. **Model provenance** — output must state provider and model ID, e.g. `openrouter / z-ai/glm-4.5-air:free`.
2. **Domain-pack provenance** — output must name the domain pack used.
3. **Evidence discipline** — claims must be labelled as arXiv evidence, participant/domain-pack context, or assumption.
4. **Context restraint** — smaller/free-tier models can over-compress or overgeneralize, so the harness should prefer fewer, higher-quality sources.
5. **No capability overclaiming** — the brief should mention that model quality may differ from the stronger baseline and should be reviewed before publication.

This is the teaching point: swapping the LLM is easy; keeping the agent reliable requires a harness that captures model identity, evidence boundaries, and domain-specific checks.

## Suggested participant prompt

```text
I am using the OpenRouter lane for the workshop.

First, run the generic research brief using z-ai/glm-4.5-air:free.
Then specialize it with the Artificial Intelligence domain pack.
Later, rerun the same specialist workflow with a second available open instruct model.

For every output, include:
- provider/model used;
- domain pack used, if any;
- arXiv evidence vs domain-pack context vs assumptions;
- implementation implication;
- open questions for human review.

Write the generic brief to outputs/research-brief-generic.md, the specialist brief to outputs/research-brief-specialized.md, and the before/after comparison to outputs/delta-notes.md.
Before claiming completion, run the harness check.
```
