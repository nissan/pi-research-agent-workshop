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


def wait_for(predicate, timeout: float = 10.0, step: float = 0.2) -> str:
    deadline = time.time() + timeout
    last = ""
    while time.time() < deadline:
        last = predicate()
        if last:
            return last
        time.sleep(step)
    raise RuntimeError("timed out waiting for condition")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "workshop"
        starter = root / "starter"
        fallback = root / "fallback"
        outputs = starter / "outputs"
        (starter / "prompts").mkdir(parents=True)
        (starter / "sources" / "domain-packs").mkdir(parents=True)
        outputs.mkdir(parents=True)
        fallback.mkdir()
        (root / "app" / "static").mkdir(parents=True)
        (root / "traces").mkdir(parents=True)

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
            "if [[ \"$*\" == *openrouter* ]]; then\n"
            "  test -n \"\${OPENROUTER_API_KEY:-}\" || { echo 'missing openrouter key' >&2; exit 3; }\n"
            "fi\n"
            "echo 'starting agent run'\n"
            "sleep 1\n"
            "echo 'reading sources'\n"
            "sleep 1\n"
            "printf 'live generic output' > outputs/research-brief-generic.md\n"
            "printf 'live specialized output' > outputs/research-brief-specialized.md\n"
            "printf 'live delta output' > outputs/delta-notes.md\n"
            "echo 'finished'\n"
            "exit 0\n",
            encoding="utf-8",
        )
        pi.chmod(0o755)

        base_env = os.environ.copy()
        base_env.pop("OPENROUTER_API_KEY", None)
        base_env.pop("OPENAI_API_KEY", None)
        base_env.pop("ANTHROPIC_API_KEY", None)
        base_env["PATH"] = f"{fake_bin}:{base_env['PATH']}"
        base_env["WORKSHOP_ROOT"] = str(root)
        base_env["WORKSHOP_PORT"] = "18787"

        no_key_proc = subprocess.Popen(
            [sys.executable, str(APP)],
            cwd=root,
            env=base_env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            for _ in range(30):
                try:
                    home = fetch("http://127.0.0.1:18787/")
                    break
                except Exception:
                    time.sleep(0.2)
            else:
                raise RuntimeError("server did not start without key")

            assert 'Run generic agent with OpenRouter' in home
            assert 'data-disabled-by-credential="true"' in home
            assert 'disabled' in home
        finally:
            no_key_proc.terminate()
            try:
                no_key_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                no_key_proc.kill()

        key_env = dict(base_env)
        key_env["OPENROUTER_API_KEY"] = "test-key-redacted"
        key_proc = subprocess.Popen(
            [sys.executable, str(APP)],
            cwd=root,
            env=key_env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            for _ in range(30):
                try:
                    home = fetch("http://127.0.0.1:18787/")
                    break
                except Exception:
                    time.sleep(0.2)
            else:
                raise RuntimeError("server did not start with key")

            assert 'lane-highlight' in home

            body = urllib.parse.urlencode({"kind": "specialized_alt"}).encode()
            panel = fetch("http://127.0.0.1:18787/run", body)
            assert 'data-running="true"' in panel
            assert 'Agent running (specialized OpenRouter lane)' in panel

            running_panel = wait_for(
                lambda: fetch("http://127.0.0.1:18787/partial/run-status") if 'reading sources' in fetch("http://127.0.0.1:18787/partial/run-status") else ""
            )
            assert 'reading sources' in running_panel

            done_panel = wait_for(
                lambda: fetch("http://127.0.0.1:18787/partial/run-status") if 'data-running="false"' in fetch("http://127.0.0.1:18787/partial/run-status") else ""
            )
            assert 'specialized OpenRouter lane finished: exit 0' in done_panel

            compare = fetch("http://127.0.0.1:18787/compare")
            assert 'LIVE - OpenRouter z-ai/glm-4.5-air:free' in compare
            assert 'live generic output' in compare
            assert 'live specialized output' in compare

            fallback_panel = fetch("http://127.0.0.1:18787/run", urllib.parse.urlencode({"kind": "fallback"}).encode())
            assert 'Fallback outputs copied' in fallback_panel

            compare_after_fallback = fetch("http://127.0.0.1:18787/compare")
            assert 'FALLBACK SAMPLE' in compare_after_fallback

            harness = fetch("http://127.0.0.1:18787/harness")
            assert 'FALLBACK SAMPLE' in harness
        finally:
            key_proc.terminate()
            try:
                key_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                key_proc.kill()

    print("RATE_LIMIT_UI_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
