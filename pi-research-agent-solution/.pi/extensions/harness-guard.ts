import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";
import { readFileSync, writeFileSync, mkdirSync, appendFileSync } from "node:fs";
import { resolve, relative, join } from "node:path";

const allowedWriteRoots = ["outputs", "listing", "harness"];

function log(event: unknown) {
  try {
    mkdirSync("outputs/traces", { recursive: true });
    appendFileSync("outputs/traces/harness-events.jsonl", JSON.stringify({ ts: Date.now(), ...event }) + "\n");
  } catch {}
}

function isInsideAllowed(pathValue: string): boolean {
  const cwd = process.cwd();
  const target = resolve(cwd, pathValue);
  return allowedWriteRoots.some((root) => {
    const rel = relative(resolve(cwd, root), target);
    return rel === "" || (!rel.startsWith("..") && !rel.startsWith("/"));
  });
}

function checkBrief(pathValue: string) {
  const text = readFileSync(pathValue, "utf8");
  const required = [
    "Executive summary",
    "Key findings",
    "Evidence notes",
    "Risks and uncertainties",
    "Recommended next action",
    "Open questions",
  ];
  const missingSections = required.filter((s) => !text.toLowerCase().includes(s.toLowerCase()));
  const hasEvidenceLabels = /participant|source notes|arxiv|pdf|abstract|assumption/i.test(text);
  const hasRiskBoundary = /human review|not final advice|uncertain|weak evidence|limitations|risk/i.test(text);
  const hasRecommendation = /recommend|next action|pilot|should/i.test(text);
  const hasModelProvenance = /provider\s*\/\s*model|model used|huggingface|openai|Qwen\/Qwen2\.5-7B-Instruct/i.test(text);
  const hasDomainPackProvenance = /domain pack|sources\/domain-packs|artificial-intelligence|blockchain-development|cloud-computing|database-development/i.test(text);
  const pass = missingSections.length === 0 && hasEvidenceLabels && hasRiskBoundary && hasRecommendation && hasModelProvenance && hasDomainPackProvenance;
  return {
    pass,
    missingSections,
    checks: {
      hasEvidenceLabels,
      hasRiskBoundary,
      hasRecommendation,
      hasModelProvenance,
      hasDomainPackProvenance,
    },
    policy: "harness/HARNESS-POLICY.md",
    modelSwapNote: "For Hugging Face/open-model runs, name the provider/model and domain pack so quality deltas are auditable.",
  };
}

export default function (pi: ExtensionAPI) {
  pi.on("tool_call", async (event: any) => {
    const toolName = event.toolName || event.name;
    const input = event.input || event.params || {};
    log({ kind: "tool_call", toolName, input });

    if (["write", "edit"].includes(toolName)) {
      const candidate = input.path || input.file || input.filePath;
      if (candidate && !isInsideAllowed(String(candidate))) {
        log({ kind: "blocked", reason: "write_outside_allowed_roots", candidate });
        return { block: true, reason: `Harness blocked write outside outputs/, listing/, or harness/: ${candidate}` };
      }
    }

    if (toolName === "bash") {
      const command = String(input.command || "");
      const dangerous = /rm\s+-rf|git\s+push\s+--force|sudo|mkfs|dd\s+if=|DROP\s+TABLE/i.test(command);
      if (dangerous) {
        log({ kind: "blocked", reason: "dangerous_shell", command });
        return { block: true, reason: "Harness blocked dangerous shell command." };
      }
      const network = /\b(curl|wget|fetch)\b/i.test(command);
      const arxiv = /arxiv\.org|export\.arxiv\.org|tools\/arxiv_search\.py|tools\/pdf_read\.py/.test(command);
      if (network && !arxiv) {
        log({ kind: "blocked", reason: "non_arxiv_network", command });
        return { block: true, reason: "Harness blocked non-arXiv network access for this lab." };
      }
    }
  });

  pi.registerTool({
    name: "harness_check_brief",
    label: "Harness Check Brief",
    description: "Validate a research brief against the workshop harness policy. Writes outputs/harness-report.json.",
    parameters: Type.Object({
      brief_path: Type.String({ description: "Path to markdown brief, usually outputs/research-brief-specialized.md" }),
    }),
    async execute(_toolCallId, params) {
      const report = checkBrief(params.brief_path);
      mkdirSync("outputs", { recursive: true });
      writeFileSync("outputs/harness-report.json", JSON.stringify(report, null, 2));
      log({ kind: "harness_check_brief", brief_path: params.brief_path, pass: report.pass });
      return {
        content: [{ type: "text", text: JSON.stringify(report, null, 2) }],
        details: { artifact: "outputs/harness-report.json", pass: report.pass },
      };
    },
  });
}
