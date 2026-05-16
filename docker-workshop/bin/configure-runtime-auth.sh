#!/usr/bin/env bash
set -euo pipefail
# Runtime-only helper. It does not write secrets into the image; it only notes env availability.
mkdir -p /workshop/starter/outputs
{
  if [ -n "${OPENAI_API_KEY:-}" ]; then
    echo "OPENAI_API_KEY is present at runtime. Pi can use provider env auth depending on selected provider/model."
  else
    echo "OPENAI_API_KEY not detected. Use Pi /login for the default/OpenAI lane if needed."
  fi

  if [ -n "${ANTHROPIC_API_KEY:-}" ]; then
    echo "ANTHROPIC_API_KEY is present at runtime for Claude-compatible lanes if your Pi provider config supports it."
  fi

  if [ -n "${OPENROUTER_API_KEY:-}" ]; then
    echo "OPENROUTER_API_KEY is present at runtime. Use the OpenRouter lane with --provider openrouter."
    echo "OpenRouter free models may hit minute limits, daily request limits, or 402 insufficient-credit errors; if they do, the web UI falls back to sample outputs."
  else
    echo "OPENROUTER_API_KEY not detected. For the free OpenRouter lane, pass -e OPENROUTER_API_KEY=... at docker run time."
  fi

  echo "If auth takes too long, use fallback outputs and continue the workshop."
} > /workshop/starter/outputs/auth-mode.txt
