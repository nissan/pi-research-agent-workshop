#!/usr/bin/env python3
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs
import html
import json
import os
import shutil
import subprocess
import threading
import time

ROOT = Path(os.environ.get('WORKSHOP_ROOT', '/workshop'))
if not ROOT.exists():
    ROOT = Path(__file__).resolve().parents[1]
PORT = int(os.environ.get('WORKSHOP_PORT', '8787'))
ALT_BASELINE_MODEL = os.environ.get('ALT_BASELINE_MODEL', 'z-ai/glm-4.5-air:free')
ALT_SWAP_MODEL = os.environ.get('ALT_SWAP_MODEL', 'qwen/qwen3-next-80b-a3b-instruct:free')
RUN_LOCK = threading.Lock()


def read(path, default=''):
    try:
        return Path(path).read_text(encoding='utf-8')
    except FileNotFoundError:
        return default


def page(title, body):
    return f'''<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<script src="/static/htmx.min.js"></script>
<link rel="stylesheet" href="/static/style.css">
</head><body><main>{body}</main></body></html>'''


def safe_rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def artifact_links():
    outdir = ROOT / 'starter' / 'outputs'
    outs = sorted(outdir.glob('*.md')) if outdir.exists() else []
    items = ''.join(
        f'<li><a href="/artifact?path={html.escape(safe_rel(p))}">{html.escape(safe_rel(p))}</a></li>'
        for p in outs
    )
    extras = []
    for rel in ['outputs/harness-report.json', 'outputs/arxiv-ranked-results.json']:
        p = ROOT / 'starter' / rel
        if p.exists():
            extras.append(f'<li><a href="/artifact?path={html.escape(safe_rel(p))}">{html.escape(safe_rel(p))}</a></li>')
    return f'<ul>{items + "".join(extras) or "<li>No outputs yet.</li>"}</ul>'


def run_indicator(target='run-result'):
    return (
        f'<div id="{target}-indicator" class="htmx-indicator run-indicator" role="status" aria-live="polite">'
        '<span class="spinner" aria-hidden="true"></span> Running... this can take a few minutes. '
        'If a live model stalls, fallback outputs will keep the workshop moving.'
        '</div>'
    )


def copy_fallback_outputs():
    outdir = ROOT / 'starter' / 'outputs'
    outdir.mkdir(exist_ok=True)
    mapping = {
        'sample-research-brief-generic.md': 'research-brief-generic.md',
        'sample-research-brief-specialized.md': 'research-brief-specialized.md',
        'sample-delta-notes.md': 'delta-notes.md',
    }
    copied = []
    for src, dst in mapping.items():
        for base in [ROOT / 'fallback', ROOT / 'starter' / 'outputs']:
            if (base / src).exists():
                shutil.copy2(base / src, outdir / dst)
                copied.append(dst)
                break
    return copied


def openrouter_key():
    return os.environ.get('OPENROUTER_API_KEY', '').strip()


def openrouter_env():
    env = os.environ.copy()
    env['OPENROUTER_API_KEY'] = openrouter_key()
    # Keep OpenRouter browser buttons isolated from saved/default OpenAI/Claude
    # auth so a persisted Pi login cannot silently steer these runs elsewhere.
    env.pop('OPENAI_API_KEY', None)
    env.pop('ANTHROPIC_API_KEY', None)
    home = ROOT / 'starter' / 'outputs' / 'openrouter-runtime-home'
    home.mkdir(parents=True, exist_ok=True)
    env['HOME'] = str(home)
    return env


def is_openrouter_capacity_limited(text):
    lowered = text.lower()
    return (
        '429' in lowered
        or 'rate limit' in lowered
        or 'ratelimit' in lowered
        or 'too many requests' in lowered
        or 'temporarily rate-limited' in lowered
        or 'daily limit' in lowered
        or 'daily request limit' in lowered
        or '402' in lowered
        or 'insufficient credit' in lowered
        or 'insufficient credits' in lowered
        or 'payment required' in lowered
        or 'negative credit balance' in lowered
        or 'credit balance' in lowered
        or 'quota exceeded' in lowered
    )


def traces_html():
    trace_files = []
    for base in [ROOT / 'starter' / 'outputs' / 'traces', ROOT / 'traces']:
        if base.exists():
            trace_files.extend(sorted(base.glob('*')))
    items = ''.join(
        f'<li><a href="/artifact?path={html.escape(safe_rel(p))}">{html.escape(safe_rel(p))}</a></li>'
        for p in trace_files if p.is_file() and p.stat().st_size < 500000
    )
    return f'<ul>{items or "<li>No traces yet. Run the harnessed specialist agent first.</li>"}</ul>'


def scorecard_html():
    raw = read(ROOT / 'starter' / 'outputs' / 'harness-delta-scorecard.json', '')
    if not raw:
        return '<p>No harness scorecard yet. Run the loose and harnessed agents, then run harness comparison.</p>'
    try:
        data = json.loads(raw)
    except Exception:
        return f'<pre>{html.escape(raw)}</pre>'
    loose = data.get('loose_signal_count', 0)
    harnessed = data.get('harnessed_signal_count', 0)
    passed = data.get('harness_check_pass')
    thesis = html.escape(str(data.get('thesis', '')) )
    return f'<div class="scorecard"><p><strong>Loose signals:</strong> {loose}</p><p><strong>Harnessed signals:</strong> {harnessed}</p><p><strong>Harness check pass:</strong> {passed}</p><p>{thesis}</p></div>'


class Handler(BaseHTTPRequestHandler):
    def send_html(self, content, status=200):
        data = content.encode('utf-8')
        self.send_response(status)
        self.send_header('content-type', 'text/html; charset=utf-8')
        self.send_header('content-length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = self.path.split('?', 1)[0]
        if path == '/static/style.css':
            css = read(ROOT / 'app' / 'static' / 'style.css')
            self.send_response(200)
            self.send_header('content-type', 'text/css')
            self.end_headers()
            self.wfile.write(css.encode())
            return
        if path == '/static/htmx.min.js':
            js = read(ROOT / 'app' / 'static' / 'htmx.min.js')
            self.send_response(200)
            self.send_header('content-type', 'application/javascript')
            self.end_headers()
            self.wfile.write(js.encode())
            return
        if path == '/health':
            status = {'ok': True, 'pi': subprocess.run(['bash','-lc','command -v pi >/dev/null'], cwd=ROOT).returncode == 0}
            self.send_response(200)
            self.send_header('content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(status).encode())
            return
        if path == '/partial/health':
            pi_ok = subprocess.run(['bash','-lc','command -v pi >/dev/null'], cwd=ROOT).returncode == 0
            writable = os.access(ROOT / 'starter', os.W_OK)
            auth_modes = []
            if os.environ.get('OPENAI_API_KEY'):
                auth_modes.append('OPENAI_API_KEY present')
            if os.environ.get('ANTHROPIC_API_KEY'):
                auth_modes.append('ANTHROPIC_API_KEY present')
            if os.environ.get('OPENROUTER_API_KEY'):
                auth_modes.append('OPENROUTER_API_KEY present for OpenRouter lane')
            auth_hint = '; '.join(auth_modes) or 'Use /login, pass an OpenAI/Claude runtime key, or pass OPENROUTER_API_KEY for the free OpenRouter lane.'
            self.send_html(
                '<ul>'
                f'<li>Pi installed: {"✅" if pi_ok else "❌"}</li>'
                f'<li>Workspace writable: {"✅" if writable else "❌"}</li>'
                f'<li>Auth: {html.escape(auth_hint)}</li>'
                '</ul>'
            )
            return
        if path == '/artifact':
            qs = parse_qs(self.path.split('?',1)[1] if '?' in self.path else '')
            rel = qs.get('path', [''])[0]
            target = (ROOT / rel).resolve()
            if ROOT.resolve() not in target.parents and target != ROOT.resolve():
                self.send_html(page('Blocked', '<h1>Blocked path</h1>'), 403)
                return
            self.send_html(page(rel, f'<p><a href="/">← Home</a></p><pre>{html.escape(read(target, "Not found"))}</pre>'))
            return
        if path == '/solution':
            files = sorted((ROOT / 'solution').rglob('*')) if (ROOT / 'solution').exists() else []
            lis = ''.join(
                f'<li><a href="/artifact?path={html.escape(safe_rel(p))}">{html.escape(safe_rel(p))}</a></li>'
                for p in files if p.is_file() and p.stat().st_size < 200000
            )
            body = f'''<h1>Full solution folder</h1><p><a href="/">← Home</a></p>
<p>Spoiler zone: use this when stuck.</p>
<form method="post" action="/copy-solution" hx-post="/copy-solution" hx-target="#solution-copy" hx-swap="innerHTML"><button type="submit">Copy solution into starter workspace</button></form>
<div id="solution-copy"></div><ul>{lis}</ul>'''
            self.send_html(page('Solution', body))
            return
        if path == '/openrouter':
            guide = html.escape(read(ROOT / 'starter' / 'HUGGINGFACE-MODEL-SWAP.md', 'OpenRouter guide not found.'))
            pack_dir = ROOT / 'starter' / 'sources' / 'domain-packs'
            packs = sorted(pack_dir.glob('*.md')) if pack_dir.exists() else []
            lis = ''.join(
                f'<li><strong>{html.escape(pack.name)}</strong><pre>{html.escape(read(pack))}</pre></li>'
                for pack in packs
            )
            body = f'''<h1>OpenRouter / model swap</h1><p><a href="/">← Home</a></p>
<section class="card"><h2>Guide</h2><pre>{guide}</pre></section>
<section class="card"><h2>Domain specialization packs</h2><ul>{lis}</ul></section>'''
            self.send_html(page('OpenRouter / model swap', body))
            return
        if path == '/harness':
            policy = html.escape(read(ROOT / 'starter' / 'harness' / 'HARNESS-POLICY.md', 'Harness policy not found.'))
            report = html.escape(read(ROOT / 'starter' / 'outputs' / 'harness-report.json', 'Run the harnessed agent to generate a report.'))
            body = f'''<h1>Harness Lab</h1><p><a href="/">← Home</a></p>
<section class="card"><h2>Thesis</h2><p><strong>Prompts ask. Harnesses enforce.</strong> Run a loose agent, then run a harnessed agent with tool boundaries, evidence gates, and output validation.</p></section>
<section class="card"><h2>Run before/after</h2><form hx-post="/run" hx-target="#harness-result" hx-swap="innerHTML" hx-indicator="#harness-result-indicator"><button name="kind" value="unharnessed">Run loose agent</button><button name="kind" value="harnessed">Run harnessed agent</button><button name="kind" value="harness_compare">Build scorecard</button></form>{run_indicator('harness-result')}<div id="harness-result"></div></section>
<section class="card"><h2>Harness policy</h2><pre>{policy}</pre></section>
<section class="card"><h2>Harness delta scorecard</h2>{scorecard_html()}</section><section class="card"><h2>Latest harness report</h2><pre>{report}</pre></section>'''
            self.send_html(page('Harness Lab', body))
            return
        if path == '/compare':
            generic = html.escape(read(ROOT / 'starter' / 'outputs' / 'research-brief-generic.md', 'Generic output not created yet.'))
            unharnessed = html.escape(read(ROOT / 'starter' / 'outputs' / 'research-brief-unharnessed.md', 'Loose/unharnessed output not created yet.'))
            specialized = html.escape(read(ROOT / 'starter' / 'outputs' / 'research-brief-specialized.md', 'Specialized output not created yet.'))
            delta = html.escape(read(ROOT / 'starter' / 'outputs' / 'delta-notes.md', 'Delta notes not created yet.'))
            report = html.escape(read(ROOT / 'starter' / 'outputs' / 'harness-report.json', 'Harness report not created yet.'))
            body = f'<h1>Compare outputs</h1><p><a href="/">← Home</a></p><div class="grid"><section><h2>Loose / unharnessed</h2><pre>{unharnessed}</pre></section><section><h2>Harnessed specialist</h2><pre>{specialized}</pre></section></div><section class="card"><h2>Generic baseline</h2><pre>{generic}</pre></section><section class="card"><h2>Delta notes</h2><pre>{delta}</pre></section><section class="card"><h2>Harness delta scorecard</h2>{scorecard_html()}</section><section class="card"><h2>Harness report</h2><pre>{report}</pre></section>'
            self.send_html(page('Compare', body))
            return
        if path == '/traces':
            self.send_html(page('Tool traces', f'<h1>Tool traces</h1><p><a href="/">← Home</a></p>{traces_html()}'))
            return
        body = f'''
<h1>Pi Research Agent Workshop</h1>
<section class="card"><h2>1. Health</h2><div hx-get="/partial/health" hx-trigger="load" hx-swap="innerHTML">Checking…</div></section>
<section class="card"><h2>2. Choose your credential lane</h2><p><strong>No key?</strong> Click <strong>Use fallback sample outputs</strong> first so you can still complete the workshop discussion. Use the default Pi/OpenAI/Claude lane only if you have Pi login or an OpenAI/Claude runtime key. Use the OpenRouter lane if you passed <code>OPENROUTER_API_KEY</code>. OpenRouter browser buttons force an isolated OpenRouter runtime so saved Claude/OpenAI auth cannot silently take over. OpenRouter free models may hit minute limits, daily request limits, or 402 insufficient-credit errors; if that happens, the app copies fallback outputs and keeps the workshop moving. Restart Docker only if the UI or Docker CLI stops responding.</p>
<form hx-post="/run" hx-target="#run-result" hx-swap="innerHTML" hx-indicator="#run-result-indicator">
<button name="kind" value="fallback">No key required: use fallback sample outputs</button>
<button name="kind" value="generic_alt">Requires OpenRouter key: run generic agent</button>
<button name="kind" value="specialized_alt">Requires OpenRouter key: run specialized arXiv agent</button>
<button name="kind" value="specialized_alt_swap">Requires OpenRouter key: run specialist with second model</button>
<button name="kind" value="generic">Requires Pi/OpenAI/Claude login: run generic agent</button>
<button name="kind" value="specialized">Requires Pi/OpenAI/Claude login: run specialized arXiv agent</button>
</form>{run_indicator('run-result')}<div id="run-result"></div></section>
<section class="card"><h2>3. Example prompts</h2><p>Use these to understand the three workshop states before clicking the run buttons.</p>
<h3>Before specialization: generic baseline</h3><pre>Read AGENTS.md and inputs/generic-brief-request.md. Use sources/source-notes.md. Write outputs/research-brief-generic.md. Include source notes used, limitations, and open questions.</pre>
<h3>After specialization: tools + domain context</h3><pre>Use the arxiv-literature-scan and pdf-evidence-reader skills. Read sources/domain-packs/artificial-intelligence.md. Search arXiv, rank useful papers, read the best PDF if available, then write outputs/research-brief-specialized.md and outputs/delta-notes.md. Include evidence labels, provider/model used, risks, and open questions.</pre>
<h3>Harnessed: enforce and measure</h3><pre>Run the specialist research task under the harness policy. Use only allowed arXiv/evidence tools, write only approved output files, label evidence versus assumptions, run the harness check, and produce outputs/harness-report.json plus a short comparison against the generic baseline.</pre></section>
<section class="card"><h2>4. Harness lab</h2><p>Show why the agentic harness matters: loose prompt vs enforced policy + evidence gate.</p><a class="button" href="/harness">Open harness lab</a></section>
<section class="card"><h2>5. Model swap lane</h2><p>Swap OpenAI → OpenRouter, or OpenRouter model A → OpenRouter model B, then tighten the harness around model provenance.</p><a class="button" href="/openrouter">Open model swap lab</a></section>
<section class="card"><h2>6. Outputs</h2>{artifact_links()}<p><a class="button" href="/compare">Compare outputs</a> <a class="button" href="/traces">View tool traces</a></p></section>
<section class="card"><h2>7. If stuck</h2><a class="button" href="/solution">Peek at the full solution</a></section>
'''
        self.send_html(page('Pi Research Agent Workshop', body))

    def do_POST(self):
        if self.path.split('?', 1)[0] == '/copy-solution':
            dst = ROOT / 'starter'
            src = ROOT / 'solution'
            for item in src.iterdir():
                target = dst / item.name
                if item.is_dir():
                    if target.exists():
                        shutil.rmtree(target)
                    shutil.copytree(item, target)
                elif item.is_file():
                    shutil.copy2(item, target)
            self.send_html('<p>✅ Solution copied into starter workspace. You can now inspect or run it.</p>')
            return
        length = int(self.headers.get('content-length', '0'))
        form = parse_qs(self.rfile.read(length).decode())
        kind = form.get('kind', [''])[0]
        prompts = {
            'generic': 'Read the project instructions and generate the research brief requested in inputs/generic-brief-request.md. Use sources/source-notes.md. Write the result to outputs/research-brief-generic.md.',
            'generic_alt': f'Read AGENTS.md and inputs/generic-brief-request.md. Use sources/source-notes.md. Write outputs/research-brief-generic.md. Include provider/model used as openrouter / {ALT_BASELINE_MODEL}, source notes used, limitations, and open questions.',
            'specialized': 'Use the arxiv-literature-scan and pdf-evidence-reader skills. Identify a research keyword, search arXiv, rank results, read the best PDF if available, then write outputs/arxiv-ranked-results.json, outputs/pdf-evidence-notes.md, outputs/research-brief-specialized.md and outputs/delta-notes.md.',
            'specialized_alt': f'Use the arxiv-literature-scan and pdf-evidence-reader skills with openrouter / {ALT_BASELINE_MODEL}. Identify a research keyword, search arXiv, rank results, read the best PDF if available, then write outputs/arxiv-ranked-results.json, outputs/pdf-evidence-notes.md, outputs/research-brief-specialized.md and outputs/delta-notes.md. Include provider/model used, evidence labels, limitations, and open questions.',
            'specialized_alt_swap': f'Rerun the specialist brief with the same inputs and the Artificial Intelligence domain pack using openrouter / {ALT_SWAP_MODEL}. Write outputs/research-brief-specialized.md and outputs/delta-notes.md. Compare against the first model run. Include provider/model used, domain pack used, evidence labels, improvements, regressions, risks, and open questions. Run the harness check before completion.',
            'unharnessed': read(ROOT / 'starter' / 'prompts' / 'unharnessed-research-agent.md'),
            'harnessed': read(ROOT / 'starter' / 'prompts' / 'harnessed-research-agent.md'),
        }
        if kind == 'harness_compare':
            trace = ROOT / 'traces' / f'{int(time.time())}-harness-compare.log'
            trace.parent.mkdir(parents=True, exist_ok=True)
            proc = subprocess.run(['python3', 'tools/harness_compare.py'], text=True, cwd=ROOT / 'starter', capture_output=True, timeout=30)
            trace.write_text(proc.stdout + '\n--- STDERR ---\n' + proc.stderr, encoding='utf-8')
            safe = html.escape((proc.stdout + proc.stderr)[-4000:])
            self.send_html(f'<h3>Harness scorecard finished: exit {proc.returncode}</h3><pre>{safe}</pre><p><a href="/compare">Compare</a> · <a href="/harness">Harness lab</a></p>')
            return
        if kind == 'fallback':
            copied = copy_fallback_outputs()
            self.send_html(f'<h3>Fallback outputs copied.</h3><p>Copied {html.escape(", ".join(copied) or "no files")}.</p>{artifact_links()}')
            return
        prompt = prompts.get(kind)
        if not prompt:
            self.send_html('<p>Unknown run.</p>', 400)
            return
        if kind in {'generic_alt', 'specialized_alt', 'specialized_alt_swap'} and not openrouter_key():
            self.send_html(
                '<h3>OpenRouter key not detected.</h3>'
                '<p>Restart the container with <code>-e OPENROUTER_API_KEY="$OPENROUTER_API_KEY"</code>, '
                'or click <strong>No key required: use fallback sample outputs</strong>.</p>',
                400,
            )
            return
        trace = ROOT / 'traces' / f'{int(time.time())}-{kind}.log'
        trace.parent.mkdir(parents=True, exist_ok=True)
        started = time.time()
        if not RUN_LOCK.acquire(blocking=False):
            self.send_html('<h3>Another run is already in progress.</h3><p>Wait for the current run to finish, or click <strong>No key required: use fallback sample outputs</strong> if the workshop needs to move on now.</p>', 429)
            return
        try:
            cmd = ['pi', '-p']
            if kind == 'unharnessed':
                cmd = ['pi', '-p', '--no-extensions', '--no-skills']
            if kind == 'generic_alt':
                cmd = ['pi', '-p', '--provider', 'openrouter', '--model', ALT_BASELINE_MODEL]
            if kind == 'specialized_alt':
                cmd = ['pi', '-p', '--provider', 'openrouter', '--model', ALT_BASELINE_MODEL]
            if kind == 'specialized_alt_swap':
                cmd = ['pi', '-p', '--provider', 'openrouter', '--model', ALT_SWAP_MODEL]
            env = openrouter_env() if kind in {'generic_alt', 'specialized_alt', 'specialized_alt_swap'} else None
            proc = subprocess.run(cmd, input=prompt, text=True, cwd=ROOT / 'starter', capture_output=True, timeout=240, env=env)
            trace.write_text(proc.stdout + '\n--- STDERR ---\n' + proc.stderr, encoding='utf-8')
            combined = proc.stdout + proc.stderr
            safe = html.escape(combined[-4000:])
            hint = ''
            if kind in {'generic_alt', 'specialized_alt', 'specialized_alt_swap'} and is_openrouter_capacity_limited(combined):
                copied = copy_fallback_outputs()
                self.send_html(
                    '<h3>OpenRouter limit reached; fallback outputs copied.</h3>'
                    '<div class="card"><strong>OpenRouter limit guidance:</strong> Free OpenRouter models can hit minute limits, daily request limits, or 402 insufficient-credit errors. '
                    'Wait before trying the live model again, add a small credit balance if you need uninterrupted live calls, or continue the workshop with the fallback outputs below.</div>'
                    f'<p>Copied {html.escape(", ".join(copied) or "no files")}.</p>'
                    f'<pre>{safe}</pre><h4>Outputs</h4>{artifact_links()}'
                    '<p><a href="/compare">Compare</a> · <a href="/traces">Traces</a> · <a href="/harness">Harness lab</a></p>',
                    200,
                )
                return
            if kind in {'generic_alt', 'specialized_alt', 'specialized_alt_swap'} and ('401' in combined or 'Invalid username or password' in combined):
                hint = '<div class="card"><strong>OpenRouter auth hint:</strong> pass a valid OpenRouter API key as <code>-e OPENROUTER_API_KEY</code>. The Hugging Face <code>HF_TOKEN</code> will not work for this lane.</div>'
            if kind in {'generic_alt', 'specialized_alt', 'specialized_alt_swap'} and ('deprecated' in combined.lower() or 'model' in combined.lower() and '404' in combined):
                hint += f'<div class="card"><strong>OpenRouter model hint:</strong> free models can change. Relaunch with <code>-e ALT_SWAP_MODEL={html.escape(ALT_SWAP_MODEL)}</code> or use fallback outputs if a provider reports a deprecated/unavailable model.</div>'
            if kind == 'generic' and proc.returncode != 0 and os.environ.get('OPENROUTER_API_KEY') and not (os.environ.get('OPENAI_API_KEY') or os.environ.get('ANTHROPIC_API_KEY')):
                hint += '<div class="card"><strong>Credential lane hint:</strong> the default generic button does not use OpenRouter. With only <code>OPENROUTER_API_KEY</code>, use <strong>Run generic agent with OpenRouter</strong> instead.</div>'
            self.send_html(f'<h3>{html.escape(kind)} finished: exit {proc.returncode}, {time.time()-started:.1f}s</h3>{hint}<pre>{safe}</pre><h4>Outputs</h4>{artifact_links()}<p><a href="/compare">Compare</a> · <a href="/traces">Traces</a> · <a href="/harness">Harness lab</a></p>')
        except subprocess.TimeoutExpired:
            self.send_html('<h3>Run timed out.</h3><p>Use fallback outputs and keep moving. If the UI or Docker CLI stops responding, restart Docker Desktop/Engine, rerun the container, then continue from fallback or solution.</p>', 504)
        finally:
            RUN_LOCK.release()


if __name__ == '__main__':
    ThreadingHTTPServer(('0.0.0.0', PORT), Handler).serve_forever()
