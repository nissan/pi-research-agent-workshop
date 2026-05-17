# Docker Registry Publish Runbook

> Docker Hub namespace note: the active Docker Hub username/namespace is `nissan`, not `redditech`. Use `nissan/pi-research-agent-workshop` for public pushes unless a Redditech org namespace is created later.

## Image

Recommended public image:

```text
nissan/pi-research-agent-workshop:latest
nissan/pi-research-agent-workshop:2026-05-roadshow
```

## Precondition

Nissan must confirm:

1. Registry target: Docker Hub `nissan/*` or GHCR.
2. Login is active locally (`docker login` or `gh auth`/GHCR equivalent).
3. Credential mode for workshop: participant `/login`, short-lived runtime key, or both.

## Build and Push Multi-Arch Image

```bash
cd pi-research-agent-workshop
docker buildx create --name pi-workshop-builder --use 2>/dev/null || docker buildx use pi-workshop-builder
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -f docker-workshop/Dockerfile \
  -t nissan/pi-research-agent-workshop:2026-05-roadshow \
  -t nissan/pi-research-agent-workshop:latest \
  --push \
  .
```

## Verify Published Manifest

Do not announce the public image until both platforms are present:

```bash
docker buildx imagetools inspect nissan/pi-research-agent-workshop:latest
```

Expected platforms:

- `linux/amd64`
- `linux/arm64`

## Local Pre-push Smoke

When doing a local single-platform candidate build before the multi-arch push:

```bash
docker build -f docker-workshop/Dockerfile -t nissan/pi-research-agent-workshop:local .
./docker-workshop/tests/smoke.sh nissan/pi-research-agent-workshop:local
```

## Participant-readiness preflight

Run this before sending participant links and again on the day of the workshop:

```bash
./scripts/workshop-preflight.py --pull
```

The preflight checks:

- participant guide, tester worksheet, and troubleshooting FAQ return HTTP 200
- Docker is installed and can inspect the public image manifest
- optional `--pull` can fetch the public image
- recommended OpenRouter model IDs are still present in OpenRouter's public model list

If any check fails, do not send the participant invitation yet. Republish the broken doc, push/fix the image, or update the OpenRouter model list/defaults first.

## Secret scan

```bash
if grep -RInE 'code=ac_|access_token|refresh_token|id_token|sk-(proj-)?[A-Za-z0-9_-]{20,}' \
  docker-workshop pi-research-agent-proof pi-research-agent-solution fallback *.md; then
  echo 'SECRET_SCAN_FAILED'; exit 1;
fi
```

## GHCR Equivalent, If Selected

```bash
docker tag nissan/pi-research-agent-workshop:2026-05-roadshow ghcr.io/nissan/pi-research-agent-workshop:2026-05-roadshow
docker tag nissan/pi-research-agent-workshop:latest ghcr.io/nissan/pi-research-agent-workshop:latest
docker push ghcr.io/nissan/pi-research-agent-workshop:2026-05-roadshow
docker push ghcr.io/nissan/pi-research-agent-workshop:latest
```

## Post-push clean-machine smoke

```bash
docker pull nissan/pi-research-agent-workshop:latest
docker run --rm -p 8787:8787 nissan/pi-research-agent-workshop:latest
curl http://localhost:8787/health
curl http://localhost:8787/harness
```

## Credential rule

Never bake API keys, OAuth tokens, or Pi auth files into image layers. Runtime-only env vars or participant `/login` only.
