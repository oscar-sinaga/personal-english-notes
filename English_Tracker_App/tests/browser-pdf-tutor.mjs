import assert from "node:assert/strict";
import { chromium } from "playwright";

const root = "http://127.0.0.1:8080/workspaces/english-notes/";
const andersonQuote = "Expected loss depends on PD, LGD, and EAD.";
const siddiqiQuote = "A score ranks applicants by their estimated risk.";
const browser = await chromium.launch({ args: ["--no-sandbox", "--disable-dev-shm-usage"] });
const button = (view, name) => view.getByRole("button", { name, exact: true });
const tutor = page => page.getByRole("region", { name: "Book tutor" });
const excerpt = page => tutor(page).getByLabel("Book excerpt");
const problems = [];

async function read(page) {
  page.setDefaultTimeout(15000);
  page.on("pageerror", error => problems.push(error.message));
  await page.goto(root);
  await button(page, "Read Book").click();
}

async function highlight(page, quote) {
  // Drive a real drag on the PDF.js text layer.
  const node = page.locator(".textLayer span").filter({ hasText: quote });
  await node.waitFor();
  const box = await node.boundingBox();
  await page.mouse.move(box.x + 1, box.y + box.height / 2);
  await page.mouse.down();
  await page.mouse.move(box.x + box.width + 2, box.y + box.height / 2, { steps: 14 });
  await page.mouse.up();
  await page.waitForFunction(() => document.querySelector(".study-actions button:last-child")?.disabled === false);
  assert.equal(await page.evaluate(() => window.getSelection().toString().trim()), quote);
}

async function checkExcerpt(page, book, number, text) {
  await excerpt(page).waitFor();
  assert.equal(await excerpt(page).inputValue(), text);
  assert.equal(await tutor(page).getByLabel("Book", { exact: true }).inputValue(), book);
  assert.equal(await tutor(page).getByLabel("PDF page").inputValue(), String(number));
}

try {
  const desktop = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await desktop.addInitScript(() => {
    // Exercise the native-viewer switch even on headless installations without a PDF plugin.
    Object.defineProperty(navigator, "pdfViewerEnabled", { value: true });
    const match = window.matchMedia.bind(window);
    window.matchMedia = query => query === "(any-hover: hover) and (any-pointer: fine)" ? { matches: true } : match(query);
  });
  let requests = 0;
  desktop.on("request", request => {
    if (request.method() === "POST" && request.url().endsWith("/tutor/excerpt")) requests++;
  });
  await read(desktop);
  await desktop.locator('iframe[title="Anderson PDF"]').waitFor();
  await button(desktop, "Study reader").click();
  await button(desktop, "Next").click();
  await highlight(desktop, andersonQuote);
  await button(desktop, "Ask tutor").click();
  await checkExcerpt(desktop, "anderson", 2, andersonQuote);
  assert.equal(requests, 0);
  const explain = button(tutor(desktop), "Explain excerpt");
  assert.equal(await explain.evaluate(el => document.activeElement === el), true);
  assert.ok((await explain.boundingBox()).height >= 44);
  assert.equal(await desktop.getByRole("region", { name: "Anderson reader" }).isVisible(), true);
  assert.equal(await button(desktop, "AI Assistant").evaluate(element => getComputedStyle(element.parentElement).position === "fixed"), false);
  const bookControl = await button(desktop, "Anderson PDF").boundingBox();
  const headerControl = await button(desktop, "Show header").boundingBox();
  assert.ok(Math.abs(bookControl.y - headerControl.y) < 12, "Desktop reader controls should fit on one row");
  if (process.env.UX_SCREENSHOTS) {
    await desktop.screenshot({ path: process.env.UX_SCREENSHOTS + "/after-desktop.png" });
  }
  await explain.click();
  await tutor(desktop).getByText("Anderson · PDF page 2").waitFor();
  assert.equal(requests, 1);

  const separator = desktop.getByRole("separator", { name: "Reading notes width" });
  await separator.focus();
  await desktop.keyboard.press("ArrowLeft");
  assert.equal(await separator.getAttribute("aria-valuenow"), "408");

  await button(desktop, "Siddiqi PDF").click();
  await highlight(desktop, siddiqiQuote);
  desktop.once("dialog", dialog => dialog.dismiss());
  await button(desktop, "Ask tutor").click();
  await checkExcerpt(desktop, "anderson", 2, andersonQuote);
  desktop.once("dialog", dialog => dialog.accept());
  await button(desktop, "Ask tutor").click();
  await checkExcerpt(desktop, "siddiqi", 1, siddiqiQuote);
  await button(desktop, "Full screen").click();
  await desktop.locator(".reader-expanded").waitFor();
  await highlight(desktop, siddiqiQuote);
  await button(desktop, "Ask tutor").click();
  await desktop.locator(".reader-expanded").waitFor({ state: "hidden" });
  await checkExcerpt(desktop, "siddiqi", 1, siddiqiQuote);
  await desktop.close();
  console.log("Desktop: viewer switch, real PDF selection, accurate reference, focus, draft protection and fullscreen handoff pass.");

  const phone = await browser.newPage({
    viewport: { width: 390, height: 844 },
    isMobile: true, hasTouch: true,
  });
  await read(phone);
  await button(phone, "Next").tap();
  const pageText = button(phone, "Page text");
  await phone.locator(".textLayer span").filter({ hasText: andersonQuote }).waitFor();
  await pageText.focus();
  await phone.keyboard.press("Enter");
  const dialog = phone.getByRole("dialog", { name: "PDF page 2 text" });
  const text = dialog.getByRole("textbox", { name: "Text from PDF page" });
  await text.waitFor();
  await phone.waitForFunction(() => document.activeElement?.getAttribute("aria-label") === "Text from PDF page");
  await phone.keyboard.press("Control+Home");
  for (const _ of andersonQuote) await phone.keyboard.press("Shift+ArrowRight");
  const selection = await text.evaluate(el => el.value.slice(el.selectionStart, el.selectionEnd));
  assert.equal(selection, andersonQuote);
  await phone.keyboard.press("Tab");
  assert.equal(await button(dialog, "Use selected text").evaluate(el => el === document.activeElement), true);
  await phone.keyboard.press("Enter");
  await checkExcerpt(phone, "anderson", 2, andersonQuote);
  assert.equal(await phone.getByRole("region", { name: "Anderson reader" }).isVisible(), false);
  assert.equal(await button(phone, "AI Assistant").evaluate(element => element.closest("nav") !== null), true);
  assert.equal(await phone.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
  if (process.env.UX_SCREENSHOTS) {
    await phone.screenshot({ path: process.env.UX_SCREENSHOTS + "/after-phone.png" });
  }
  await button(phone, "Back to PDF").tap();
  assert.equal(await phone.getByRole("spinbutton", { name: "Page number" }).inputValue(), "2");
  const phoneSentence = phone.locator(".textLayer span").filter({ hasText: andersonQuote });
  await phoneSentence.waitFor();
  await phoneSentence.evaluate(node => {
    window.getSelection().selectAllChildren(node);
  });
  await button(phone, "Ask tutor").tap();
  await checkExcerpt(phone, "anderson", 2, andersonQuote);
  await button(phone, "Back to PDF").tap();
  await button(phone, "Reading notes").tap();
  await checkExcerpt(phone, "anderson", 2, andersonQuote);
  await button(phone, "Back to PDF").tap();
  await button(phone, "Next").tap();
  await pageText.tap();
  await phone.getByText(/no selectable text/).waitFor();
  await button(phone.getByRole("dialog"), "Close").tap();
  assert.deepEqual(problems, []);
  console.log("Phone: keyboard selection, single-pane tutor, draft return, textless-page fallback and reflow pass.");
} finally {
  await browser.close();
}
