#!/usr/bin/env python3
"""Preflight checks for the Pi Research Agent workshop.

This is intentionally dependency-free so a facilitator can run it from a clean
machine before sending participant links or starting a live session.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass


DEFAULT_DOCS = {
    "participant_guide": "https://quaint-pillar-vmbr.here.now/",
    "tester_worksheet": "https://mighty-nimbus-73bm.here.now/",
    "troubleshooting_faq": "https://alpine-delta-hrex.here.now/",
}
DEFAULT_IMAGE = "nissan/pi-research-agent-workshop:latest"
DEFAULT_MODELS = [
    "z-ai/glm-4.5-air:free",
    "qwen/qwen3-next-80b-a3b-instruct:free",
]


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


def fetch(url: str, timeout: int, max_bytes: int | None = 300) -> tuple[int, str]:
    request = urllib.request.Request(
        url,
        headers={
            "user-agent": "redditech-workshop-preflight/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body_bytes = response.read(max_bytes) if max_bytes is not None else response.read()
        body = body_bytes.decode("utf-8", errors="replace")
        return response.status, body


def check_url(name: str, url: str, timeout: int) -> CheckResult:
    try:
        status, body = fetch(url, timeout)
    except urllib.error.HTTPError as exc:
        body = exc.read(120).decode("utf-8", errors="replace")
        return CheckResult(name, False, f"HTTP {exc.code} from {url}: {body.strip()!r}")
    except Exception as exc:  # noqa: BLE001 - report exact preflight failure
        return CheckResult(name, False, f"{url}: {exc}")

    if status != 200:
        return CheckResult(name, False, f"HTTP {status} from {url}: {body.strip()!r}")
    return CheckResult(name, True, f"HTTP 200 from {url}")


def run_command(name: str, command: list[str], timeout: int) -> CheckResult:
    try:
        completed = subprocess.run(
            command,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return CheckResult(name, False, f"timed out after {timeout}s: {' '.join(command)}")
    except Exception as exc:  # noqa: BLE001 - report exact preflight failure
        return CheckResult(name, False, str(exc))

    output = (completed.stdout or "").strip()
    if completed.returncode != 0:
        return CheckResult(name, False, output[-700:] or f"exit {completed.returncode}")
    return CheckResult(name, True, output.splitlines()[-1] if output else "ok")


def check_docker_installed() -> CheckResult:
    docker = shutil.which("docker")
    if not docker:
        return CheckResult("docker_binary", False, "docker not found on PATH")
    return run_command("docker_binary", [docker, "--version"], 15)


def check_docker_image(image: str, timeout: int, pull: bool) -> list[CheckResult]:
    docker = shutil.which("docker") or "docker"
    results = [
        run_command("docker_manifest", [docker, "manifest", "inspect", image], timeout),
    ]
    if pull:
        results.append(run_command("docker_pull", [docker, "pull", image], timeout))
    return results


def check_openrouter_models(models: list[str], timeout: int) -> CheckResult:
    try:
        status, body = fetch("https://openrouter.ai/api/v1/models", timeout, max_bytes=None)
    except Exception as exc:  # noqa: BLE001 - report exact preflight failure
        return CheckResult("openrouter_models", False, f"could not fetch model list: {exc}")

    if status != 200:
        return CheckResult("openrouter_models", False, f"HTTP {status} from OpenRouter model list")

    try:
        payload = json.loads(body)
    except Exception as exc:  # noqa: BLE001
        return CheckResult("openrouter_models", False, f"could not parse model list: {exc}")

    available = {item.get("id") for item in payload.get("data", []) if isinstance(item, dict)}
    missing = [model for model in models if model not in available]
    if missing:
        return CheckResult(
            "openrouter_models",
            False,
            f"missing model IDs: {', '.join(missing)}",
        )
    return CheckResult("openrouter_models", True, f"available: {', '.join(models)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run workshop readiness checks.")
    parser.add_argument("--image", default=DEFAULT_IMAGE, help="Docker image tag to inspect.")
    parser.add_argument(
        "--doc",
        action="append",
        default=[],
        metavar="NAME=URL",
        help="Override/add a participant doc URL check. Can be repeated.",
    )
    parser.add_argument(
        "--model",
        action="append",
        default=[],
        help="OpenRouter model ID to require. Can be repeated.",
    )
    parser.add_argument("--timeout", type=int, default=30, help="Per-check timeout in seconds.")
    parser.add_argument("--pull", action="store_true", help="Also docker pull the public image.")
    parser.add_argument(
        "--skip-openrouter",
        action="store_true",
        help="Skip OpenRouter public model-list availability check.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    docs = dict(DEFAULT_DOCS)
    for item in args.doc:
        if "=" not in item:
            print(f"Invalid --doc value, expected NAME=URL: {item}", file=sys.stderr)
            return 2
        name, url = item.split("=", 1)
        docs[name.strip()] = url.strip()

    models = args.model or DEFAULT_MODELS
    results: list[CheckResult] = []
    results.extend(check_url(name, url, args.timeout) for name, url in docs.items())
    results.append(check_docker_installed())
    results.extend(check_docker_image(args.image, args.timeout, args.pull))
    if not args.skip_openrouter:
        results.append(check_openrouter_models(models, args.timeout))

    for result in results:
        status = "PASS" if result.ok else "FAIL"
        print(f"[{status}] {result.name}: {result.detail}")

    failed = [result for result in results if not result.ok]
    if failed:
        print(f"\nPREFLIGHT_FAILED: {len(failed)} check(s) failed", file=sys.stderr)
        return 1

    print("\nPREFLIGHT_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
