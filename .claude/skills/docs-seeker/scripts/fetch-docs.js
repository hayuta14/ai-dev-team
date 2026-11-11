#!/usr/bin/env node

/**
 * Documentation Fetcher Script
 * Fetches documentation from context7.com with topic support and fallback chain
 */

const { execFile } = require('child_process');
const { loadEnv } = require('./utils/env-loader');
const { detectTopic } = require('./detect-topic');

// Load environment
const env = loadEnv();
const DEBUG = env.DEBUG === 'true';
const API_KEY = env.CONTEXT7_API_KEY;
const TIMEOUT_SECONDS = 15;

/**
 * Make HTTPS GET request via curl (honours HTTPS_PROXY/NO_PROXY, 15 s timeout).
 * The Authorization header goes through a curl config on stdin, never argv.
 * @param {string} url - URL to fetch
 * @returns {Promise<string|null>} Response body, or null on HTTP 404
 * @throws {Error} on connection/timeout/proxy errors and non-404 HTTP statuses
 */
function httpsGet(url) {
  return new Promise((resolve, reject) => {
    const fail = (message) => reject(new Error(message));
    const args = ['-q', '-sS', '--max-time', String(TIMEOUT_SECONDS), '-w', '\n%{http_code}', '-K', '-', url];
    const child = execFile('curl', args, { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 }, (error, stdout, stderr) => {
      if (error) {
        fail((stderr || '').trim() || error.message);
        return;
      }
      const cut = stdout.lastIndexOf('\n');
      const status = Number(stdout.slice(cut + 1));
      const data = stdout.slice(0, cut);
      if (status === 200) {
        resolve(data);
      } else if (status === 404) {
        resolve(null);
      } else {
        fail(`HTTP ${status}: ${data.slice(0, 200)}`);
      }
    });
    const header = API_KEY ? `Authorization: Bearer ${API_KEY}`.replace(/[\\"]/g, '\\$&') : '';
    child.stdin.on('error', () => {}); // curl may exit before reading stdin
    child.stdin.end(header ? `header = "${header}"\n` : '');
  });
}

/**
 * Construct context7.com URL
 * @param {string} library - Library name (e.g., "next.js", "shadcn/ui")
 * @param {string} topic - Optional topic keyword
 * @returns {string} context7.com URL
 */
function buildContext7Url(library, topic = null) {
  // Determine if GitHub repo or website
  let basePath;

  if (library.includes('/')) {
    // GitHub repo format: org/repo
    const [org, repo] = library.split('/');
    basePath = `${org}/${repo}`;
  } else {
    // Try common patterns
    const normalized = library.toLowerCase().replace(/[^a-z0-9-]/g, '');
    basePath = `websites/${normalized}`;
  }

  const baseUrl = `https://context7.com/${basePath}/llms.txt`;

  if (topic) {
    return `${baseUrl}?topic=${encodeURIComponent(topic)}`;
  }

  return baseUrl;
}

/**
 * Try multiple URL variations for a library
 * @param {string} library - Library name
 * @param {string} topic - Optional topic
 * @returns {Promise<Array>} Array of URLs to try
 */
async function getUrlVariations(library, topic = null) {
  const urls = [];

  // Known repo mappings
  const knownRepos = {
    'next.js': 'vercel/next.js',
    'nextjs': 'vercel/next.js',
    'remix': 'remix-run/remix',
    'astro': 'withastro/astro',
    'shadcn': 'shadcn-ui/ui',
    'shadcn/ui': 'shadcn-ui/ui',
    'better-auth': 'better-auth/better-auth',
  };

  const normalized = library.toLowerCase();
  const repo = knownRepos[normalized] || library;

  // Primary: Try with topic if available
  if (topic) {
    urls.push(buildContext7Url(repo, topic));
  }

  // Fallback: Try without topic
  urls.push(buildContext7Url(repo));

  return urls;
}

/**
 * Fetch documentation from context7.com
 * @param {string} query - User query
 * @returns {Promise<Object>} Documentation result
 */
async function fetchDocs(query) {
  const topicInfo = detectTopic(query);

  if (DEBUG) {
    console.error('[DEBUG] Topic detection result:', topicInfo);
  }

  let urls = [];

  if (topicInfo && topicInfo.isTopicSpecific) {
    // Topic-specific search
    urls = await getUrlVariations(topicInfo.library, topicInfo.topic);

    if (DEBUG) {
      console.error('[DEBUG] Topic-specific URLs:', urls);
    }
  } else {
    // Extract library from general query
    const libraryMatch = query.match(/(?:documentation|docs|guide) (?:for )?(.+)/i);
    if (libraryMatch) {
      const library = libraryMatch[1].trim();
      urls = await getUrlVariations(library);

      if (DEBUG) {
        console.error('[DEBUG] General library URLs:', urls);
      }
    }
  }

  return tryUrls(urls);
}

/**
 * Try URLs in order; 404 moves on, network errors are remembered
 * @param {Array<string>} urls - URLs to try
 * @param {Function} get - fetcher (url) => body | null, throws on network error
 * @returns {Promise<Object>} Documentation result
 */
async function tryUrls(urls, get = httpsGet) {
  const networkErrors = [];

  for (const url of urls) {
    if (DEBUG) {
      console.error(`[DEBUG] Trying URL: ${url}`);
    }

    try {
      const content = await get(url);

      if (content) {
        return {
          success: true,
          source: 'context7.com',
          url,
          content,
          topicSpecific: url.includes('?topic='),
        };
      }
    } catch (error) {
      networkErrors.push(`${url}: ${error.message}`);
      if (DEBUG) {
        console.error(`[DEBUG] Failed to fetch ${url}:`, error.message);
      }
    }
  }

  if (networkErrors.length > 0) {
    // Cannot tell whether the docs exist: do NOT report "not found"
    return {
      success: false,
      source: 'context7.com',
      error: 'network',
      message: networkErrors.join('; '),
      urls,
      suggestion: 'Check network/HTTPS_PROXY and retry; the library may still have llms.txt',
    };
  }

  // Every URL answered 404
  return {
    success: false,
    source: 'context7.com',
    error: 'Documentation not found on context7.com',
    urls,
    suggestion: 'Try repository analysis or web search',
  };
}

/**
 * CLI entry point
 */
async function main() {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.error('Usage: node fetch-docs.js "<user query>"');
    process.exit(1);
  }

  const query = args.join(' ');

  try {
    const result = await fetchDocs(query);
    console.log(JSON.stringify(result, null, 2));
    process.exit(result.success ? 0 : result.error === 'network' ? 2 : 1);
  } catch (error) {
    console.error('Error:', error.message);
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = {
  fetchDocs,
  buildContext7Url,
  getUrlVariations,
  httpsGet,
  tryUrls,
};
