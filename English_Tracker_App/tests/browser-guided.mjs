import assert from "node:assert/strict";
import { chromium } from "playwright";

const root = "http://127.0.0.1:8080/workspaces/english-notes/";
let browser;
const launch = () => chromium.launch({
  args: ["--no-sandbox", "--disable-dev-shm-usage", "--use-fake-device-for-media-stream", "--use-fake-ui-for-media-stream",
    "--autoplay-policy=no-user-gesture-required"],
});
const errors = [];

async function openPage({ mobile = false } = {}) {
  const context = await browser.newContext({
    viewport: mobile ? { width: 393, height: 852 } : { width: 1440, height: 950 },
    hasTouch: mobile,
    permissions: ["microphone"],
  });
  await context.addInitScript(({ mobile }) => {
    window.__speech = [];
    window.__tracks = [];
    const voice = { name: "English fixture", localService: true, lang: "en-US", voiceURI: "fixture" };
    const remote = { name: "Remote", localService: false, lang: "en-US", voiceURI: "remote" };
    Object.defineProperty(window, "speechSynthesis", {
      configurable: true,
      value: {
        getVoices: () => mobile ? [remote] : [remote, voice],
        addEventListener() {}, removeEventListener() {}, cancel() {},
        speak(utterance) {
          window.__speech.push({ text: utterance.text, rate: utterance.rate, local: utterance.voice.localService });
          setTimeout(() => {
            if (window.__failSpeech) utterance.onerror?.({ error: "synthesis-failed" });
            else utterance.onend?.();
          }, 20);
        },
      },
    });
    Object.defineProperty(window, "SpeechSynthesisUtterance", {
      configurable: true,
      value: class { constructor(text) { this.text = text; } },
    });
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { async writeText(text) { window.__clipboard = text; } },
    });
    if (mobile && navigator.mediaDevices) {
      navigator.mediaDevices.getUserMedia = async () => {
        throw new DOMException("Microphone permission denied", "NotAllowedError");
      };
    }
    if (!mobile) {
      class LocalRecognition {
        static available({ processLocally }) { return processLocally ? "available" : "unavailable"; }
        start(track) {
          if (!this.processLocally || track.kind !== "audio") throw new Error("Expected local audio track");
        }
        stop() {
          this.onresult?.({ results: [[{ transcript: "The credit team reviewed the default rate." }]] });
          this.onend?.();
        }
        abort() {}
      }
      LocalRecognition.prototype.processLocally = false;
      Object.defineProperty(window, "SpeechRecognition", { value: LocalRecognition, configurable: true });
      const getAudio = navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
      navigator.mediaDevices.getUserMedia = async options => {
        const stream = await getAudio(options);
        window.__tracks.push(...stream.getTracks());
        return stream;
      };
    }
  }, { mobile });
  const page = await context.newPage();
  page.setDefaultTimeout(15000);
  page.on("pageerror", error => errors.push(error.message));
  await page.goto(root);
  return page;
}

const button = (node, name) => node.getByRole("button", { name, exact: true });

async function record(page, node) {
  await button(node, "Record answer").click();
  const stop = node.getByRole("button", { name: /Stop recording/ });
  await stop.waitFor();
  await page.waitForFunction(() => window.__tracks.some(track => track.readyState === "live"));
  await page.waitForTimeout(650);
  await stop.click();
  await node.locator("audio").waitFor();
  await page.waitForFunction(() => window.__tracks.every(track => track.readyState === "ended"));
}

try {
  browser = await launch();
  const page = await openPage();
  await button(page, "Read Book").click();
  await button(page, "Reading notes").click();
  const reading = page.getByRole("region", { name: "Book tutor" });
  await reading.getByLabel("PDF page").fill("14");
  await reading.getByLabel("Book excerpt").fill("This is a synthetic passage about the probability of default.");
  await button(reading, "Copy prompt for Codex Voice").click();
  assert.match(await page.evaluate(() => window.__clipboard), /anderson, PDF page 14/);
  assert.match(await page.evaluate(() => window.__clipboard), /synthetic passage/);
  await button(reading, "Explain excerpt").click();
  await reading.getByText("Anderson · PDF page 14").waitFor();
  await reading.getByText("PD is the chance of default.").waitFor();
  await reading.getByLabel("Answer or transcript", { exact: true }).fill("PD means the probability of default.");
  await button(reading, "Get tutor feedback").click();
  await reading.getByText("You identified the main risk concept.").waitFor();
  await reading.getByLabel("Answer or transcript", { exact: true }).fill("PD is the chance of default.");
  await reading.getByText("You identified the main risk concept.").waitFor({ state: "hidden" });
  await button(reading, "Get tutor feedback").click();
  await reading.getByText("You identified the main risk concept.").waitFor();
  await button(reading, "Save to Practice Journal").click();
  await reading.getByText(/Saved to Practice Journal/).waitFor();
  await button(page, "Dashboard").click();

  await page.locator("#practice-skill").selectOption("Listening");
  const guide = page.getByRole("region", { name: "Guided practice" });
  await button(guide, "Generate exercise").click();
  await guide.getByText("What did the credit team review?").waitFor();
  assert.equal(await guide.getByText("The credit team reviewed the default rate before changing its policy.").count(), 0);
  await guide.getByLabel("Speed").selectOption("0.7");
  await page.evaluate(() => window.__failSpeech = true);
  await button(guide, "Play passage").click();
  await guide.getByText("Could not play audio with the selected device voice.").waitFor();
  assert.equal(await button(guide, "Read instead").isEnabled(), true);
  await page.evaluate(() => window.__failSpeech = false);
  await button(guide, "Play passage").click();
  assert.equal((await page.evaluate(() => window.__speech.at(-1))).rate, 0.7);
  assert.equal((await page.evaluate(() => window.__speech.at(-1))).local, true);
  assert.equal(await button(guide, "Reveal transcript").isDisabled(), true);
  const first = guide.locator("h5", { hasText: /^Attempt 1$/ }).locator("..");
  await record(page, first);
  assert.equal(await first.getByLabel("Answer or transcript", { exact: true }).inputValue(), "The credit team reviewed the default rate.");
  await button(first, "Get tutor feedback").click();
  await guide.getByText(/A manager checked the portfolio afterward/).waitFor();
  await guide.getByLabel("Replay").selectOption("1");
  await button(guide, "Play passage").click();
  assert.equal((await page.evaluate(() => window.__speech.at(-1))).text, "A manager checked the portfolio afterward.");
  await button(first, "Try again").click();
  const second = guide.locator("h5", { hasText: /^Attempt 2$/ }).locator("..");
  await record(page, second);
  await button(guide, "Save to Practice Journal").click();
  await guide.getByText(/Saved to Practice Journal/).waitFor();

  await button(page, "Practice Journal").click();
  const journal = page.getByRole("dialog", { name: "Practice journal" });
  const listeningEntry = journal.locator("article").filter({ hasText: /Listening · Study/ });
  await button(listeningEntry, "Study details").click();
  await journal.locator("audio").last().waitFor();
  assert.equal(await journal.locator("audio").count(), 2);
  const linked = await journal.locator("audio").evaluateAll(elements => elements.map(el => el.src));
  for (const url of linked) {
    const result = await page.request.get(url, { headers: { Range: "bytes=0-3" } });
    assert.equal(result.status(), 206);
    assert.equal((await result.body()).toString("hex"), "1a45dfa3");
  }
  await button(journal, "Back to journal").click();
  await button(listeningEntry, "Review now").click();
  assert.equal(await journal.locator("audio").count(), 0);
  await journal.getByLabel("Recall your answer before looking at the original").fill("They reviewed the default rate.");
  await button(journal, "Reveal previous feedback").click();
  await journal.locator("audio").last().waitFor();
  await button(journal, "I remembered").click();
  await journal.getByText(/Next review/).waitFor();
  await button(journal, "Close").click();

  await button(page, "Credit Risk Case Lab").click();
  await button(guide, "Open case").click();
  assert.equal(await guide.getByText(/Rp900,000/).count(), 0);
  await guide.getByLabel("Answer or transcript", { exact: true }).fill("Borrower B has a higher expected loss.");
  await button(guide, "Get tutor feedback").click();
  await guide.getByText("Case reasoning").click();
  await guide.getByText(/Rp900,000/).waitFor();
  await button(guide, "Save to Practice Journal").click();
  await guide.getByText(/Saved to Practice Journal/).waitFor();

  await guide.getByLabel("Exercise mode").selectOption("roleplay");
  await guide.getByLabel("Tutor role").selectOption("senior-analyst");
  await button(guide, "Generate exercise").click();
  await guide.getByText("How would you explain PD to a colleague?").waitFor();
  await guide.getByLabel("Answer or transcript", { exact: true }).fill("PD is the probability of default.");
  await button(guide, "Get tutor feedback").click();
  await button(guide, "Save to Practice Journal").click();
  await guide.getByText(/Saved to Practice Journal/).waitFor();
  await button(guide, "Continue role-play").click();
  await guide.getByText("How would you explain LGD?").waitFor();
  await page.context().close();
  console.log("Desktop: excerpt, device recorder, two saved takes, review, case and role-play pass");

  await browser.close();
  browser = await launch();
  const phone = await openPage({ mobile: true });
  await phone.locator("#practice-skill").selectOption("Speaking");
  const mobile = phone.getByRole("region", { name: "Guided practice" });
  await mobile.getByLabel("Exercise mode").selectOption("shadowing");
  await button(mobile, "Generate exercise").click();
  await mobile.getByText("Repeat the model sentence aloud.").waitFor();
  await button(mobile, "Play model sentence").click();
  await mobile.getByText("An English voice is unavailable on this device.").waitFor();
  await button(mobile, "Record answer").click();
  await mobile.getByText(/Allow microphone access to record/).waitFor();
  await mobile.getByLabel("Answer or transcript", { exact: true }).fill("The analyst explained the credit score in plain English.");
  await button(mobile, "Get tutor feedback").click();
  await mobile.getByText("Wording", { exact: true }).waitFor();
  await button(mobile, "Save to Practice Journal").click();
  await mobile.getByText(/Saved to Practice Journal/).waitFor();
  assert.equal(await phone.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
  assert.deepEqual(errors, []);
  console.log("Mobile viewport: guided mode, no-device-voice recovery, typed shadowing and save pass");
} finally {
  await browser?.close();
}
