# Run Workshop Locally

## Build and run with Compose

```bash
cd projects/redditech-academy/roadshows/prosumer-to-specialist-agents
docker compose -f docker-compose.workshop.yml up --build
```

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
