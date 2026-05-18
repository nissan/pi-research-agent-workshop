#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


REPO = Path(__file__).resolve().parents[2]


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def fetch(url: str, data: dict[str, str] | None = None) -> str:
    if data is None:
        with urlopen(url, timeout=10) as response:
            return response.read().decode()
    body = urlencode(data).encode()
    request = Request(url, data=body, method="POST")
    request.add_header("content-type", "application/x-www-form-urlencoded")
    with urlopen(request, timeout=10) as response:
        return response.read().decode()


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        shutil.copytree(REPO / "pi-research-agent-proof", root / "starter")
        shutil.copytree(REPO / "pi-research-agent-solution", root / "solution")
        shutil.copytree(REPO / "fallback", root / "fallback")
        shutil.copytree(REPO / "docker-workshop" / "app", root / "app")
        (root / "starter" / "outputs").mkdir(parents=True, exist_ok=True)
        (root / "traces").mkdir(parents=True, exist_ok=True)

        port = free_port()
        proc = subprocess.Popen(
            ["python3", str(REPO / "docker-workshop" / "app" / "server.py")],
            env={**os.environ, "WORKSHOP_ROOT": str(root), "WORKSHOP_PORT": str(port)},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            base = f"http://127.0.0.1:{port}"
            for _ in range(60):
                try:
                    fetch(base + "/health")
                    break
                except Exception:
                    time.sleep(0.1)
            else:
                raise AssertionError("server did not start")

            assert "Chat Lab" in fetch(base + "/chat")
            assert "Model-only answer" in fetch(base + "/chat", {"mode": "plain", "prompt": "Compare RAG agents"})
            assert "Agent answer with tools available" in fetch(
                base + "/chat", {"mode": "agent", "prompt": "Compare RAG agents"}
            )
            assert "Harnessed agent answer" in fetch(
                base + "/chat", {"mode": "harnessed", "prompt": "Compare RAG agents"}
            )

            history_file = root / "starter" / "outputs" / "chat-lab-history.json"
            report_file = root / "starter" / "outputs" / "chat-harness-report.json"
            assert history_file.exists()
            assert report_file.exists()
            history = json.loads(history_file.read_text())
            assert [item["mode"] for item in history[-3:]] == ["plain", "agent", "harnessed"]
            report = json.loads(report_file.read_text())
            assert report["harness_check_pass"] is True
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        print("CHAT_LAB_OK")


if __name__ == "__main__":
    main()
