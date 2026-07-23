import { createRequire } from "node:module";
import fs from "node:fs";
import path from "node:path";

const require = createRequire(import.meta.url);
const playwrightPath = (process.env.NODE_PATH || "").split(path.delimiter)
  .map((entry) => path.join(entry, "playwright"))
  .find(fs.existsSync) || "playwright";
const { chromium } = require(playwrightPath);
const candidates = [
  process.env.BOTJOBS_BROWSER_EXECUTABLE,
  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
].filter(Boolean);
const executablePath = candidates.find(fs.existsSync);

const [url, cvPath, letterPath, evidencePath, portal, profilePath, submitFlag, rawTimeout] = process.argv.slice(2);
const timeout = Number(rawTimeout || 30000);
let context;

const ADAPTERS = {
  linkedin: {
    hosts: ["linkedin.com"],
    apply: [/easy apply/i, /solicitud sencilla/i],
    submit: [/submit application/i, /enviar solicitud/i],
    success: ["application sent", "solicitud enviada"],
  },
  indeed: {
    hosts: ["indeed.com", "indeed.com.mx"],
    apply: [/apply now/i, /postúlate ahora/i, /postulate ahora/i],
    submit: [/submit your application/i, /enviar tu solicitud/i],
    success: ["application submitted", "solicitud enviada"],
  },
  occ: {
    hosts: ["occ.com.mx"],
    apply: [/postularme/i, /aplicar/i],
    submit: [/enviar postulación/i, /enviar postulacion/i],
    success: ["postulación enviada", "postulacion enviada"],
  },
  computrabajo: {
    hosts: ["computrabajo.com.mx"],
    apply: [/postularme/i, /aplicar/i],
    submit: [/enviar candidatura/i, /finalizar postulación/i],
    success: ["candidatura enviada", "postulación enviada"],
  },
  glassdoor: {
    hosts: ["glassdoor.com", "glassdoor.com.mx"],
    apply: [/easy apply/i, /apply now/i, /solicitud sencilla/i],
    submit: [/submit application/i, /enviar solicitud/i],
    success: ["application submitted", "solicitud enviada"],
  },
};

try {
  const adapter = ADAPTERS[portal];
  const hostname = new URL(url).hostname.toLowerCase();
  if (!adapter || !adapter.hosts.some((host) => hostname === host || hostname.endsWith(`.${host}`))) {
    throw new Error("Portal o dominio no soportado");
  }
  fs.mkdirSync(profilePath, { recursive: true });
  context = await chromium.launchPersistentContext(profilePath, {
    headless: true, locale: "es-MX", ...(executablePath ? { executablePath } : {}),
  });
  const page = context.pages()[0] || await context.newPage();
  page.setDefaultTimeout(timeout);
  await page.goto(url, { waitUntil: "domcontentloaded", timeout });
  await page.waitForTimeout(1000);

  const text = (await page.locator("body").innerText().catch(() => "")).toLowerCase();
  const barrier = [
    ["captcha", ["captcha", "verify you are human", "verifica que eres humano"]],
    ["login_requerido", ["sign in", "log in", "iniciar sesión", "iniciar sesion"]],
    ["bloqueado", ["access denied", "forbidden", "unusual traffic"]],
  ].find(([, patterns]) => patterns.some((pattern) => text.includes(pattern)))?.[0] || "";

  if (barrier) {
    console.log(JSON.stringify({ ok: false, estado: "requiere_intervencion", resultado: barrier }));
  } else {
    let applyClicked = false;
    for (const name of adapter.apply) {
      const button = page.getByRole("button", { name }).or(page.getByRole("link", { name })).first();
      if (await button.isVisible().catch(() => false)) {
        await button.click();
        applyClicked = true;
        await page.waitForTimeout(800);
        break;
      }
    }

    const fileInput = page.locator("input[type=file]").first();
    const hasFile = await fileInput.count() > 0;
    if (hasFile) await fileInput.setInputFiles(cvPath);

    const letter = fs.readFileSync(letterPath, "utf8");
    const textArea = page.locator("textarea").first();
    const hasText = await textArea.count() > 0;
    if (hasText) await textArea.fill(letter);

    fs.mkdirSync(path.dirname(evidencePath), { recursive: true });
    await page.screenshot({ path: evidencePath, fullPage: true });
    const missingRequired = await page.locator("input[required], textarea[required], select[required]").evaluateAll(
      (items) => items.filter((item) => !item.value && item.type !== "hidden" && item.type !== "file").length,
    ).catch(() => 0);
    const prepared = (hasFile || hasText || applyClicked) && missingRequired === 0;
    let state = prepared ? "preparada" : "requiere_intervencion";
    let result = prepared ? `Formulario preparado: CV=${hasFile}, carta=${hasText}` : `Campos obligatorios pendientes: ${missingRequired}`;
    let submitAttempted = false;

    if (prepared && submitFlag === "submit") {
      let submitted = false;
      for (const name of adapter.submit) {
        const button = page.getByRole("button", { name }).first();
        if (await button.isVisible().catch(() => false)) {
          await button.click();
          submitted = true;
          submitAttempted = true;
          await page.waitForTimeout(1500);
          break;
        }
      }
      const finalText = (await page.locator("body").innerText().catch(() => "")).toLowerCase();
      const confirmed = submitted && adapter.success.some((pattern) => finalText.includes(pattern));
      state = confirmed ? "aplicada" : "requiere_intervencion";
      result = confirmed ? "Portal confirmó el envío" : "No se pudo confirmar el envío";
    }
    console.log(JSON.stringify({
      ok: ["preparada", "aplicada"].includes(state),
      estado: state,
      resultado: result,
      evidencia: evidencePath,
      url_final: page.url(),
      submit_intentado: submitAttempted,
    }));
  }
} catch (error) {
  console.log(JSON.stringify({ ok: false, estado: "fallida", resultado: error.message }));
} finally {
  if (context) await context.close().catch(() => {});
}
