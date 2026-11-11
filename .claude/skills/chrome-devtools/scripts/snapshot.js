#!/usr/bin/env node
/**
 * Get DOM snapshot with selectors
 * Usage: node snapshot.js [--url https://example.com] [--output snapshot.json]
 */
import { getBrowser, getPage, closeBrowser, parseArgs, outputJSON, outputError } from './lib/browser.js';
import fs from 'fs/promises';
import { buildElementSelector, snapshotValue } from './lib/selector.js';

/**
 * Runs inside the page: list interactive elements with metadata.
 * Lowercase tagName everywhere (filter with select(.tagName=="button")).
 */
function collectInteractiveElements(buildSelector, valueOf) {
  const interactiveSelectors = [
    'a[href]',
    'button',
    'input',
    'textarea',
    'select',
    '[onclick]',
    '[role="button"]',
    '[role="link"]',
    '[contenteditable]'
  ];

  const elements = [];
  const selector = interactiveSelectors.join(', ');
  const nodes = document.querySelectorAll(selector);

  nodes.forEach((el, index) => {
    const rect = el.getBoundingClientRect();

    elements.push({
      index: index,
      tagName: el.tagName.toLowerCase(),
      type: el.type || null,
      id: el.id || null,
      className: el.getAttribute('class') || null,
      name: el.name || null,
      value: valueOf(el),
      text: el.textContent?.trim().substring(0, 100) || null,
      href: el.href || null,
      selector: buildSelector(el, CSS.escape),
      xpath: getXPath(el),
      visible: rect.width > 0 && rect.height > 0,
      position: {
        x: rect.x,
        y: rect.y,
        width: rect.width,
        height: rect.height
      }
    });
  });

  function getXPath(element) {
    if (element.id) {
      return `//*[@id="${element.id}"]`;
    }
    if (element === document.body) {
      return '/html/body';
    }
    let ix = 0;
    const siblings = element.parentNode?.childNodes || [];
    for (let i = 0; i < siblings.length; i++) {
      const sibling = siblings[i];
      if (sibling === element) {
        return getXPath(element.parentNode) + '/' + element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
      }
      if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {
        ix++;
      }
    }
    return '';
  }

  return elements;
}

async function snapshot() {
  const args = parseArgs(process.argv.slice(2));

  try {
    const browser = await getBrowser({
      headless: args.headless !== 'false'
    });

    const page = await getPage(browser);

    // Navigate if URL provided
    if (args.url) {
      await page.goto(args.url, {
        waitUntil: args['wait-until'] || 'networkidle2'
      });
    }

    // Get interactive elements with metadata. Passed as a string expression so the
    // pure helpers from lib/selector.js can be injected into the page.
    const elements = await page.evaluate(
      `(${collectInteractiveElements})(${buildElementSelector}, ${snapshotValue})`
    );

    const result = {
      success: true,
      url: page.url(),
      title: await page.title(),
      elementCount: elements.length,
      elements: elements
    };

    if (args.output) {
      await fs.writeFile(args.output, JSON.stringify(result, null, 2));
      outputJSON({
        success: true,
        output: args.output,
        elementCount: elements.length
      });
    } else {
      outputJSON(result);
    }

    if (args.close !== 'false') {
      await closeBrowser();
    }
  } catch (error) {
    outputError(error);
  }
}

snapshot();
