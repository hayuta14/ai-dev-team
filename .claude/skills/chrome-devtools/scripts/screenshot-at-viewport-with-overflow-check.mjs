#!/usr/bin/env node
/**
 * Full-page screenshot at a given viewport, plus a horizontal-overflow check.
 * Usage: node screenshot-at-viewport-with-overflow-check.mjs <url> <out.png> [width=360] [height=800]
 * Prints JSON: { out, viewport, scrollWidth, horizontalOverflow }.
 * scrollWidth is read from <html>, so content clipped by `body { overflow-x: hidden }` still counts.
 * Run `bash install.sh` in this directory first (installs puppeteer with its Chromium); node_modules lives
 * inside .claude/pack and is gone after each `avatar sync`.
 * Exit 0 = screenshot taken (read horizontalOverflow for the verdict), 2 = usage error, 1 = browser/navigation failure.
 * Verified 2026-10-19 with puppeteer 24.43.1: 500px div on a 360 viewport ⇒ scrollWidth 500, horizontalOverflow true
 * (also under body overflow-x hidden); same page at 1280 ⇒ false.
 */
import puppeteer from "puppeteer";

const [url, out, w = "360", h = "800"] = process.argv.slice(2);
if (!url || !out) {
  console.error("usage: node screenshot-at-viewport-with-overflow-check.mjs <url> <out.png> [width] [height]");
  process.exit(2);
}
const launch = { headless: true, args: ["--no-sandbox"] };
if (process.env.CHROME_PATH) launch.executablePath = process.env.CHROME_PATH;
const browser = await puppeteer.launch(launch);
try {
  const page = await browser.newPage();
  await page.setViewport({ width: Number(w), height: Number(h), deviceScaleFactor: 2 });
  await page.goto(url, { waitUntil: "networkidle0", timeout: 30000 });
  const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
  await page.screenshot({ path: out, fullPage: true });
  console.log(JSON.stringify({ out, viewport: Number(w), scrollWidth, horizontalOverflow: scrollWidth > Number(w) }));
} finally {
  await browser.close();
}
