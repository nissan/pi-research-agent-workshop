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
<body><main>{body}</main></body>
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
<section class="card"><h2>5. Model swap lane</h2><p>Swap OpenAI to OpenRouter, or OpenRouter model A to OpenRouter model B, then tighten the harness around model provenance.</p><a class="button" href="/openrouter">Open model swap lab</a></section>
<section class="card"><h2>6. Outputs</h2>{artifact_links()}<p><a class="button" href="/compare">Compare outputs</a> <a class="button" href="/traces">View tool traces</a></p></section>
<section class="card"><h2>7. If stuck</h2><a class="button" href="/solution">Peek at the full solution</a></section>
"""
        self.send_html(page("Pi Research Agent Workshop", body))

    def do_POST(self) -> None:
        route = self.path.split("?", 1)[0]
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
