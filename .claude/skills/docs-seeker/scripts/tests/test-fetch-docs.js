#!/usr/bin/env node

/**
 * Tests for fetch-docs.js
 */

const http = require('http');
const path = require('path');
const { execFile } = require('child_process');
const { buildContext7Url, getUrlVariations, httpsGet, tryUrls } = require('../fetch-docs');

// Test counter
let passed = 0;
let failed = 0;

function assert(condition, message) {
  if (condition) {
    console.log(`✓ ${message}`);
    passed++;
  } else {
    console.error(`✗ ${message}`);
    failed++;
  }
}

function assertEqual(actual, expected, message) {
  if (actual === expected) {
    console.log(`✓ ${message}`);
    passed++;
  } else {
    console.error(`✗ ${message}`);
    console.error(`  Expected: ${expected}`);
    console.error(`  Actual: ${actual}`);
    failed++;
  }
}

console.log('Running fetch-docs.js tests...\n');

// Test buildContext7Url
console.log('## Testing buildContext7Url()');

assertEqual(
  buildContext7Url('vercel/next.js'),
  'https://context7.com/vercel/next.js/llms.txt',
  'Build URL for GitHub repo'
);

assertEqual(
  buildContext7Url('vercel/next.js', 'cache'),
  'https://context7.com/vercel/next.js/llms.txt?topic=cache',
  'Build URL with topic parameter'
);

assertEqual(
  buildContext7Url('shadcn-ui/ui', 'date'),
  'https://context7.com/shadcn-ui/ui/llms.txt?topic=date',
  'Build URL for shadcn with topic'
);

// Test getUrlVariations
console.log('\n## Testing getUrlVariations()');

async function testUrlVariations() {
  const urls1 = await getUrlVariations('next.js', 'cache');
  assert(urls1.length >= 2, 'Returns multiple URL variations with topic');
  assert(urls1[0].includes('?topic=cache'), 'First URL has topic parameter');
  assert(!urls1[1].includes('?topic='), 'Second URL has no topic parameter');

  const urls2 = await getUrlVariations('shadcn/ui');
  assert(urls2.length >= 1, 'Returns URL variations without topic');
  assert(!urls2[0].includes('?topic='), 'URL has no topic parameter');

  const urls3 = await getUrlVariations('astro', 'routing');
  assert(urls3.length >= 2, 'Returns variations for known library');
  assertEqual(urls3[0], 'https://context7.com/withastro/astro/llms.txt?topic=routing', 'Maps Astro correctly');
}

// Local servers only: no real network in these tests
function listen(server) {
  return new Promise((resolve) => server.listen(0, '127.0.0.1', () => resolve(server.address().port)));
}

async function getError(promise) {
  try {
    await promise;
    return null;
  } catch (error) {
    return error;
  }
}

async function testHttpsGet() {
  console.log('\n## Testing httpsGet()');
  // Arrange
  const server = http.createServer((req, res) => {
    if (req.url === '/ok') return res.end('# Docs\nhttps://ex.com/a');
    res.statusCode = req.url === '/500' ? 500 : 404;
    res.end('nope');
  });
  const base = `http://127.0.0.1:${await listen(server)}`;
  const closed = http.createServer();
  const closedPort = await listen(closed);
  await new Promise((resolve) => closed.close(resolve));

  // Act + Assert
  assertEqual(await httpsGet(`${base}/ok`), '# Docs\nhttps://ex.com/a', 'test_httpsGet_http200_returnsBody');
  assertEqual(await httpsGet(`${base}/missing`), null, 'test_httpsGet_http404_returnsNull');
  const err500 = await getError(httpsGet(`${base}/500`));
  assert(err500 && /HTTP 500/.test(err500.message), 'test_httpsGet_http500_throws');
  const errClosed = await getError(httpsGet(`http://127.0.0.1:${closedPort}/x`));
  assert(errClosed && /connect/i.test(errClosed.message), 'test_httpsGet_connectionRefused_throwsWithCause');
  server.close();
}

async function testHttpsGetProxy() {
  console.log('\n## Testing httpsGet() through HTTPS_PROXY');
  // Arrange: proxy that records CONNECT and refuses the tunnel
  const seen = [];
  const proxy = http.createServer();
  proxy.on('connect', (req, socket) => {
    seen.push(req.url);
    socket.end('HTTP/1.1 502 Bad Gateway\r\n\r\n');
  });
  const saved = { HTTPS_PROXY: process.env.HTTPS_PROXY, NO_PROXY: process.env.NO_PROXY, no_proxy: process.env.no_proxy };
  process.env.HTTPS_PROXY = `http://127.0.0.1:${await listen(proxy)}`;
  delete process.env.NO_PROXY;
  delete process.env.no_proxy;

  // Act
  const error = await getError(httpsGet('https://docs.example.test/llms.txt'));

  // Assert
  assertEqual(seen[0], 'docs.example.test:443', 'test_httpsGet_httpsProxySet_tunnelsThroughProxy');
  assert(error !== null, 'test_httpsGet_proxyRefusesTunnel_throws');
  for (const [key, value] of Object.entries(saved)) {
    if (value === undefined) delete process.env[key];
    else process.env[key] = value;
  }
  proxy.close();
}

async function testTryUrls() {
  console.log('\n## Testing tryUrls()');
  const urls = ['https://a/llms.txt?topic=x', 'https://a/llms.txt'];

  const found = await tryUrls(urls, async (url) => (url.includes('?topic=') ? null : 'docs'));
  assert(found.success && found.url === urls[1], 'test_tryUrls_topic404ThenBase200_returnsBase');

  const missing = await tryUrls(urls, async () => null);
  assertEqual(missing.error, 'Documentation not found on context7.com', 'test_tryUrls_all404_reportsNotFound');

  const offline = await tryUrls(urls, async () => { throw new Error('curl: (28) timed out'); });
  assertEqual(offline.error, 'network', 'test_tryUrls_networkFailure_reportsNetworkNotNotFound');
  assert(/timed out/.test(offline.message), 'test_tryUrls_networkFailure_keepsUnderlyingMessage');

  const mixed = await tryUrls(urls, async (url) => {
    if (url.includes('?topic=')) return null;
    throw new Error('HTTP 503: down');
  });
  assertEqual(mixed.error, 'network', 'test_tryUrls_404Then503_reportsNetwork');
}

function testCliExitCodeOnNetworkError() {
  console.log('\n## Testing CLI exit code on network error');
  return new Promise((resolve) => {
    // Arrange: dead proxy (closed port) so nothing leaves the machine
    const closed = http.createServer();
    closed.listen(0, '127.0.0.1', () => {
      const port = closed.address().port;
      closed.close(() => {
        const env = { ...process.env, HTTPS_PROXY: `http://127.0.0.1:${port}`, NO_PROXY: '', no_proxy: '' };
        // Act
        execFile('node', [path.join(__dirname, '..', 'fetch-docs.js'), 'documentation for next.js'], { env }, (error, stdout) => {
          // Assert
          const code = error ? error.code : 0;
          let result = {};
          try { result = JSON.parse(stdout); } catch (e) { /* asserted below */ }
          assertEqual(code, 2, 'test_fetchDocsCli_deadProxy_exits2');
          assertEqual(result.error, 'network', 'test_fetchDocsCli_deadProxy_outputsErrorNetwork');
          resolve();
        });
      });
    });
  });
}

testUrlVariations()
  .then(testHttpsGet)
  .then(testHttpsGetProxy)
  .then(testTryUrls)
  .then(testCliExitCodeOnNetworkError)
  .catch((error) => {
    console.error(`✗ Unexpected error: ${error.message}`);
    failed++;
  })
  .then(() => {
    // Summary
    console.log('\n## Test Summary');
    console.log(`Passed: ${passed}`);
    console.log(`Failed: ${failed}`);
    console.log(`Total: ${passed + failed}`);

    process.exit(failed > 0 ? 1 : 0);
  });
