#!/usr/bin/env python3
from __future__ import annotations

from collections import deque
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs
import html
import json
import os
import shutil
import subprocess
import threading
import time

ROOT = Path(os.environ.get("WORKSHOP_ROOT", "/workshop"))
if not ROOT.exists():
    ROOT = Path(__file__).resolve().parents[1]
PORT = int(os.environ.get("WORKSHOP_PORT", "8787"))
ALT_BASELINE_MODEL = os.environ.get("ALT_BASELINE_MODEL", "z-ai/glm-4.5-air:free")
ALT_SWAP_MODEL = os.environ.get("ALT_SWAP_MODEL", "qwen/qwen3-next-80b-a3b-instruct:free")
RUN_TIMEOUT_SECONDS = 240
RUN_STATE_LOCK = threading.Lock()
RUN_STATE = {
    "running": False,
    "kind": "",
    "label": "",
    "started_at": 0.0,
    "trace_rel": "",
    "tail": "",
    "result_html": "<p>No run started yet.</p>",
}
ARTIFACT_META_FILE = ROOT / "starter" / "outputs" / ".artifact-meta.json"
CHAT_HISTORY_FILE = ROOT / "starter" / "outputs" / "chat-lab-history.json"
CHAT_TRANSCRIPT_FILE = ROOT / "starter" / "outputs" / "chat-lab-transcript.md"


def read(path: Path | str, default: str = "") -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return default


def page(title: str, body: str) -> str:
    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<script src="/static/htmx.min.js"></script>
<link rel="stylesheet" href="/static/style.css">
<script>
function syncRunButtons() {{
  const panel = document.getElementById("run-status-panel");
  const running = panel && panel.dataset.running === "true";
  document.querySelectorAll("[data-run-form] button").forEach((button) => {{
    if (button.dataset.disabledByCredential === "true") {{
      button.disabled = true;
      return;
    }}
    button.disabled = !!running;
  }});
}}
document.addEventListener("DOMContentLoaded", syncRunButtons);
document.body.addEventListener("htmx:beforeRequest", (event) => {{
  const form = event.target.closest ? event.target.closest("[data-run-form]") : null;
  if (form) {{
    document.querySelectorAll("[data-run-form] button").forEach((button) => {{
      if (button.dataset.disabledByCredential !== "true") {{
        button.disabled = true;
      }}
    }});
  }}
}});
document.body.addEventListener("htmx:afterSwap", syncRunButtons);
</script>
</head>
<body>
<div class="page-bg"></div>
<main>
  <header class="shell-head">
    <div>
      <p class="eyebrow">Pi.dev Workshop</p>
      <p class="shell-title">Specialist Research Agent Lab</p>
    </div>
    <div class="shell-actions">
      <a class="shell-link" href="/">Home</a>
      <a class="shell-link" href="/chat">Chat Lab</a>
      <a class="shell-link" href="/harness">Harness Lab</a>
      <a class="shell-link" href="/compare">Compare</a>
    </div>
  </header>
  <section class="workspace-frame">{body}</section>
</main>
</body>
</html>"""


def safe_rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def read_artifact_meta() -> dict[str, dict[str, str]]:
    raw = read(ARTIFACT_META_FILE, "")
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def write_artifact_meta(meta: dict[str, dict[str, str]]) -> None:
    ARTIFACT_META_FILE.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_META_FILE.write_text(json.dumps(meta, indent=2, sort_keys=True), encoding="utf-8")


def mark_artifacts(paths: list[Path], source: str, label: str) -> None:
    meta = read_artifact_meta()
    stamp = datetime.now().strftime("%H:%M:%S")
    for path in paths:
        if not path.exists() or not path.is_file():
            continue
        rel = safe_rel(path)
        meta[rel] = {
            "source": source,
            "label": label,
            "updated_at": stamp,
        }
    write_artifact_meta(meta)


def artifact_badge(path: Path) -> str:
    meta = read_artifact_meta().get(safe_rel(path), {})
    source = meta.get("source", "unknown")
    label = meta.get("label", "unknown source")
    updated = meta.get("updated_at", datetime.fromtimestamp(path.stat().st_mtime).strftime("%H:%M:%S"))
    size_kb = f"{path.stat().st_size / 1024:.1f}KB"
    if source == "live":
        badge_class = "artifact-live"
        badge_text = f"LIVE - {label}, {updated}, {size_kb}"
    elif source == "fallback":
        badge_class = "artifact-fallback"
        badge_text = f"FALLBACK SAMPLE - {updated}, {size_kb}"
    else:
        badge_class = "artifact-unknown"
        badge_text = f"UNKNOWN SOURCE - {updated}, {size_kb}"
    return f'<span class="artifact-badge {badge_class}">{html.escape(badge_text)}</span>'


def artifact_links() -> str:
    outdir = ROOT / "starter" / "outputs"
    paths = sorted(outdir.glob("*")) if outdir.exists() else []
    items = []
    for path in paths:
        if not path.is_file():
            continue
        if path.name == ".artifact-meta.json":
            continue
        items.append(
            "<li>"
            f'<a href="/artifact?path={html.escape(safe_rel(path))}">{html.escape(safe_rel(path))}</a> '
            f"{artifact_badge(path)}</li>"
        )
    extras = []
    for rel in ["traces", "outputs/traces", "traces"]:
        base = ROOT / rel
        if base.exists() and base.is_dir():
            for path in sorted(base.glob("*")):
                if path.is_file():
                    extras.append(
                        "<li>"
                        f'<a href="/artifact?path={html.escape(safe_rel(path))}">{html.escape(safe_rel(path))}</a> '
                        f"{artifact_badge(path)}</li>"
                    )
    return f'<ul>{"".join(items + extras) or "<li>No outputs yet.</li>"}</ul>'


def copy_fallback_outputs() -> list[Path]:
    outdir = ROOT / "starter" / "outputs"
    outdir.mkdir(parents=True, exist_ok=True)
    mapping = {
        "sample-research-brief-generic.md": "research-brief-generic.md",
        "sample-research-brief-specialized.md": "research-brief-specialized.md",
        "sample-delta-notes.md": "delta-notes.md",
    }
    copied: list[Path] = []
    for src, dst in mapping.items():
        for base in [ROOT / "fallback", ROOT / "starter" / "outputs"]:
            candidate = base / src
            if candidate.exists():
                target = outdir / dst
                shutil.copy2(candidate, target)
                copied.append(target)
                break
    mark_artifacts(copied, "fallback", "fallback sample")
    return copied


def openrouter_key() -> str:
    return os.environ.get("OPENROUTER_API_KEY", "").strip()


def openrouter_env() -> dict[str, str]:
    env = os.environ.copy()
    env["OPENROUTER_API_KEY"] = openrouter_key()
    env.pop("OPENAI_API_KEY", None)
    env.pop("ANTHROPIC_API_KEY", None)
    home = ROOT / "starter" / "outputs" / "openrouter-runtime-home"
    home.mkdir(parents=True, exist_ok=True)
    env["HOME"] = str(home)
    return env


def is_openrouter_capacity_limited(text: str) -> bool:
    lowered = text.lower()
    return any(
        needle in lowered
        for needle in [
            "429",
            "rate limit",
            "ratelimit",
            "too many requests",
            "temporarily rate-limited",
            "daily limit",
            "daily request limit",
            "402",
            "insufficient credit",
            "insufficient credits",
            "payment required",
            "negative credit balance",
            "credit balance",
            "quota exceeded",
        ]
    )


def traces_html() -> str:
    trace_files: list[Path] = []
    for base in [ROOT / "starter" / "outputs" / "traces", ROOT / "traces"]:
        if base.exists():
            trace_files.extend(sorted(base.glob("*")))
    items = "".join(
        "<li>"
        f'<a href="/artifact?path={html.escape(safe_rel(path))}">{html.escape(safe_rel(path))}</a> '
        f"{artifact_badge(path)}</li>"
        for path in trace_files
        if path.is_file() and path.stat().st_size < 500000
    )
    return f'<ul>{items or "<li>No traces yet. Run an agent first.</li>"}</ul>'


def scorecard_html() -> str:
    raw = read(ROOT / "starter" / "outputs" / "harness-delta-scorecard.json", "")
    if not raw:
        return "<p>No harness scorecard yet. Run the loose and harnessed agents, then run harness comparison.</p>"
    try:
        data = json.loads(raw)
    except Exception:
        return f"<pre>{html.escape(raw)}</pre>"
    loose = data.get("loose_signal_count", 0)
    harnessed = data.get("harnessed_signal_count", 0)
    passed = data.get("harness_check_pass")
    thesis = html.escape(str(data.get("thesis", "")))
    return (
        '<div class="scorecard">'
        f"<p><strong>Loose signals:</strong> {loose}</p>"
        f"<p><strong>Harnessed signals:</strong> {harnessed}</p>"
        f"<p><strong>Harness check pass:</strong> {passed}</p>"
        f"<p>{thesis}</p>"
        "</div>"
    )


def read_chat_history() -> list[dict[str, str]]:
    raw = read(CHAT_HISTORY_FILE, "")
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except Exception:
        return []
    if not isinstance(data, list):
        return []
    history = []
    for item in data[-30:]:
        if isinstance(item, dict):
            history.append(
                {
                    "mode": str(item.get("mode", "")),
                    "prompt": str(item.get("prompt", "")),
                    "response": str(item.get("response", "")),
                    "trace": str(item.get("trace", "")),
                    "stamp": str(item.get("stamp", "")),
                }
            )
    return history


def write_chat_history(history: list[dict[str, str]]) -> None:
    CHAT_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    CHAT_HISTORY_FILE.write_text(json.dumps(history[-30:], indent=2), encoding="utf-8")


def chat_mode_label(mode: str) -> str:
    return {
        "plain": "Plain model chat",
        "agent": "Agent chat - tools allowed, harness off",
        "harnessed": "Harnessed agent chat - tools plus policy",
    }.get(mode, "Unknown mode")


def make_chat_response(mode: str, prompt: str) -> tuple[str, str, list[Path]]:
    prompt = prompt.strip()
    outdir = ROOT / "starter" / "outputs"
    outdir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    artifacts: list[Path] = []
    safe_prompt = prompt or "No prompt supplied."
    if mode == "plain":
        response = (
            "Model-only answer:\n"
            f"I can discuss the request, but I am not using workshop tools or writing artifacts. "
            f"For this prompt, I would first clarify the research question, identify likely source types, "
            f"and warn that any paper claims need verification before publication.\n\nPrompt: {safe_prompt}"
        )
        trace = "No tools used. No harness policy applied."
        return response, trace, artifacts
    if mode == "agent":
        copied = copy_fallback_outputs()
        artifacts.extend(copied)
        trace_path = outdir / f"chat-agent-trace-{stamp}.md"
        trace = (
            "Agent mode trace:\n"
            "- Read the participant prompt.\n"
            "- Selected fallback/sample workshop artifacts because no live credential lane is required for this demo.\n"
            "- Would use arXiv search, PDF evidence reading, and domain packs in a live credentialed run.\n"
            "- Harness enforcement: OFF.\n"
        )
        trace_path.write_text(trace + f"\nPrompt: {safe_prompt}\n", encoding="utf-8")
        artifacts.append(trace_path)
        response = (
            "Agent answer with tools available:\n"
            "I can turn the conversation into artifacts. In this no-key demo I copied the sample research brief, "
            "specialized brief, and delta notes so you can inspect the same output surfaces a live tool-using run would create. "
            "Because the harness is off, this answer should be treated as helpful but not enforced."
        )
        return response, trace, artifacts
    if mode == "harnessed":
        report = {
            "mode": "harnessed_chat_demo",
            "prompt": safe_prompt,
            "harness_check_pass": True,
            "enforced": [
                "label evidence versus assumptions",
                "keep writes inside approved output paths",
                "surface human review boundary",
                "preserve provenance for generated artifacts",
            ],
            "blocked_actions": [
                "No arbitrary network browsing in demo mode",
                "No secret display or persistence",
            ],
        }
        report_path = outdir / "chat-harness-report.json"
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        artifacts.append(report_path)
        mark_artifacts([report_path], "live", "Chat Lab harness report")
        trace = (
            "Harnessed agent trace:\n"
            "- Applied the harness policy before answering.\n"
            "- Required evidence/assumption separation.\n"
            "- Wrote a harness report artifact.\n"
            "- Blocked secret exposure and arbitrary external browsing in demo mode.\n"
        )
        response = (
            "Harnessed agent answer:\n"
            "I can still help with the request, but the harness changes the contract: claims need evidence labels, "
            "writes stay inside approved outputs, and risky actions are blocked or reported. See chat-harness-report.json "
            "for the enforced checks."
        )
        return response, trace, artifacts
    return "Unknown chat mode.", "No action taken.", artifacts


def render_chat_history() -> str:
    history = read_chat_history()
    if not history:
        return "<p>No chat turns yet. Enter a prompt and choose a mode.</p>"
    cards = []
    for item in history:
        cards.append(
            '<article class="chat-turn">'
            f'<div class="chat-meta">{html.escape(item["stamp"])} - {html.escape(chat_mode_label(item["mode"]))}</div>'
            f'<div class="chat-user"><strong>You:</strong> {html.escape(item["prompt"])}</div>'
            f'<pre>{html.escape(item["response"])}</pre>'
            f'<details><summary>Trace / enforcement</summary><pre>{html.escape(item["trace"])}</pre></details>'
            "</article>"
        )
    return "".join(cards)


def chat_transcript_markdown() -> str:
    history = read_chat_history()
    lines = ["# Chat Lab Transcript", ""]
    if not history:
        lines.append("No chat turns recorded yet.")
        return "\n".join(lines) + "\n"
    for index, item in enumerate(history, start=1):
        lines.extend(
            [
                f"## Turn {index}: {chat_mode_label(item['mode'])}",
                "",
                f"Time: {item['stamp']}",
                "",
                "### Prompt",
                item["prompt"] or "No prompt supplied.",
                "",
                "### Response",
                item["response"],
                "",
                "### Trace / Enforcement",
                item["trace"],
                "",
            ]
        )
    return "\n".join(lines)


def write_chat_transcript() -> Path:
    CHAT_TRANSCRIPT_FILE.parent.mkdir(parents=True, exist_ok=True)
    CHAT_TRANSCRIPT_FILE.write_text(chat_transcript_markdown(), encoding="utf-8")
    mark_artifacts([CHAT_TRANSCRIPT_FILE], "live", "Chat Lab transcript")
    return CHAT_TRANSCRIPT_FILE


def kind_label(kind: str) -> str:
    mapping = {
        "generic": "generic default lane",
        "generic_alt": "generic OpenRouter lane",
        "specialized": "specialized default lane",
        "specialized_alt": "specialized OpenRouter lane",
        "specialized_alt_swap": "specialized second-model lane",
        "unharnessed": "loose agent",
        "harnessed": "harnessed agent",
        "harness_compare": "harness compare",
        "fallback": "fallback sample copy",
    }
    return mapping.get(kind, kind)


def kind_provider_label(kind: str) -> str:
    mapping = {
        "generic": "Pi/OpenAI/Claude lane",
        "generic_alt": f"OpenRouter {ALT_BASELINE_MODEL}",
        "specialized": "Pi/OpenAI/Claude lane",
        "specialized_alt": f"OpenRouter {ALT_BASELINE_MODEL}",
        "specialized_alt_swap": f"OpenRouter {ALT_SWAP_MODEL}",
        "unharnessed": "Pi no-extensions/no-skills",
        "harnessed": "Pi harnessed specialist",
        "harness_compare": "local harness compare script",
    }
    return mapping.get(kind, "unknown provider")


def known_output_paths() -> list[Path]:
    outdir = ROOT / "starter" / "outputs"
    paths = []
    if outdir.exists():
        for path in outdir.glob("*"):
            if path.is_file() and path.name != ".artifact-meta.json":
                paths.append(path)
    for extra in [ROOT / "traces", ROOT / "starter" / "outputs" / "traces"]:
        if extra.exists():
            for path in extra.glob("*"):
                if path.is_file():
                    paths.append(path)
    return paths


def mark_recent_live_outputs(started_at: float, provider_label: str) -> None:
    recent = []
    for path in known_output_paths():
        if path.stat().st_mtime >= started_at - 1:
            recent.append(path)
    mark_artifacts(recent, "live", provider_label)


def set_run_state(**updates: object) -> None:
    with RUN_STATE_LOCK:
        RUN_STATE.update(updates)


def get_run_state() -> dict[str, object]:
    with RUN_STATE_LOCK:
        return dict(RUN_STATE)


def render_result_html(title: str, detail: str, status_class: str = "status-idle") -> str:
    return f'<div class="status-summary {status_class}"><h3>{html.escape(title)}</h3>{detail}</div>'


def render_run_status_panel() -> str:
    state = get_run_state()
    running = bool(state["running"])
    label = html.escape(str(state["label"] or "idle"))
    tail = html.escape(str(state["tail"] or "No trace output yet."))
    if running:
        elapsed = int(time.time() - float(state["started_at"] or time.time()))
        body = (
            f'<p><strong>Agent running ({label})</strong> - ~{elapsed}s elapsed</p>'
            f'<p>Trace file: <code>{html.escape(str(state["trace_rel"]))}</code></p>'
            f'<pre>{tail}</pre>'
        )
        return f'<section id="run-status-panel" class="card status-card" data-running="true">{body}</section>'
    return (
        '<section id="run-status-panel" class="card status-card" data-running="false">'
        f'{state["result_html"]}'
        "</section>"
    )


def run_button(kind: str, text: str) -> str:
    disabled = False
    reason = ""
    classes = ["run-button"]
    if kind in {"generic_alt", "specialized_alt", "specialized_alt_swap"} and not openrouter_key():
        disabled = True
        reason = "OpenRouter key not present in container environment"
    if kind in {"generic_alt", "specialized_alt", "specialized_alt_swap"} and openrouter_key():
        classes.append("lane-highlight")
    if kind in {"generic", "specialized"} and (os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")):
        classes.append("lane-highlight")
    attrs = [
        f'name="kind"',
        f'value="{html.escape(kind)}"',
        f'class="{" ".join(classes)}"',
    ]
    if disabled:
        attrs.append("disabled")
        attrs.append('data-disabled-by-credential="true"')
        attrs.append(f'title="{html.escape(reason)}"')
    return f'<button {" ".join(attrs)}>{html.escape(text)}</button>'


def start_run(kind: str, prompt: str, cmd: list[str], env: dict[str, str] | None) -> tuple[bool, str]:
    with RUN_STATE_LOCK:
        if RUN_STATE["running"]:
            return False, "Another run is already active."
        trace_path = ROOT / "traces" / f"{int(time.time())}-{kind}.log"
        trace_path.parent.mkdir(parents=True, exist_ok=True)
        RUN_STATE.update(
            {
                "running": True,
                "kind": kind,
                "label": kind_label(kind),
                "started_at": time.time(),
                "trace_rel": safe_rel(trace_path),
                "tail": "Starting agent process...",
                "result_html": render_result_html("Run queued", "<p>Starting…</p>", "status-running"),
            }
        )

    def worker() -> None:
        trace_path = ROOT / str(get_run_state()["trace_rel"])
        prompt_start = float(get_run_state()["started_at"])
        tail_lines: deque[str] = deque(maxlen=40)
        provider = kind_provider_label(kind)
        try:
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=ROOT / "starter",
                env=env,
                bufsize=1,
            )
            assert proc.stdin is not None
            assert proc.stdout is not None
            proc.stdin.write(prompt)
            proc.stdin.close()
            with trace_path.open("w", encoding="utf-8") as handle:
                def reader() -> None:
                    for line in proc.stdout:
                        handle.write(line)
                        handle.flush()
                        tail_lines.append(line.rstrip())
                        set_run_state(tail="\n".join(tail_lines) or "Running...")
                reader_thread = threading.Thread(target=reader, daemon=True)
                reader_thread.start()
                timed_out = False
                try:
                    returncode = proc.wait(timeout=RUN_TIMEOUT_SECONDS)
                except subprocess.TimeoutExpired:
                    timed_out = True
                    proc.kill()
                    returncode = proc.wait()
                reader_thread.join(timeout=2)
            if timed_out:
                result_html = render_result_html(
                    "Run timed out",
                    "<p>Use fallback outputs and keep moving. If the UI or Docker CLI stops responding, restart Docker and resume from the saved outputs.</p>",
                    "status-error",
                )
                set_run_state(running=False, tail="\n".join(tail_lines), result_html=result_html)
                return
            combined = read(trace_path)
            if kind in {"generic_alt", "specialized_alt", "specialized_alt_swap"} and is_openrouter_capacity_limited(combined):
                copied = copy_fallback_outputs()
                result_html = render_result_html(
                    "OpenRouter limit reached; fallback outputs copied",
                    f"<p>Copied {html.escape(', '.join(path.name for path in copied) or 'no files')}.</p><p><a href=\"/compare\">Compare</a> · <a href=\"/traces\">Traces</a> · <a href=\"/harness\">Harness lab</a></p>",
                    "status-warning",
                )
                set_run_state(running=False, tail="\n".join(tail_lines), result_html=result_html)
                return
            mark_recent_live_outputs(prompt_start, provider)
            result_html = render_result_html(
                f"{kind_label(kind)} finished: exit {returncode}",
                f"<p>{html.escape(provider)}</p><p><a href=\"/compare\">Compare</a> · <a href=\"/traces\">Traces</a> · <a href=\"/harness\">Harness lab</a></p>",
                "status-success" if returncode == 0 else "status-error",
            )
            set_run_state(running=False, tail="\n".join(tail_lines), result_html=result_html)
        except Exception as exc:
            result_html = render_result_html(
                "Run failed to start",
                f"<p>{html.escape(str(exc))}</p>",
                "status-error",
            )
            set_run_state(running=False, result_html=result_html)

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    return True, ""


class Handler(BaseHTTPRequestHandler):
    def send_html(self, content: str, status: int = 200) -> None:
        data = content.encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "text/html; charset=utf-8")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_text(self, content: str, filename: str | None = None) -> None:
        data = content.encode("utf-8")
        self.send_response(200)
        self.send_header("content-type", "text/markdown; charset=utf-8")
        self.send_header("content-length", str(len(data)))
        if filename:
            self.send_header("content-disposition", f'attachment; filename="{filename}"')
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        if path == "/static/style.css":
            css = read(ROOT / "app" / "static" / "style.css")
            self.send_response(200)
            self.send_header("content-type", "text/css")
            self.end_headers()
            self.wfile.write(css.encode())
            return
        if path == "/static/htmx.min.js":
            js = read(ROOT / "app" / "static" / "htmx.min.js")
            self.send_response(200)
            self.send_header("content-type", "application/javascript")
            self.end_headers()
            self.wfile.write(js.encode())
            return
        if path == "/health":
            status = {"ok": True, "pi": subprocess.run(["bash", "-lc", "command -v pi >/dev/null"], cwd=ROOT).returncode == 0}
            self.send_response(200)
            self.send_header("content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(status).encode())
            return
        if path == "/partial/health":
            pi_ok = subprocess.run(["bash", "-lc", "command -v pi >/dev/null"], cwd=ROOT).returncode == 0
            writable = os.access(ROOT / "starter", os.W_OK)
            auth_modes = []
            if os.environ.get("OPENAI_API_KEY"):
                auth_modes.append("OPENAI_API_KEY present")
            if os.environ.get("ANTHROPIC_API_KEY"):
                auth_modes.append("ANTHROPIC_API_KEY present")
            if os.environ.get("OPENROUTER_API_KEY"):
                auth_modes.append("OPENROUTER_API_KEY present for OpenRouter lane")
            auth_hint = "; ".join(auth_modes) or "Use /login, pass an OpenAI/Claude runtime key, or pass OPENROUTER_API_KEY for the OpenRouter lane."
            self.send_html(
                "<ul>"
                f'<li>Pi installed: {"YES" if pi_ok else "NO"}</li>'
                f'<li>Workspace writable: {"YES" if writable else "NO"}</li>'
                f"<li>Auth: {html.escape(auth_hint)}</li>"
                "</ul>"
            )
            return
        if path == "/partial/run-status":
            self.send_html(render_run_status_panel())
            return
        if path == "/chat-transcript":
            transcript = write_chat_transcript()
            self.send_text(read(transcript), "chat-lab-transcript.md")
            return
        if path == "/artifact":
            qs = parse_qs(self.path.split("?", 1)[1] if "?" in self.path else "")
            rel = qs.get("path", [""])[0]
            target = (ROOT / rel).resolve()
            if ROOT.resolve() not in target.parents and target != ROOT.resolve():
                self.send_html(page("Blocked", "<h1>Blocked path</h1>"), 403)
                return
            self.send_html(page(rel, f'<p><a href="/">Home</a></p><pre>{html.escape(read(target, "Not found"))}</pre>'))
            return
        if path == "/solution":
            files = sorted((ROOT / "solution").rglob("*")) if (ROOT / "solution").exists() else []
            lis = "".join(
                f'<li><a href="/artifact?path={html.escape(safe_rel(p))}">{html.escape(safe_rel(p))}</a></li>'
                for p in files
                if p.is_file() and p.stat().st_size < 200000
            )
            body = (
                '<h1>Full solution folder</h1><p><a href="/">Home</a></p>'
                "<p>Spoiler zone: use this when stuck.</p>"
                '<form method="post" action="/copy-solution" hx-post="/copy-solution" hx-target="#solution-copy" hx-swap="innerHTML"><button type="submit">Copy solution into starter workspace</button></form>'
                '<div id="solution-copy"></div>'
                f"<ul>{lis}</ul>"
            )
            self.send_html(page("Solution", body))
            return
        if path == "/openrouter":
            guide = html.escape(read(ROOT / "starter" / "HUGGINGFACE-MODEL-SWAP.md", "OpenRouter guide not found."))
            pack_dir = ROOT / "starter" / "sources" / "domain-packs"
            packs = sorted(pack_dir.glob("*.md")) if pack_dir.exists() else []
            lis = "".join(
                f"<li><strong>{html.escape(pack.name)}</strong><pre>{html.escape(read(pack))}</pre></li>"
                for pack in packs
            )
            body = (
                '<h1>OpenRouter / model swap</h1><p><a href="/">Home</a></p>'
                f'<section class="card"><h2>Guide</h2><pre>{guide}</pre></section>'
                f'<section class="card"><h2>Domain specialization packs</h2><ul>{lis}</ul></section>'
            )
            self.send_html(page("OpenRouter / model swap", body))
            return
        if path == "/harness":
            policy = html.escape(read(ROOT / "starter" / "harness" / "HARNESS-POLICY.md", "Harness policy not found."))
            report = html.escape(read(ROOT / "starter" / "outputs" / "harness-report.json", "Run the harnessed agent to generate a report."))
            body = f"""
<h1>Harness Lab</h1><p><a href="/">Home</a></p>
<section class="card"><h2>Thesis</h2><p><strong>Prompts ask. Harnesses enforce.</strong> Run a loose agent, then run a harnessed agent with tool boundaries, evidence gates, and output validation.</p></section>
{render_run_status_panel()}
<section class="card"><h2>Run before/after</h2><form data-run-form hx-post="/run" hx-target="#run-status-panel" hx-swap="outerHTML">
{run_button("unharnessed", "Run loose agent")}
{run_button("harnessed", "Run harnessed agent")}
<button name="kind" value="harness_compare" class="run-button">Build scorecard</button>
</form></section>
<section class="card"><h2>Harness policy</h2><pre>{policy}</pre></section>
<section class="card"><h2>Latest outputs</h2>{artifact_links()}</section>
<section class="card"><h2>Harness delta scorecard</h2>{scorecard_html()}</section>
<section class="card"><h2>Latest harness report</h2><pre>{report}</pre></section>
"""
            self.send_html(page("Harness Lab", body))
            return
        if path == "/chat":
            body = f"""
<h1>Chat Lab</h1><p><a href="/">Home</a></p>
<section class="card"><h2>Compare the same prompt three ways</h2><p>This is the ChatGPT-like workshop surface: model-only chat, tool-using agent chat, and harnessed agent chat. Conversation history is saved in <code>starter/outputs/chat-lab-history.json</code>.</p><p><strong>Workshop-fast path:</strong> for a 45-minute session, click <strong>Run all three modes</strong> first so participants can inspect the end-user chat results in the browser before reviewing artifacts or source files.</p><div class="mode-summary"><div><strong>Plain</strong><span>No tools or policy.</span></div><div><strong>Agent</strong><span>Tools/output surfaces, harness off.</span></div><div><strong>Harnessed</strong><span>Policy, provenance, report.</span></div></div></section>
<section class="card"><form method="post" action="/chat" hx-post="/chat" hx-target="#chat-history" hx-swap="innerHTML">
<label for="prompt"><strong>Prompt</strong></label>
<textarea id="prompt" name="prompt" rows="4" placeholder="Ask for a research brief, paper comparison, or evidence summary.">Compare two recent retrieval-augmented generation papers and separate evidence from assumptions.</textarea>
<div class="mode-grid">
<label><input type="radio" name="mode" value="plain" checked> Plain chat - no tools, no harness</label>
<label><input type="radio" name="mode" value="agent"> Agent chat - tools/domain packs, harness off</label>
<label><input type="radio" name="mode" value="harnessed"> Harnessed agent chat - tools plus policy</label>
</div>
<button type="submit" name="action" value="all">Run all three modes</button>
<button type="submit" name="action" value="single">Send selected mode</button>
</form></section>
<section class="card"><h2>Conversation</h2><form method="post" action="/chat-clear" hx-post="/chat-clear" hx-target="#chat-history" hx-swap="innerHTML"><button type="submit">Clear conversation</button> <a class="button" href="/chat-transcript">Download transcript</a></form><div id="chat-history">{render_chat_history()}</div></section>
<section class="card"><h2>Artifacts</h2>{artifact_links()}<p><a class="button" href="/compare">Compare outputs</a> <a class="button" href="/harness">Harness lab</a> <a class="button" href="/chat-transcript">Export transcript</a></p></section>
"""
            self.send_html(page("Chat Lab", body))
            return
        if path == "/compare":
            generic = html.escape(read(ROOT / "starter" / "outputs" / "research-brief-generic.md", "Generic output not created yet."))
            unharnessed = html.escape(read(ROOT / "starter" / "outputs" / "research-brief-unharnessed.md", "Loose/unharnessed output not created yet."))
            specialized = html.escape(read(ROOT / "starter" / "outputs" / "research-brief-specialized.md", "Specialized output not created yet."))
            delta = html.escape(read(ROOT / "starter" / "outputs" / "delta-notes.md", "Delta notes not created yet."))
            report = html.escape(read(ROOT / "starter" / "outputs" / "harness-report.json", "Harness report not created yet."))
            body = f"""
<h1>Compare outputs</h1><p><a href="/">Home</a></p>
{render_run_status_panel()}
<section class="card"><h2>Current artifacts</h2>{artifact_links()}</section>
<div class="grid"><section><h2>Loose / unharnessed</h2><pre>{unharnessed}</pre></section><section><h2>Harnessed specialist</h2><pre>{specialized}</pre></section></div>
<section class="card"><h2>Generic baseline</h2><pre>{generic}</pre></section>
<section class="card"><h2>Delta notes</h2><pre>{delta}</pre></section>
<section class="card"><h2>Harness delta scorecard</h2>{scorecard_html()}</section>
<section class="card"><h2>Harness report</h2><pre>{report}</pre></section>
"""
            self.send_html(page("Compare", body))
            return
        if path == "/traces":
            body = f"<h1>Tool traces</h1><p><a href=\"/\">Home</a></p>{render_run_status_panel()}{traces_html()}"
            self.send_html(page("Tool traces", body))
            return

        body = f"""
<h1>Pi Research Agent Workshop</h1>
<section class="card"><h2>1. Health</h2><div hx-get="/partial/health" hx-trigger="load" hx-swap="innerHTML">Checking...</div></section>
{render_run_status_panel()}
<section class="card"><h2>2. Choose your credential lane</h2><p><strong>No key?</strong> Use the fallback outputs first so you can still complete the workshop discussion. OpenRouter buttons are disabled unless <code>OPENROUTER_API_KEY</code> is present. The matching credential lane is highlighted when a key is already detected.</p>
<form data-run-form hx-post="/run" hx-target="#run-status-panel" hx-swap="outerHTML">
{run_button("fallback", "No key required: use fallback sample outputs")}
{run_button("generic_alt", "Run generic agent with OpenRouter")}
{run_button("specialized_alt", "Run specialized arXiv agent with OpenRouter")}
{run_button("specialized_alt_swap", "Run specialist with second OpenRouter model")}
{run_button("generic", "Run generic agent with Pi/OpenAI/Claude")}
{run_button("specialized", "Run specialized arXiv agent with Pi/OpenAI/Claude")}
</form></section>
<section class="card"><h2>3. Example prompts</h2><p>Use these to compare baseline, specialization, and harnessed behavior.</p>
<h3>Before specialization: generic baseline</h3><pre>Read AGENTS.md and inputs/generic-brief-request.md. Use sources/source-notes.md. Write outputs/research-brief-generic.md. Include source notes used, limitations, and open questions.</pre>
<h3>After specialization: tools + domain context</h3><pre>Use the arxiv-literature-scan and pdf-evidence-reader skills. Read sources/domain-packs/artificial-intelligence.md. Search arXiv, rank useful papers, read the best PDF if available, then write outputs/research-brief-specialized.md and outputs/delta-notes.md. Include evidence labels, provider/model used, risks, and open questions.</pre>
<h3>Harnessed: enforce and measure</h3><pre>Run the specialist research task under the harness policy. Use only allowed arXiv/evidence tools, write only approved output files, label evidence versus assumptions, run the harness check, and produce outputs/harness-report.json plus a short comparison against the generic baseline.</pre></section>
<section class="card"><h2>4. Harness lab</h2><p>Show why the agentic harness matters: loose prompt vs enforced policy + evidence gate.</p><a class="button" href="/harness">Open harness lab</a></section>
<section class="card"><h2>5. Chat lab</h2><p>Show the end-user result first: compare a normal chat answer with a tool-using agent and a harnessed agent using the same prompt.</p><a class="button" href="/chat">Open chat lab</a></section>
<section class="card"><h2>6. Model swap lane</h2><p>Swap OpenAI to OpenRouter, or OpenRouter model A to OpenRouter model B, then tighten the harness around model provenance.</p><a class="button" href="/openrouter">Open model swap lab</a></section>
<section class="card"><h2>7. Outputs</h2>{artifact_links()}<p><a class="button" href="/compare">Compare outputs</a> <a class="button" href="/traces">View tool traces</a></p></section>
<section class="card"><h2>8. If stuck</h2><a class="button" href="/solution">Peek at the full solution</a></section>
"""
        self.send_html(page("Pi Research Agent Workshop", body))

    def do_POST(self) -> None:
        route = self.path.split("?", 1)[0]
        if route == "/chat-clear":
            CHAT_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
            CHAT_HISTORY_FILE.write_text("[]\n", encoding="utf-8")
            if CHAT_TRANSCRIPT_FILE.exists():
                CHAT_TRANSCRIPT_FILE.unlink()
            self.send_html(render_chat_history())
            return

        if route == "/chat":
            length = int(self.headers.get("content-length", "0"))
            form = parse_qs(self.rfile.read(length).decode())
            prompt = form.get("prompt", [""])[0].strip()
            mode = form.get("mode", ["plain"])[0]
            history = read_chat_history()
            modes = ["plain", "agent", "harnessed"] if form.get("action", ["single"])[0] == "all" else [mode]
            for selected_mode in modes:
                response, trace, artifacts = make_chat_response(selected_mode, prompt)
                if artifacts:
                    mark_artifacts(artifacts, "live", chat_mode_label(selected_mode))
                history.append(
                    {
                        "mode": selected_mode,
                        "prompt": prompt,
                        "response": response,
                        "trace": trace,
                        "stamp": datetime.now().strftime("%H:%M:%S"),
                    }
                )
            write_chat_history(history)
            write_chat_transcript()
            self.send_html(render_chat_history())
            return

        if route == "/copy-solution":
            dst = ROOT / "starter"
            src = ROOT / "solution"

            def copy_into(source: Path, target: Path) -> None:
                if source.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    for child in source.iterdir():
                        copy_into(child, target / child.name)
                    return
                shutil.copy2(source, target)

            for item in src.iterdir():
                target = dst / item.name
                copy_into(item, target)
            self.send_html("<p>Solution copied into starter workspace. You can now inspect or run it.</p>")
            return

        length = int(self.headers.get("content-length", "0"))
        form = parse_qs(self.rfile.read(length).decode())
        kind = form.get("kind", [""])[0]
        prompts = {
            "generic": "Read the project instructions and generate the research brief requested in inputs/generic-brief-request.md. Use sources/source-notes.md. Write the result to outputs/research-brief-generic.md.",
            "generic_alt": f"Read AGENTS.md and inputs/generic-brief-request.md. Use sources/source-notes.md. Write outputs/research-brief-generic.md. Include provider/model used as openrouter / {ALT_BASELINE_MODEL}, source notes used, limitations, and open questions.",
            "specialized": "Use the arxiv-literature-scan and pdf-evidence-reader skills. Identify a research keyword, search arXiv, rank results, read the best PDF if available, then write outputs/arxiv-ranked-results.json, outputs/pdf-evidence-notes.md, outputs/research-brief-specialized.md and outputs/delta-notes.md.",
            "specialized_alt": f"Use the arxiv-literature-scan and pdf-evidence-reader skills with openrouter / {ALT_BASELINE_MODEL}. Identify a research keyword, search arXiv, rank results, read the best PDF if available, then write outputs/arxiv-ranked-results.json, outputs/pdf-evidence-notes.md, outputs/research-brief-specialized.md and outputs/delta-notes.md. Include provider/model used, evidence labels, limitations, and open questions.",
            "specialized_alt_swap": f"Rerun the specialist brief with the same inputs and the Artificial Intelligence domain pack using openrouter / {ALT_SWAP_MODEL}. Write outputs/research-brief-specialized.md and outputs/delta-notes.md. Compare against the first model run. Include provider/model used, domain pack used, evidence labels, improvements, regressions, risks, and open questions. Run the harness check before completion.",
            "unharnessed": read(ROOT / "starter" / "prompts" / "unharnessed-research-agent.md"),
            "harnessed": read(ROOT / "starter" / "prompts" / "harnessed-research-agent.md"),
        }

        if kind == "harness_compare":
            trace = ROOT / "traces" / f"{int(time.time())}-harness-compare.log"
            trace.parent.mkdir(parents=True, exist_ok=True)
            proc = subprocess.run(
                ["python3", "tools/harness_compare.py"],
                text=True,
                cwd=ROOT / "starter",
                capture_output=True,
                timeout=30,
            )
            trace.write_text(proc.stdout + "\n--- STDERR ---\n" + proc.stderr, encoding="utf-8")
            mark_artifacts([trace], "live", kind_provider_label(kind))
            safe = html.escape((proc.stdout + proc.stderr)[-4000:])
            result = render_result_html(
                f"Harness scorecard finished: exit {proc.returncode}",
                f"<pre>{safe}</pre><p><a href=\"/compare\">Compare</a> · <a href=\"/harness\">Harness lab</a></p>",
                "status-success" if proc.returncode == 0 else "status-error",
            )
            set_run_state(running=False, tail="", result_html=result)
            self.send_html(render_run_status_panel())
            return

        if kind == "fallback":
            copied = copy_fallback_outputs()
            result = render_result_html(
                "Fallback outputs copied",
                f"<p>Copied {html.escape(', '.join(path.name for path in copied) or 'no files')}.</p><p><a href=\"/compare\">Compare</a> · <a href=\"/traces\">Traces</a></p>",
                "status-warning",
            )
            set_run_state(running=False, tail="", result_html=result)
            self.send_html(render_run_status_panel())
            return

        prompt = prompts.get(kind)
        if not prompt:
            self.send_html("<p>Unknown run.</p>", 400)
            return

        if kind in {"generic_alt", "specialized_alt", "specialized_alt_swap"} and not openrouter_key():
            result = render_result_html(
                "OpenRouter key not detected",
                '<p>Restart the container with <code>-e OPENROUTER_API_KEY="$OPENROUTER_API_KEY"</code>, or use the fallback sample outputs.</p>',
                "status-warning",
            )
            set_run_state(running=False, tail="", result_html=result)
            self.send_html(render_run_status_panel())
            return

        cmd = ["pi", "-p"]
        if kind == "unharnessed":
            cmd = ["pi", "-p", "--no-extensions", "--no-skills"]
        if kind in {"generic_alt", "specialized_alt"}:
            cmd = ["pi", "-p", "--provider", "openrouter", "--model", ALT_BASELINE_MODEL]
        if kind == "specialized_alt_swap":
            cmd = ["pi", "-p", "--provider", "openrouter", "--model", ALT_SWAP_MODEL]
        env = openrouter_env() if kind in {"generic_alt", "specialized_alt", "specialized_alt_swap"} else None

        started, message = start_run(kind, prompt, cmd, env)
        if not started:
            result = render_result_html(
                "Run already active",
                f"<p>{html.escape(message)} Refresh the live status below instead of starting another lane.</p>",
                "status-warning",
            )
            set_run_state(result_html=result)
        self.send_html(render_run_status_panel())


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
