import { createRequire } from "node:module";
import fs from "node:fs";
import path from "node:path";

const require = createRequire(import.meta.url);
const playwrightPath = (process.env.NODE_PATH || "").split(path.delimiter)
  .map((entry) => path.join(entry, "playwright"))
  .find(fs.existsSync) || "playwright";
const { chromium } = require(playwrightPath);
const [portal, profilePath] = process.argv.slice(2);
const homes = {
  linkedin: "https://www.linkedin.com/login",
  indeed: "https://secure.indeed.com/auth",
  occ: "https://www.occ.com.mx/login",
  computrabajo: "https://www.computrabajo.com.mx/Acceso/",
  glassdoor: "https://www.glassdoor.com/profile/login_input.htm",
};
if (!homes[portal]) throw new Error("Portal no soportado");

fs.mkdirSync(profilePath, { recursive: true });
const context = await chromium.launchPersistentContext(profilePath, { headless: false });
const page = context.pages()[0] || await context.newPage();
await page.goto(homes[portal], { waitUntil: "domcontentloaded" });
console.log(`Sesion ${portal}: inicia sesion o resuelve la verificacion y cierra el navegador al terminar.`);
await new Promise((resolve) => context.on("close", resolve));
