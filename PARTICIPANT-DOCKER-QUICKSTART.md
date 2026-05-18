# Participant Docker Quickstart — Pi Research Agent Workshop

## 1. Pull the image

Optional source clone/download:

```bash
git clone https://github.com/nissan/pi-research-agent-workshop.git
cd pi-research-agent-workshop
```

You do not need the source repo to participate if Docker is working; the clone is a fallback for inspecting files, downloading the starter/solution, or running local checks.

```bash
docker pull nissan/pi-research-agent-workshop:latest
```

The public image is built for both Apple Silicon/ARM (`linux/arm64`) and Intel/AMD Windows/Linux (`linux/amd64`). If your machine cannot pull the image, build from the cloned repo instead:

```bash
docker compose -f docker-compose.workshop.yml up -d --build
```

Current verified public digest:

```text
sha256:375f1976d61e11aaad75672e29bbd9fabe088ac0e1b2ca4100fb01aee18792cc
```

Facilitators can also rebuild locally from the cloned repo if needed:

```bash
docker build -f docker-workshop/Dockerfile -t nissan/pi-research-agent-workshop:local .
```

Windows note: this repo includes `.gitattributes` so shell/Python scripts keep Linux line endings when cloned on Windows. If you cloned before that file was present and see errors like `set -o pipefail\\r`, reclone the repo or run:

```bash
git config core.autocrlf false
git rm --cached -r .
git reset --hard
```

## 2. Choose your credential lane

The image does **not** include API keys or provider tokens.

> **OpenRouter free-lane warning:** Tester feedback confirmed HF Inference Providers can return 403 unless the user/account/org has provider access, so OpenRouter is still the recommended no-paid-subscription lane. But OpenRouter `:free` models are request-limited. Official docs describe a 20 requests/minute cap plus daily request caps that improve after buying credits; accounts with low/negative balance can also see `402 insufficient credits`. For a group workshop, assume free-only keys may run out quickly. Add about **$5 credit** before class if you want fewer interruptions, or use fallback outputs.

Choose one primary live-model path before class:

1. **Pi login / OpenAI Codex subscription path** — if you already have an OpenAI Codex subscription, use Pi's `/login` flow inside the container and register that subscription with Pi.
2. **OpenRouter path** — if you do not have a Codex subscription, create an OpenRouter key and add about **$5 credit** before class so the hosted open-model lane is less likely to stop at daily/free limits.
3. **Fallback lane** — if auth/rate limits fail during class, use the sample outputs and keep learning the agent pattern.

Recommended OpenRouter first-pass model:

```text
z-ai/glm-4.5-air:free
```

Recommended later swap model, if available in your OpenRouter provider/account:

```text
qwen/qwen3-next-80b-a3b-instruct:free
```

If the exact second model is unavailable or rate-limited, use another open instruct model exposed by your provider. The learning objective is the **model swap**, not that everyone uses the exact same hosted backend.

## 3. Run the workshop container

### Option A — Pi login with OpenAI Codex subscription

```bash
docker run --rm -it \
  --name pi-research-agent-workshop \
  -p 8787:8787 \
  -v pi_workshop_home:/home/piuser/.pi \
  -v pi_workshop_outputs:/workshop/starter/outputs \
  nissan/pi-research-agent-workshop:latest
```

Use this if you already have an OpenAI Codex subscription. Then authenticate from another terminal if needed:

```bash
docker exec -it pi-research-agent-workshop bash
cd /workshop/starter
pi
```

Inside Pi:

```text
/login
```

### Option B — OpenRouter API key path

Use this if you do not have an OpenAI Codex subscription or prefer a hosted open-model lane. Create a token at:

```text
https://openrouter.ai/settings/keys
```

Add about **$5 credit** before class if you want fewer interruptions from OpenRouter daily/free limits. Then run the container with the token only at runtime:

```bash
export OPENROUTER_API_KEY="sk-or-your-key-here"

docker run --rm -it \
  --name pi-research-agent-workshop \
  -p 8787:8787 \
  -e OPENROUTER_API_KEY="$OPENROUTER_API_KEY" \
  -v pi_workshop_outputs:/workshop/starter/outputs \
  nissan/pi-research-agent-workshop:latest
```

Do **not** reuse pi_workshop_home for the OpenRouter lane if you previously logged into Pi/Claude/OpenAI. That volume can contain saved provider auth from earlier tests. The browser OpenRouter buttons isolate their runtime, but a clean OpenRouter workshop start is simpler and avoids confusing CLI behavior.

If you already tested with stale saved auth and want a clean reset:

~~~bash
docker rm -f pi-research-agent-workshop 2>/dev/null || true
docker volume rm pi_workshop_home 2>/dev/null || true
~~~

Open:

```text
http://localhost:8787
```

## 4. Run the exercise

In the web UI:

1. Run generic agent using your chosen credential lane:
   - **Run generic agent** for the Pi/OpenAI Codex login path.
   - **Run generic agent with OpenRouter** for the OpenRouter key path.
2. Run specialized arXiv/domain-pack agent.
   - Use **Run specialized arXiv agent with OpenRouter** if you started with OPENROUTER_API_KEY.
   - If OpenRouter rate-limits, use fallback outputs and keep moving.
3. View tool traces.
4. Compare outputs.
5. Run the harness lab.
6. In the later model-swap section, change the model and require model/domain-pack provenance.
7. Peek at full solution only if stuck.

### Example prompts to compare

Baseline:

```text
Read AGENTS.md and inputs/generic-brief-request.md. Use sources/source-notes.md. Write outputs/research-brief-generic.md. Include source notes used, limitations, and open questions.
```

Specialized:

```text
Use the arxiv-literature-scan and pdf-evidence-reader skills. Read sources/domain-packs/artificial-intelligence.md. Search arXiv, rank useful papers, read the best PDF if available, then write outputs/research-brief-specialized.md and outputs/delta-notes.md. Include evidence labels, provider/model used, risks, and open questions.
```

Harnessed:

```text
Run the specialist research task under the harness policy. Use only allowed arXiv/evidence tools, write only approved output files, label evidence versus assumptions, run the harness check, and produce outputs/harness-report.json plus a short comparison against the generic baseline.
```

The important comparison is not just output quality. Look for whether the agent used better sources, labelled evidence, recorded provenance, and produced a checkable harness report.

## 5. CLI alternatives

### Pi/OpenAI Codex login lane

```bash
docker exec -it pi-research-agent-workshop bash
cd /workshop/starter
pi -p "Read the project instructions and generate the research brief requested in inputs/generic-brief-request.md. Use sources/source-notes.md. Write the result to outputs/research-brief-generic.md."
```

### OpenRouter first-pass lane

```bash
docker exec -it pi-research-agent-workshop bash
cd /workshop/starter
pi -p \
  --provider openrouter \
  --model z-ai/glm-4.5-air:free \
  "Read the project instructions and generate the research brief requested in inputs/generic-brief-request.md. Use sources/source-notes.md. Write outputs/research-brief-generic.md. Include provider/model used and any limitations."
```

## Troubleshooting

If auth/provider/model calls fail or a live run shows no visible progress, see `TROUBLESHOOTING-FAQ.md`. The current web UI shows a visible `Running...` indicator during live runs. If OpenRouter returns a common 429 rate-limit, daily-limit, or 402 insufficient-credit response, the app shows a clear limit message and copies fallback outputs automatically. The fast rule is: after 3–5 minutes, use fallback outputs and keep the workshop moving. Restart Docker Desktop/Engine only if the browser endpoint or Docker CLI itself stops responding, then rerun the same container command and resume from fallback/solution.

## Safety

- Do not paste private data into the exercise.
- Do not put API keys into files.
- Pass tokens as environment variables or Pi login credentials only.
- Use synthetic examples unless the facilitator explicitly says otherwise.

## Harness lab

The key concept is the harness lab:

1. Open `http://localhost:8787/harness`.
2. Run **loose agent**.
3. Run **harnessed agent**.
4. Open **Compare outputs**.
5. Inspect `outputs/harness-report.json` and `outputs/traces/harness-events.jsonl`.

Remember: prompts ask; harnesses enforce.

## Optional facilitator-provided key

If the facilitator provides a short-lived workshop key, pass it only at runtime:

```bash
docker run --rm -it \
  --name pi-research-agent-workshop \
  -p 8787:8787 \
  -e OPENAI_API_KEY="$WORKSHOP_OPENAI_API_KEY" \
  nissan/pi-research-agent-workshop:latest
```

Never write the key into workshop files.

## Model swap: OpenAI → OpenRouter or OpenRouter → second OpenRouter model

The second half of the lab shows that the specialist architecture is model-portable.

If you started with Pi login and an OpenAI Codex subscription, swap to OpenRouter:

```bash
cd /workshop/starter
pi -p \
  --provider openrouter \
  --model z-ai/glm-4.5-air:free \
  "Read AGENTS.md, inputs/generic-brief-request.md, sources/source-notes.md, and sources/domain-packs/artificial-intelligence.md. Write outputs/research-brief-specialized.md and outputs/delta-notes.md. Include provider/model used, domain pack used, evidence labels, risks, and open questions. Run the harness check before completion."
```

If you started with OpenRouter, keep the same workflow but swap to a second open model, for example:

```bash
cd /workshop/starter
pi -p \
  --provider openrouter \
  --model qwen/qwen3-next-80b-a3b-instruct:free \
  "Rerun the specialist brief with the same inputs and domain pack. Write outputs/research-brief-specialized.md and outputs/delta-notes.md. Compare against the first OpenRouter run. Include provider/model used, domain pack used, evidence labels, risks, regressions, and open questions. Run the harness check before completion."
```

Domain packs available:

- `sources/domain-packs/artificial-intelligence.md`
- `sources/domain-packs/blockchain-development.md`
- `sources/domain-packs/cloud-computing.md`
- `sources/domain-packs/database-development.md`

The harness becomes stricter in the model-swap step: the final brief must name the provider/model and domain pack so the before/after comparison is auditable.

Full guide inside the workspace: `HUGGINGFACE-MODEL-SWAP.md` (legacy filename; now covers the OpenRouter/free-model lane).
