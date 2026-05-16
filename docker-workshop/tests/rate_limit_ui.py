#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "docker-workshop" / "app" / "server.py"


def fetch(url: str, data: bytes | None = None) -> str:
    with urllib.request.urlopen(url, data=data, timeout=10) as response:
        return response.read().decode("utf-8", errors="replace")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "workshop"
        starter = root / "starter"
        fallback = root / "fallback"
        (starter / "outputs").mkdir(parents=True)
        (starter / "prompts").mkdir()
        (starter / "sources" / "domain-packs").mkdir(parents=True)
        fallback.mkdir()
        (root / "app" / "static").mkdir(parents=True)

        (root / "app" / "static" / "style.css").write_text((ROOT / "docker-workshop" / "app" / "static" / "style.css").read_text(), encoding="utf-8")
        (root / "app" / "static" / "htmx.min.js").write_text("/* test htmx */", encoding="utf-8")
        (starter / "HUGGINGFACE-MODEL-SWAP.md").write_text("OpenRouter guide", encoding="utf-8")
        (starter / "prompts" / "unharnessed-research-agent.md").write_text("loose", encoding="utf-8")
        (starter / "prompts" / "harnessed-research-agent.md").write_text("harnessed", encoding="utf-8")
        (fallback / "sample-research-brief-generic.md").write_text("generic fallback", encoding="utf-8")
        (fallback / "sample-research-brief-specialized.md").write_text("specialized fallback", encoding="utf-8")
        (fallback / "sample-delta-notes.md").write_text("delta fallback", encoding="utf-8")

        fake_bin = Path(tmp) / "bin"
        fake_bin.mkdir()
        pi = fake_bin / "pi"
        pi.write_text(
            "#!/usr/bin/env bash\n"
            "test -n \"${OPENROUTER_API_KEY:-}\" || { echo 'missing openrouter key' >&2; exit 3; }\n"
            "test -z \"${ANTHROPIC_API_KEY:-}\" || { echo 'anthropic leaked into openrouter run' >&2; exit 4; }\n"
            "[[ \"${HOME:-}\" == *openrouter-runtime-home ]] || { echo \"unexpected home: ${HOME:-}\" >&2; exit 5; }\n"
            "printf '%s\\n' \"$*\" > \"$HOME/pi-args.txt\"\n"
            "echo '402 insufficient credits: daily request limit reached' >&2\n"
            "exit 1\n",
            encoding="utf-8",
        )
        pi.chmod(0o755)

        env = os.environ.copy()
        env["PATH"] = f"{fake_bin}:{env['PATH']}"
        env["WORKSHOP_ROOT"] = str(root)
        env["WORKSHOP_PORT"] = "18787"
        env["OPENROUTER_API_KEY"] = "test-key-redacted"
        env["ANTHROPIC_API_KEY"] = "should-not-reach-openrouter-run"
        proc = subprocess.Popen([sys.executable, str(APP)], cwd=root, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            for _ in range(30):
                try:
                    home = fetch("http://127.0.0.1:18787/")
                    break
                except Exception:
                    time.sleep(0.2)
            else:
                raise RuntimeError("server did not start")

            assert "run-result-indicator" in home
            assert "Running... this can take a few minutes" in home

            body = urllib.parse.urlencode({"kind": "specialized_alt_swap"}).encode()
            response = fetch("http://127.0.0.1:18787/run", body)
            assert "OpenRouter limit reached" in response
            assert "fallback outputs copied" in response
            assert (starter / "outputs" / "research-brief-generic.md").read_text() == "generic fallback"
            assert (starter / "outputs" / "research-brief-specialized.md").read_text() == "specialized fallback"
            assert (starter / "outputs" / "delta-notes.md").read_text() == "delta fallback"
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

    print("RATE_LIMIT_UI_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
