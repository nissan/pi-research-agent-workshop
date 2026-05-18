# Pi Research Agent Workshop

Hands-on workshop kit for building a Pi.dev research brief specialist agent.

Participants can use the public Docker image as the fastest path, or clone this repo to inspect the workshop files, starter project, solution project, harness, fallback outputs, and facilitator materials.

## Quick Start

```bash
docker pull nissan/pi-research-agent-workshop:latest
docker run --rm -it --name pi-research-agent-workshop -p 8787:8787 nissan/pi-research-agent-workshop:latest
```

The public image is published for both `linux/amd64` and `linux/arm64`. If Docker pull is blocked on a specific participant machine, clone the repo and build locally:

```bash
git clone https://github.com/nissan/pi-research-agent-workshop.git
cd pi-research-agent-workshop
docker compose -f docker-compose.workshop.yml up -d --build
```

Then open:

```text
http://localhost:8787
```

For live model runs, use one of these credential paths:

- Existing OpenAI Codex subscription: run Pi `/login` inside the container.
- OpenRouter: pass `OPENROUTER_API_KEY` at runtime. For a group workshop, add about $5 credit before class to avoid free-tier limits.

## What Is Included

- `pi-research-agent-proof/` - participant starter workspace.
- `pi-research-agent-solution/` - completed reference solution.
- `docker-workshop/` - local workshop UI and Docker image source.
- `fallback/` - sample outputs for rate-limit or credential issues.
- `participant-pack/` - participant checklist and anti-stuck checklist.
- `facilitator/` - instructor guide and harness lab script.
- `scripts/workshop-preflight.py` - preflight checks for public docs, Docker, image pull, and OpenRouter models.

## Core Docs

- [20-minute presentation: Agents and Agent Harnesses](https://floral-vault-pz99.here.now/)
- [Participant workshop guide](https://whole-pellet-8mtw.here.now/)
- [Presentation source](presentation/index.html)
- [Participant Docker Quickstart](PARTICIPANT-DOCKER-QUICKSTART.md)
- [Agent harness reference notes](references/agent-harness-reading-notes.md)
- [Run Workshop Locally](RUN-WORKSHOP-LOCALLY.md)
- [Troubleshooting FAQ](TROUBLESHOOTING-FAQ.md)
- [Public Docker Workshop Design](PUBLIC-DOCKER-WORKSHOP-DESIGN.md)
- [Docker Registry Publish Runbook](DOCKER-REGISTRY-PUBLISH-RUNBOOK.md)

## Verification

From the repo root:

```bash
python3 -m py_compile docker-workshop/app/server.py docker-workshop/tests/integrity.py docker-workshop/tests/rate_limit_ui.py scripts/workshop-preflight.py
python3 docker-workshop/tests/integrity.py
python3 docker-workshop/tests/rate_limit_ui.py
docker buildx imagetools inspect nissan/pi-research-agent-workshop:latest
./scripts/workshop-preflight.py --timeout 20
```

The workshop image is intentionally credential-free. Do not commit API keys, OAuth tokens, Pi auth files, or participant secrets.
