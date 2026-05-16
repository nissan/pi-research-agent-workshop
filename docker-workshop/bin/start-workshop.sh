#!/usr/bin/env bash
set -euo pipefail
mkdir -p /workshop/outputs /workshop/traces /workshop/solution
/workshop/bin/configure-runtime-auth.sh
cat <<MSG

Pi Research Agent Workshop

Open: http://localhost:${WORKSHOP_PORT:-8787}

CLI option from another terminal:
  docker exec -it <container-name> bash
  cd /workshop/starter && pi

MSG
exec python3 /workshop/app/server.py
