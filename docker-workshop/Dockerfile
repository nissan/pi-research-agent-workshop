FROM node:24-bookworm-slim

LABEL org.opencontainers.image.title="Pi Research Agent Workshop" \
      org.opencontainers.image.description="Docker-first workshop kit for building and harnessing a Pi research agent" \
      org.opencontainers.image.vendor="Redditech" \
      org.opencontainers.image.source="https://github.com/nissan/redditech-academy" \
      tech.reddi.workshop="prosumer-to-specialist-agents"


ARG PI_PACKAGE=@earendil-works/pi-coding-agent
ARG PI_VERSION=0.74.0

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    bash ca-certificates curl git python3 python3-venv python3-pip ripgrep tini vim-tiny poppler-utils \
  && rm -rf /var/lib/apt/lists/*

RUN npm install -g "${PI_PACKAGE}@${PI_VERSION}" --ignore-scripts && npm cache clean --force

RUN useradd -m -s /bin/bash piuser \
  && mkdir -p /workshop /workshop/outputs /workshop/traces /home/piuser/.pi/agent \
  && chown -R piuser:piuser /workshop /home/piuser

COPY --chown=piuser:piuser docker-workshop/app /workshop/app
COPY --chown=piuser:piuser docker-workshop/bin /workshop/bin
COPY --chown=piuser:piuser pi-research-agent-proof /workshop/starter
COPY --chown=piuser:piuser fallback /workshop/fallback
COPY --chown=piuser:piuser pi-research-agent-solution /workshop/solution

USER piuser
WORKDIR /workshop
ENV HOME=/home/piuser
ENV TERM=xterm-256color
ENV WORKSHOP_PORT=8787

EXPOSE 8787
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["bash", "/workshop/bin/start-workshop.sh"]
