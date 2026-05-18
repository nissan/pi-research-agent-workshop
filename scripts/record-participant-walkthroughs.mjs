#!/usr/bin/env node
import { chromium } from "playwright";
import fs from "node:fs/promises";
import path from "node:path";

const baseUrl = process.env.WORKSHOP_URL || "http://localhost:8787";
const outputDir = path.resolve("participant-share/media");
const viewport = { width: 1440, height: 1000 };

async function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function caption(page, text) {
  await page.evaluate((message) => {
    let el = document.querySelector("[data-recording-caption]");
    if (!el) {
      el = document.createElement("div");
      el.setAttribute("data-recording-caption", "true");
      Object.assign(el.style, {
        position: "fixed",
        left: "24px",
        right: "24px",
        bottom: "24px",
        zIndex: "99999",
        background: "rgba(17, 24, 39, 0.94)",
        color: "white",
        borderRadius: "12px",
        padding: "14px 18px",
        font: "600 20px/1.35 system-ui, -apple-system, Segoe UI, sans-serif",
        boxShadow: "0 12px 32px rgba(0,0,0,.25)",
      });
      document.body.appendChild(el);
    }
    el.textContent = message;
  }, text);
  await wait(1800);
}

async function start(browser, name) {
  const context = await browser.newContext({
    viewport,
    recordVideo: { dir: outputDir, size: viewport },
  });
  const page = await context.newPage();
  page.setDefaultTimeout(15000);
  return { context, page, name };
}

async function finish(session) {
  const video = session.page.video();
  await session.context.close();
  const src = await video.path();
  const dest = path.join(outputDir, session.name + ".webm");
  await fs.rename(src, dest);
  return dest;
}

async function record(name, fn) {
  const browser = await chromium.launch({ headless: true });
  const session = await start(browser, name);
  try {
    await fn(session.page);
    const file = await finish(session);
    console.log(name + ": " + file);
  } finally {
    await browser.close();
  }
}

async function main() {
  await fs.mkdir(outputDir, { recursive: true });

  await record("01-start-workshop-ui", async (page) => {
    await page.goto(baseUrl, { waitUntil: "networkidle" });
    await caption(page, "Step 1: start the Docker image, then open http://localhost:8787.");
    await page.locator("text=Health").scrollIntoViewIfNeeded();
    await caption(page, "The health panel confirms Pi is installed and tells you which credential lane is available.");
    await page.locator("text=Choose your credential lane").scrollIntoViewIfNeeded();
    await caption(page, "No key in this clean room: OpenRouter buttons are disabled, so fallback keeps the workshop moving.");
  });

  await record("02-fallback-and-outputs", async (page) => {
    await page.goto(baseUrl, { waitUntil: "networkidle" });
    await page.getByRole("button", { name: /use fallback sample outputs/i }).click();
    await page.waitForSelector("text=Fallback outputs copied");
    await caption(page, "Step 2: use fallback outputs when auth, rate limits, or setup would slow the room down.");
    await page.getByRole("heading", { name: "6. Outputs" }).scrollIntoViewIfNeeded();
    await caption(page, "The output list labels artifacts as fallback samples, so participants know what they are reading.");
    await page.getByRole("link", { name: /Compare outputs/i }).click();
    await page.waitForURL("**/compare");
    await caption(page, "Route changes preserve access to the generated or fallback outputs.");
  });

  await record("03-harness-lab", async (page) => {
    await page.goto(baseUrl + "/harness", { waitUntil: "networkidle" });
    await caption(page, "Step 3: the harness lab explains the core thesis: prompts ask, harnesses enforce.");
    await page.locator("text=Run before/after").scrollIntoViewIfNeeded();
    await caption(page, "Participants compare loose runs with harnessed runs when credentials are available.");
    await page.getByRole("button", { name: /Build scorecard/i }).click();
    await page.waitForSelector("text=Harness scorecard finished", { timeout: 20000 }).catch(() => {});
    await caption(page, "The scorecard area shows the comparison result or what still needs to be generated.");
  });

  await record("04-model-swap-domain-packs", async (page) => {
    await page.goto(baseUrl + "/openrouter", { waitUntil: "networkidle" });
    await caption(page, "Step 4: the model-swap page shows the OpenRouter lane and the default open models.");
    await page.locator("text=Domain specialization packs").scrollIntoViewIfNeeded();
    await caption(page, "Domain packs make the same agent more specific without changing the whole workshop structure.");
  });

  await record("05-solution-recovery", async (page) => {
    await page.goto(baseUrl + "/solution", { waitUntil: "networkidle" });
    await caption(page, "Step 5: the solution folder is a recovery path, not a failure state.");
    await page.getByRole("button", { name: /Copy solution into starter workspace/i }).click();
    await page.waitForSelector("text=Solution copied into starter workspace");
    await caption(page, "If someone gets blocked, copy the solution and keep the learning arc moving.");
  });
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
