import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";
import { spawn } from "node:child_process";
import { appendFileSync, mkdirSync } from "node:fs";
import { join } from "node:path";

function runScript(script: string, args: string[], cwd: string): Promise<string> {
  return new Promise((resolve, reject) => {
    const child = spawn("python3", [script, ...args], { cwd, env: process.env });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (d) => (stdout += d.toString()));
    child.stderr.on("data", (d) => (stderr += d.toString()));
    child.on("error", reject);
    child.on("close", (code) => {
      if (code === 0) resolve(stdout);
      else reject(new Error(stderr || stdout || `script exited ${code}`));
    });
  });
}

function trace(cwd: string, event: unknown) {
  try {
    const dir = join(cwd, "outputs", "traces");
    mkdirSync(dir, { recursive: true });
    appendFileSync(join(dir, "tool-calls.jsonl"), JSON.stringify({ ts: Date.now(), ...event }) + "\n");
  } catch {}
}

export default function (pi: ExtensionAPI) {
  pi.registerTool({
    name: "arxiv_search",
    label: "Search arXiv",
    description: "Search arXiv for papers matching a research keyword. Writes outputs/arxiv-results.json.",
    parameters: Type.Object({
      query: Type.String({ description: "Research keyword or phrase" }),
      max_results: Type.Optional(Type.Number({ description: "Max results, capped at 10" })),
      year_from: Type.Optional(Type.Number({ description: "Optional earliest submission year" })),
    }),
    async execute(_toolCallId, params, _signal, _onUpdate, ctx) {
      const cwd = process.cwd();
      const args = [params.query, "--max-results", String(params.max_results ?? 5)];
      if (params.year_from) args.push("--year-from", String(params.year_from));
      trace(cwd, { tool: "arxiv_search", params });
      const out = await runScript("tools/arxiv_search.py", args, cwd);
      return { content: [{ type: "text", text: out.slice(0, 12000) }], details: { artifact: "outputs/arxiv-results.json" } };
    },
  });

  pi.registerTool({
    name: "read_pdf",
    label: "Read PDF",
    description: "Read a local or arXiv PDF and write outputs/pdf-evidence-notes.md.",
    parameters: Type.Object({
      url_or_path: Type.String({ description: "arXiv PDF URL or local PDF path" }),
      max_pages: Type.Optional(Type.Number({ description: "Max pages, capped at 8" })),
    }),
    async execute(_toolCallId, params, _signal, _onUpdate, ctx) {
      const cwd = process.cwd();
      const args = [params.url_or_path, "--max-pages", String(params.max_pages ?? 3)];
      trace(cwd, { tool: "read_pdf", params: { ...params, url_or_path: String(params.url_or_path).replace(/code=[^&]+/, "code=<redacted>") } });
      const out = await runScript("tools/pdf_read.py", args, cwd);
      return { content: [{ type: "text", text: out.slice(0, 12000) }], details: { artifact: "outputs/pdf-evidence-notes.md" } };
    },
  });


  pi.registerTool({
    name: "rank_arxiv_results",
    label: "Rank arXiv Results",
    description: "Rank outputs/arxiv-results.json using a transparent workshop rubric. Writes outputs/arxiv-ranked-results.json.",
    parameters: Type.Object({
      criteria: Type.String({ description: "Ranking criteria or decision question" }),
    }),
    async execute(_toolCallId, params) {
      const cwd = process.cwd();
      trace(cwd, { tool: "rank_arxiv_results", params });
      const out = await runScript("tools/rank_papers.py", ["--criteria", params.criteria], cwd);
      return { content: [{ type: "text", text: out.slice(0, 12000) }], details: { artifact: "outputs/arxiv-ranked-results.json" } };
    },
  });

  pi.registerTool({
    name: "write_workshop_trace",
    label: "Write Workshop Trace",
    description: "Record a short workshop trace event for the browser UI.",
    parameters: Type.Object({
      event: Type.String(),
      note: Type.Optional(Type.String()),
    }),
    async execute(_toolCallId, params) {
      trace(process.cwd(), { tool: "write_workshop_trace", params });
      return { content: [{ type: "text", text: "Trace written to outputs/traces/tool-calls.jsonl" }], details: {} };
    },
  });
}
