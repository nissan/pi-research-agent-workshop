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
  timeout 20s python3 /workshop/starter/tools/arxiv_search.py "agentic retrieval" --max-results 1 >/tmp/arxiv.json
  python3 /workshop/starter/tools/rank_papers.py --infile /tmp/arxiv.json --criteria "agentic retrieval evidence" --out /tmp/ranked.json >/tmp/rank.json
'

cleanup
docker run -d --name "$CID" -p "${PORT}:8787" "$IMAGE" >/dev/null
sleep 3
curl -fsS "http://localhost:${PORT}/health" >/dev/null
curl -fsS "http://localhost:${PORT}/harness" | grep -q 'Harness Lab'
curl -fsS "http://localhost:${PORT}/" | grep -q 'Requires OpenRouter key: run generic agent'
curl -fsS "http://localhost:${PORT}/" | grep -q 'Requires OpenRouter key: run specialized arXiv agent'
curl -fsS "http://localhost:${PORT}/" | grep -q 'run-result-indicator'
curl -fsS "http://localhost:${PORT}/" | grep -q 'Running... this can take a few minutes'
curl -fsS "http://localhost:${PORT}/openrouter" | grep -q 'z-ai/glm-4.5-air:free'
curl -fsS "http://localhost:${PORT}/openrouter" | grep -q 'qwen/qwen3-next-80b-a3b-instruct:free'
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
