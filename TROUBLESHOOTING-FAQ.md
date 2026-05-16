# Troubleshooting FAQ — Pi Research Agent Workshop

_Last updated: 2026-05-14 AEST_

This FAQ is for facilitators, testers, and participants running the Docker workshop image.

## Fast rule: keep the workshop moving

If live auth, model access, network calls, or a live model/tool run fails or shows no visible progress for more than 3–5 minutes, use the fallback outputs:

```bash
# In the web UI
Click "Use fallback sample outputs"
```

Or from the container:

```bash
docker exec -it pi-research-agent-workshop bash
cd /workshop/starter
cp /workshop/fallback/sample-research-brief-generic.md outputs/research-brief-generic.md
cp /workshop/fallback/sample-research-brief-specialized.md outputs/research-brief-specialized.md
cp /workshop/fallback/sample-delta-notes.md outputs/delta-notes.md
```

The learning objective is the agent pattern: prompt + tools + sources + domain pack + harness + provenance. Live model calls are useful, but they are not the whole workshop.

## If a live run appears stuck

**Symptom:** the browser says a run is still going, or the CLI command is waiting with no useful output for several minutes.

**Fix:**
1. Wait up to 3–5 minutes for visible progress.
2. If there is still no progress, stop waiting and use fallback outputs.
3. If `docker ps`, `docker exec`, or the browser endpoint also stops responding, restart Docker Desktop/Engine once.
4. Rerun the same `docker run` command and continue from fallback, compare, harness, or solution.

Treat this as workshop resilience, not participant failure. The learning goal is the specialist-agent pattern, not debugging provider/network stalls.

---


## 1. `Run generic agent` fails even though I passed an alternate provider key

**Likely cause:** `Run generic agent` is the Pi/OpenAI Codex login lane. It does not use OpenRouter.

**Fix:**

- Use **Run generic agent with OpenRouter** if you passed `OPENROUTER_API_KEY`.
- Use **Run generic agent** only if you have registered your OpenAI Codex subscription through Pi `/login`.

CLI equivalent for OpenRouter:

```bash
docker exec -it pi-research-agent-workshop bash
cd /workshop/starter
pi -p \
  --provider openrouter \
  --model z-ai/glm-4.5-air:free \
  "Read inputs/generic-brief-request.md and sources/source-notes.md. Write outputs/research-brief-generic.md. Include provider/model used and limitations."
```

---

## 2. Hugging Face token passes `whoami`, but Pi returns `401 Invalid username or password`

**Likely cause:** `whoami` only proves the token can identify the Hugging Face account. Pi's Hugging Face provider calls the Hugging Face router/inference path, which has different permission requirements.

**Status:** Hugging Face is no longer recommended as the workshop's free participant lane.

**Fix:** Use OpenRouter free models instead:

```bash
export OPENROUTER_API_KEY="sk-or-your-key-here"

docker run --rm -it \
  --name pi-research-agent-workshop \
  -p 8787:8787 \
  -e OPENROUTER_API_KEY="$OPENROUTER_API_KEY" \
  -v pi_workshop_outputs:/workshop/starter/outputs \
  nissan/pi-research-agent-workshop:latest
```

---

## 3. Hugging Face returns `403 insufficient permissions to call Inference Providers`

**Likely cause:** the user's HF account/token lacks Inference Providers access. Tester feedback confirmed this can happen even when the token is valid and includes inference-looking permissions.

**Decision:** Do not use Hugging Face as the beginner/free lane in the live workshop.

**Fix:** Use OpenRouter free models, or use fallback outputs.

---

## 4. OpenRouter free model rate-limits, daily-limits, 402s, or fails

**Likely cause:** OpenRouter `:free` models are request-limited. Official docs describe a 20 requests/minute cap plus daily request caps that improve after buying credits. Accounts with low/negative balance can also see `402 insufficient credits`, including for free models.

**Fix options:**

1. If you are using the web UI, read the result panel. The workshop app detects common 429 rate-limit, daily-limit, and 402 insufficient-credit responses, copies fallback outputs automatically, and links you back to Compare/Traces/Harness.
2. For a group workshop, ask participants to add about **$5 credit** before class if live OpenRouter calls must keep working, or use Pi `/login` if they already have an OpenAI Codex subscription.
3. Wait a few minutes and retry once if you specifically need a live model result.
4. Swap to another Pi-listed OpenRouter free model.
5. Use fallback outputs and continue.

Known Pi-listed OpenRouter free model examples at time of writing:

```text
z-ai/glm-4.5-air:free
qwen/qwen3-next-80b-a3b-instruct:free
meta-llama/llama-3.3-70b-instruct:free
openai/gpt-oss-20b:free
openai/gpt-oss-120b:free
```

CLI model swap example:

```bash
pi -p \
  --provider openrouter \
  --model qwen/qwen3-next-80b-a3b-instruct:free \
  "Rerun the specialist brief with the same inputs and domain pack. Include provider/model used, evidence labels, risks, regressions, and open questions."
```

---

## 5. How do I check whether the token reached the container?

Inside the running container:

```bash
docker exec -it pi-research-agent-workshop bash
printenv | grep -E 'OPENAI_API_KEY|ANTHROPIC_API_KEY|OPENROUTER_API_KEY' | sed 's/=.*/=*** present/'
cat /workshop/starter/outputs/auth-mode.txt
```

Do not print or paste full tokens into chat, screenshots, markdown, or logs.

---

## 6. Browser opens, but health says no auth detected

**Likely cause:** the container was started without the runtime environment variable, or it was started before the variable was exported.

**Fix:** restart the container with the env var:

```bash
docker rm -f pi-research-agent-workshop
export OPENROUTER_API_KEY="sk-or-your-key-here"

docker run --rm -it \
  --name pi-research-agent-workshop \
  -p 8787:8787 \
  -e OPENROUTER_API_KEY="$OPENROUTER_API_KEY" \
  -v pi_workshop_outputs:/workshop/starter/outputs \
  nissan/pi-research-agent-workshop:latest
```

---

## 7. `docker exec` says the container is not running

**Likely cause:** the container exited, or it was started with a different name.

**Check:**

```bash
docker ps -a | grep pi-research-agent-workshop
```

**Fix:** restart with the expected name:

```bash
docker rm -f pi-research-agent-workshop 2>/dev/null || true
docker run --rm -it --name pi-research-agent-workshop -p 8787:8787 \
  -v pi_workshop_home:/home/piuser/.pi \
  -v pi_workshop_outputs:/workshop/starter/outputs \
  nissan/pi-research-agent-workshop:latest
```

---

## 8. Port `8787` is already in use

**Fix option A:** stop the old container:

```bash
docker rm -f pi-research-agent-workshop
```

**Fix option B:** map to a different host port:

```bash
docker run --rm -it \
  --name pi-research-agent-workshop \
  -p 8788:8787 \
  nissan/pi-research-agent-workshop:latest
```

Then open:

```text
http://localhost:8788
```

---

## 9. arXiv/PDF/network tools fail

**Likely cause:** local network restrictions, remote API hiccups, or temporary arXiv/PDF availability issues.

**Fix:** use fallback outputs. The workshop can still teach specialization, harnessing, provenance, and comparison without live network retrieval.

---

## 10. The agent output looks weak or generic

That is expected for the first baseline.

The workshop intentionally compares:

1. generic baseline;
2. specialized agent with tools/sources/domain packs;
3. harnessed output with provenance and policy checks;
4. model-swapped output with explicit provider/model labels.

A weak baseline is useful because it makes the improvement visible.

---

## 11. What should the tester report?

For each lane, record:

- Docker image tag and digest if available;
- credential lane used;
- exact button/CLI command tried;
- HTTP/model/provider error text;
- whether fallback path worked;
- whether expected output files appeared:
  - `outputs/research-brief-generic.md`
  - `outputs/research-brief-specialized.md`
  - `outputs/delta-notes.md`
  - `outputs/harness-report.json`

Do not include secrets in the report.
