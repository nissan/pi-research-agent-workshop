# Run Workshop Locally

## Build and run with Compose

```bash
git clone https://github.com/nissan/pi-research-agent-workshop.git
cd pi-research-agent-workshop
docker compose -f docker-compose.workshop.yml up --build
```

Use this local build path if Docker cannot pull the public image for your CPU architecture. The public Docker Hub image is intended to cover both `linux/amd64` and `linux/arm64`, but a local build is the fastest classroom fallback.

Open:

```text
http://localhost:8787
```

## Open Pi CLI

```bash
docker exec -it pi-research-agent-workshop bash
cd /workshop/starter
pi
```

## Stop

```bash
docker compose -f docker-compose.workshop.yml down
```

## Reset volumes

```bash
docker compose -f docker-compose.workshop.yml down -v
```

## Windows line endings

The repo includes `.gitattributes` to keep scripts as LF when cloned on Windows. If you cloned an older copy and see container errors that include `\\r`, reclone the repo or reset line endings before rebuilding:

```bash
git config core.autocrlf false
git rm --cached -r .
git reset --hard
docker compose -f docker-compose.workshop.yml up -d --build
```
