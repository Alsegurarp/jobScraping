import { createRequire } from "node:module";
import fs from "node:fs";
import path from "node:path";

const require = createRequire(import.meta.url);
const nodePathParts = (process.env.NODE_PATH || "").split(path.delimiter).filter(Boolean);
const playwrightPath = nodePathParts
  .map((entry) => path.join(entry, "playwright"))
  .find((candidate) => fs.existsSync(candidate)) || "playwright";
const { chromium } = require(playwrightPath);

const BROWSER_CANDIDATES = [
  process.env.BOTJOBS_BROWSER_EXECUTABLE,
  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
  "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
  "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
].filter(Boolean);

function browserLaunchOptions() {
  const executablePath = BROWSER_CANDIDATES.find((candidate) => fs.existsSync(candidate));
  return executablePath ? { headless: true, executablePath } : { headless: true };
}

const BLOCK_PATTERNS = {
  captcha: ["captcha", "recaptcha", "verify you are human", "verifica que eres humano"],
  login_requerido: ["sign in", "iniciar sesion", "inicia sesion", "login", "log in"],
  bloqueado: ["access denied", "forbidden", "too many requests", "unusual traffic"],
};

function detectBlock(text) {
  const lower = (text || "").toLowerCase();
  for (const [status, patterns] of Object.entries(BLOCK_PATTERNS)) {
    if (patterns.some((pattern) => lower.includes(pattern))) {
      return status;
    }
  }
  return "";
}

async function meta(page, selector) {
  return await page.locator(selector).first().getAttribute("content").catch(() => "");
}

async function main() {
  const url = process.argv[2];
  const timeoutMs = Number(process.argv[3] || 30000);
  if (!url) {
    console.log(JSON.stringify({ ok: false, estado_extraccion: "sin_url", error: "Missing URL" }));
    return;
  }

  let browser;
  try {
    browser = await chromium.launch(browserLaunchOptions());
    const page = await browser.newPage({
      userAgent: "Mozilla/5.0 BotJobs browser extractor",
      locale: "es-MX",
    });
    page.setDefaultTimeout(timeoutMs);
    const response = await page.goto(url, { waitUntil: "domcontentloaded", timeout: timeoutMs });
    await page.waitForTimeout(1200);

    const title = await page.title().catch(() => "");
    const bodyText = await page.locator("body").innerText({ timeout: 5000 }).catch(() => "");
    const description =
      (await meta(page, "meta[name='description']")) ||
      (await meta(page, "meta[property='og:description']")) ||
      bodyText.slice(0, 5000);
    const emailMatch = bodyText.match(/[\w.+-]+@[\w-]+(?:\.[\w-]+)+/);
    const blockStatus = detectBlock(`${title}\n${description}\n${bodyText}`);

    console.log(JSON.stringify({
      ok: true,
      http_status: response ? response.status() : "",
      titulo: title,
      descripcion: description,
      email_contacto: emailMatch ? emailMatch[0] : "",
      estado_extraccion: blockStatus || (description ? "ok" : "sin_descripcion"),
      requiere_intervencion: ["captcha", "login_requerido", "bloqueado"].includes(blockStatus) ? "si" : "no",
    }));
  } catch (error) {
    console.log(JSON.stringify({
      ok: false,
      estado_extraccion: "error_navegador",
      requiere_intervencion: "no",
      error: error.message,
    }));
  } finally {
    if (browser) {
      await browser.close().catch(() => {});
    }
  }
}

await main();
