import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { chromium } from "playwright";

const root = "http://127.0.0.1:8080/workspaces/english-notes/";
const browser = await chromium.launch({ args: ["--no-sandbox", "--disable-dev-shm-usage"] });
const button = (view, name) => view.getByRole("button", { name, exact: true });
const axePath = process.env.CHECK_A11Y ? createRequire(import.meta.url).resolve("axe-core") : undefined;
const time = new Date("2026-11-27T08:00:00Z");
const problems = [];

async function openPage(width, height, mobile = false) {
  const page = await browser.newPage({ viewport: { width, height }, hasTouch: mobile, isMobile: mobile });
  page.setDefaultTimeout(15000);
  await page.clock.install({ time });
  page.on("pageerror", error => problems.push(error.message));
  await page.goto(root);
  await page.getByRole("heading", { name: "Practice Editor" }).waitFor();
  return page;
}

async function audit(page, label) {
  if (!axePath) return;
  if (!await page.evaluate(() => Boolean(window.axe))) await page.addScriptTag({ path: axePath });
  const report = await page.evaluate(async () => {
    const result = await window.axe.run({
      runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"] },
    });
    return {
      violations: result.violations.map(item => ({ id: item.id, targets: item.nodes.map(node => node.target) })),
      checks: result.passes.length,
      needsManualCheck: result.incomplete.map(item => ({ id: item.id, targets: item.nodes.map(node => node.target) })),
    };
  });
  assert.deepEqual(report.violations, [], label + " accessibility findings: " + JSON.stringify(report.violations));
  console.log(label + ": " + report.checks + " automated accessibility checks, manual checks " + JSON.stringify(report.needsManualCheck));
}

async function checkDailyContrast(page) {
  const weakest = await page.locator(".daily-practice").evaluate(card => {
    const canvas = document.createElement("canvas");
    canvas.width = canvas.height = 1;
    const context = canvas.getContext("2d", { willReadFrequently: true });
    const luminance = color => {
      context.clearRect(0, 0, 1, 1);
      context.fillStyle = color;
      context.fillRect(0, 0, 1, 1);
      const values = Array.from(context.getImageData(0, 0, 1, 1).data).slice(0, 3);
      const linear = values.map(value => {
        const srgb = value / 255;
        return srgb < 0.04045 ? srgb / 12.92 : ((srgb + 0.055) / 1.055) ** 2.4;
      });
      return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2];
    };
    const panel = getComputedStyle(card);
    const stops = panel.backgroundImage.match(/rgb\([^)]+\)/g) || [];
    const background = Math.max(...[panel.backgroundColor, ...stops].map(luminance));
    return Math.min(...[...card.querySelectorAll("h2, h3, .text-slate-400, .text-slate-200")]
      .map(text => (luminance(getComputedStyle(text).color) + 0.05) / (background + 0.05)));
  });
  assert.ok(weakest >= 4.5, "Daily exercise text contrast ratio " + weakest.toFixed(2));
  console.log("Daily exercise worst-case text contrast " + weakest.toFixed(2) + ":1");
}

async function screenshot(page, name) {
  if (process.env.UX_SCREENSHOTS) await page.screenshot({ path: process.env.UX_SCREENSHOTS + "/" + name + ".png" });
}

async function verifyLayout(page) {
  const clock = page.getByRole("timer", { name: "Time remaining" });
  assert.equal(await clock.count(), 1);
  assert.equal(await clock.textContent(), "20:00");
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
  const navAssistant = button(page.getByRole("navigation"), "AI Assistant");
  const launcher = await navAssistant.evaluate(element => {
    const style = getComputedStyle(element);
    const bounds = element.getBoundingClientRect();
    return { position: style.position, height: bounds.height };
  });
  assert.notEqual(launcher.position, "fixed");
  assert.ok(launcher.height >= 44);
  const start = button(page, "Start today’s practice");
  const bounds = await start.boundingBox();
  assert.ok(bounds.height >= 44 && bounds.y + bounds.height <= page.viewportSize().height);
  const editor = page.getByRole("group", { name: "Practice skill" });
  assert.ok((await button(editor, "Speaking").boundingBox()).width >= 44);
  assert.ok((await button(editor, "Listening").boundingBox()).height >= 44);
}

try {
  const desktop = await openPage(1440, 900);
  await verifyLayout(desktop);
  await audit(desktop, "Desktop dashboard");
  await checkDailyContrast(desktop);
  await screenshot(desktop, "studio-desktop");

  await button(desktop, "Start today’s practice").click();
  const answer = desktop.getByLabel("Original response or transcript");
  assert.equal(await answer.evaluate(element => element === document.activeElement), true);
  assert.ok((await desktop.getByLabel("Exercise prompt").inputValue()).length > 40);
  await answer.fill("Ask for the updated cash flow forecast before making a decision.");
  await button(desktop, "Save practice").click();
  await desktop.getByText("Draft saved.", { exact: true }).waitFor();

  const journalTrigger = button(desktop, "Practice Journal");
  await journalTrigger.click();
  const journal = desktop.getByRole("dialog", { name: "Practice journal" });
  await journal.getByText(/updated cash flow forecast/).waitFor();
  await audit(desktop, "Practice journal");
  await journal.getByLabel("Search topic, notes, or feedback").fill("no such entry");
  await button(journal, "Search").click();
  await journal.getByText("No practice matches these filters.").waitFor();
  await button(journal, "Clear search and filters").click();
  await journal.getByText(/updated cash flow forecast/).waitFor();
  await button(journal, "Open entry").click();
  await journal.waitFor({ state: "hidden" });
  await desktop.waitForFunction(() => document.activeElement?.id === "content");

  const timerOptions = button(desktop, "Timer options");
  await timerOptions.click();
  const timer = desktop.getByRole("dialog", { name: "Study timer" });
  assert.equal(await button(timer, "Stop & Save").isDisabled(), true);
  await timer.getByLabel("Duration in minutes").fill("1");
  await button(timer, "Set duration").click();
  await button(timer, "Next Stage").press("Enter");
  await timer.getByText("Stage · Thinking & Circumlocution", { exact: true }).waitFor();
  await button(timer, "Reset timer").click();
  await audit(desktop, "Study timer");
  await desktop.keyboard.press("Escape");
  await timer.waitFor({ state: "hidden" });
  assert.equal(await timerOptions.evaluate(element => element === document.activeElement), true);

  const start = button(desktop.getByRole("group", { name: "Study timer" }), "Start");
  await start.click();
  await desktop.clock.fastForward(2000);
  const clock = desktop.getByRole("timer", { name: "Time remaining" });
  await desktop.waitForFunction(() => /\b00:5\d\b/.test(document.querySelector('[role="timer"]').textContent));
  await button(desktop, "Pause").click();
  const paused = await clock.textContent();
  await desktop.clock.fastForward(8000);
  assert.equal(await clock.textContent(), paused);
  await button(desktop, "Resume").click();
  await desktop.clock.fastForward(62000);
  await desktop.getByText("Saved 1 min of study time.").waitFor();
  assert.equal(await clock.textContent(), "01:00");

  let configured = { provider: "codex", model: "codex-fixture" };
  await desktop.route("**/api/ai/preferences*", async route => {
    if (route.request().method() === "PUT") {
      configured = route.request().postDataJSON();
      await route.fulfill({ json: configured });
    } else {
      const provider = new URL(route.request().url()).searchParams.get("provider") || configured.provider;
      await route.fulfill({ json: { active: configured, models: [provider + "-fixture"] } });
    }
  });
  await desktop.route("**/api/chat", route => route.fulfill({
    contentType: "text/plain", body: "PD estimates the chance that a borrower will default.",
  }));
  const assistantTrigger = button(desktop, "AI Assistant");
  await assistantTrigger.click();
  const assistant = desktop.getByRole("dialog", { name: "English AI Assistant" });
  await button(assistant, "AI settings").click();
  await assistant.getByLabel("AI provider").selectOption("claude");
  await button(assistant, "Save AI preferences").click();
  await assistant.getByText("AI preferences saved.", { exact: true }).waitFor();
  assert.deepEqual(configured, { provider: "claude", model: "claude-fixture" });
  await assistant.getByLabel("Message").fill("What is PD?");
  await button(assistant, "Send").click();
  await assistant.getByText("PD estimates the chance that a borrower will default.").waitFor();
  await audit(desktop, "AI assistant");
  await button(assistant, "History").click();
  const history = desktop.getByRole("dialog", { name: "AI history" });
  await history.getByText("No matching interactions.").waitFor();
  await desktop.keyboard.press("Escape");
  await history.waitFor({ state: "hidden" });
  assert.equal(await button(assistant, "History").evaluate(element => element === document.activeElement), true);
  await desktop.keyboard.press("Escape");
  await assistant.waitFor({ state: "hidden" });
  assert.equal(await assistantTrigger.evaluate(element => element === document.activeElement), true);

  const resources = desktop.getByRole("complementary", { name: "Study resources" });
  await resources.getByText("Course syllabus", { exact: true }).click();
  await button(resources, "1: Credit Intelligence").click();
  const progress = resources.getByRole("checkbox", { name: "1.1 Debt versus Credit" });
  await progress.check();
  await desktop.waitForFunction(async () => {
    const result = await fetch("./api/progress");
    return (await result.json()).some(item => item.module_name === "1.1 Debt versus Credit" && item.is_completed);
  });
  await resources.getByText(/Technical lexicon/).click();
  await resources.getByLabel("Term", { exact: true }).fill("EAD");
  await resources.getByLabel("Definition", { exact: true }).fill("Exposure at default.");
  await button(resources, "Save term").click();
  await resources.getByText("Exposure at default.", { exact: true }).waitFor();

  await button(desktop, "Read Book").click();
  const studyReader = button(desktop, "Study reader");
  if (await studyReader.isVisible()) await studyReader.click();
  await desktop.locator(".pdf-sheet:not(.invisible) .textLayer span").first().waitFor();
  await audit(desktop, "PDF reader");
  await button(desktop, "Reading notes").click();
  const companion = desktop.getByRole("region", { name: "Reading Companion" });
  await companion.getByText("Other reading tools", { exact: true }).click();
  await audit(desktop, "Reading companion");
  await desktop.close();

  for (const [width, height, mobile] of [[1024, 768, false], [768, 950, false], [390, 844, true], [320, 700, true]]) {
    const page = await openPage(width, height, mobile);
    await verifyLayout(page);
    if (width === 390) {
      await audit(page, "Phone dashboard");
      await screenshot(page, "studio-phone");
      const editor = page.getByRole("group", { name: "Practice skill" });
      await button(editor, "Speaking").tap();
      await page.getByRole("region", { name: "Guided practice" }).waitFor();
      assert.equal(await button(editor, "Speaking").getAttribute("aria-pressed"), "true");
      const speaking = page.getByRole("heading", { name: "Speaking", exact: true });
      assert.equal(await speaking.evaluate(element => element === document.activeElement), true);
      await audit(page, "Phone speaking");
      await screenshot(page, "studio-phone-speaking");
      await button(page, "AI Assistant").tap();
      await screenshot(page, "studio-phone-assistant");
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    }
    await page.close();
  }
  assert.deepEqual(problems, []);
  console.log("Dashboard, timer, journal, provider settings and study resources pass; layout verified at 320–1440px.");
} finally {
  await browser.close();
}
