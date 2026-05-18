#!/usr/bin/env bash
set -euo pipefail
IMAGE="${1:-nissan/pi-research-agent-workshop:local}"
CID="pi-workshop-test-$RANDOM"
PORT=$((18000 + RANDOM % 1000))
STARTER_VOL="pi-workshop-starter-$RANDOM"
TRACES_VOL="pi-workshop-traces-$RANDOM"
cleanup() {
  docker rm -f "$CID" >/dev/null 2>&1 || true
  docker volume rm "$STARTER_VOL" "$TRACES_VOL" >/dev/null 2>&1 || true
}
trap cleanup EXIT

docker run --rm "$IMAGE" bash -lc '
  set -euo pipefail
  pi --version >/dev/null
  test -f /workshop/starter/.pi/extensions/workshop-tools.ts
  test -f /workshop/starter/.pi/extensions/harness-guard.ts
  test -f /workshop/starter/harness/HARNESS-POLICY.md
  test -f /workshop/starter/prompts/harnessed-research-agent.md
  test -f /workshop/starter/harness/HARNESS-GUARD-SELF-CHECK.md
  test -f /workshop/starter/HUGGINGFACE-MODEL-SWAP.md
  test -f /workshop/starter/sources/domain-packs/artificial-intelligence.md
  test -f /workshop/starter/sources/domain-packs/blockchain-development.md
  test -f /workshop/starter/sources/domain-packs/cloud-computing.md
  test -f /workshop/starter/sources/domain-packs/database-development.md
  grep -q "z-ai/glm-4.5-air:free" /workshop/starter/HUGGINGFACE-MODEL-SWAP.md
  grep -q "qwen/qwen3-next-80b-a3b-instruct:free" /workshop/starter/HUGGINGFACE-MODEL-SWAP.md
  grep -q "hasModelProvenance" /workshop/starter/.pi/extensions/harness-guard.ts
  test ! -f /workshop/starter/outputs/research-brief-generic.md
  test -f /workshop/starter/outputs/sample-research-brief-generic.md
  test -f /workshop/solution/outputs/harness-report.json
  ok=0
  for i in 1 2 3; do
    if timeout 20s python3 /workshop/starter/tools/arxiv_search.py "agentic retrieval" --max-results 1 >/tmp/arxiv.json; then
      ok=1
      break
    fi
    sleep 2
  done
  if [ "$ok" -eq 1 ]; then
    python3 /workshop/starter/tools/rank_papers.py --infile /tmp/arxiv.json --criteria "agentic retrieval evidence" --out /tmp/ranked.json >/tmp/rank.json
  else
    echo "ARXIV_SMOKE_SKIPPED: arXiv API unavailable or rate limited"
  fi
'

cleanup
docker run -d --name "$CID" -p "${PORT}:8787" "$IMAGE" >/dev/null
sleep 3
curl -fsS "http://localhost:${PORT}/health" >/dev/null
curl -fsS "http://localhost:${PORT}/harness" | grep -q 'Harness Lab'
curl -fsS "http://localhost:${PORT}/" | grep -q 'Run generic agent with OpenRouter'
curl -fsS "http://localhost:${PORT}/" | grep -q 'Run specialized arXiv agent with OpenRouter'
curl -fsS "http://localhost:${PORT}/" | grep -q 'data-running="false"'
curl -fsS "http://localhost:${PORT}/" | grep -q 'No run started yet'
curl -fsS "http://localhost:${PORT}/" | grep -q 'data-disabled-by-credential="true"'
curl -fsS "http://localhost:${PORT}/openrouter" | grep -q 'z-ai/glm-4.5-air:free'
curl -fsS "http://localhost:${PORT}/openrouter" | grep -q 'qwen/qwen3-next-80b-a3b-instruct:free'
curl -fsS "http://localhost:${PORT}/chat" | grep -q 'Chat Lab'
curl -fsS -X POST -d 'mode=plain&prompt=Compare+agent+modes' "http://localhost:${PORT}/chat" | grep -q 'Model-only answer'
curl -fsS -X POST -d 'mode=agent&prompt=Compare+agent+modes' "http://localhost:${PORT}/chat" | grep -q 'Agent answer with tools available'
curl -fsS -X POST -d 'mode=harnessed&prompt=Compare+agent+modes' "http://localhost:${PORT}/chat" | grep -q 'Harnessed agent answer'
curl -fsS -X POST -d 'action=all&mode=plain&prompt=Compare+agent+modes' "http://localhost:${PORT}/chat" | grep -q 'Harnessed agent answer'
curl -fsS "http://localhost:${PORT}/chat-transcript" | grep -q 'Chat Lab Transcript'
curl -fsS -X POST "http://localhost:${PORT}/chat-clear" | grep -q 'No chat turns yet'
docker exec "$CID" bash -lc 'test -f /workshop/starter/outputs/chat-lab-history.json && test -f /workshop/starter/outputs/chat-harness-report.json && test ! -f /workshop/starter/outputs/chat-lab-transcript.md'
curl -fsS "http://localhost:${PORT}/solution" | grep -q 'Full solution folder'
curl -fsS "http://localhost:${PORT}/static/htmx.min.js" >/dev/null
curl -fsS "http://localhost:${PORT}/compare" | grep -q 'Harness report'
docker rm -f "$CID" >/dev/null

docker run -d --name "$CID" -p "${PORT}:8787" \
  -v "${STARTER_VOL}:/workshop/starter" \
  -v "${TRACES_VOL}:/workshop/traces" \
  "$IMAGE" >/dev/null
sleep 3
curl -fsS "http://localhost:${PORT}/health" >/dev/null
curl -fsS -X POST -d 'kind=harness_compare' "http://localhost:${PORT}/run" | grep -q 'Harness scorecard finished: exit 0'
docker exec "$CID" bash -lc 'test -f /workshop/traces/*-harness-compare.log'
curl -fsS -X POST "http://localhost:${PORT}/copy-solution" | grep -q 'Solution copied'
docker rm -f "$CID" >/dev/null

echo "SMOKE_OK $IMAGE"
