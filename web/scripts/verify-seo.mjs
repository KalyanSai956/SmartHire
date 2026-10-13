#!/usr/bin/env node
// Verifies SmartHire link-preview metadata.
//
//   Local build output:
//     node scripts/verify-seo.mjs --dist dist --site https://your-domain.tld
//   Live deployment (what crawlers actually receive):
//     node scripts/verify-seo.mjs --url https://your-domain.tld
//
// Exit code is 0 only when every check passes.

import fs from "node:fs";
import path from "node:path";
import { HOME_META, ROUTES, FALLBACK_META, SITE } from "../src/seo/routes.js";

const args = process.argv.slice(2);
const getArg = (name) => {
  const i = args.indexOf(name);
  return i === -1 ? undefined : args[i + 1] && !args[i + 1].startsWith("--") ? args[i + 1] : "";
};

const CRAWLERS = {
  WhatsApp: "WhatsApp/2.23.20 A",
  LinkedIn: "LinkedInBot/1.0 (compatible; Mozilla/5.0; Apache-HttpClient +http://www.linkedin.com)",
  Telegram: "TelegramBot (like TwitterBot)",
  Discord: "Mozilla/5.0 (compatible; Discordbot/2.0; +https://discordapp.com)",
  "X/Twitter": "Twitterbot/1.0",
  Facebook: "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)",
};

let failures = 0;
const pass = (label, detail = "") => console.log(`  PASS  ${label}${detail ? `  ${detail}` : ""}`);
const fail = (label, detail = "") => {
  failures += 1;
  console.log(`  FAIL  ${label}${detail ? `  ${detail}` : ""}`);
};
const check = (ok, label, detail) => (ok ? pass(label) : fail(label, detail));

function decode(s) {
  return s
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&amp;/g, "&");
}

function parseHead(html) {
  const head = html.split(/<\/head>/i)[0] || html;
  const attrsOf = (s) => {
    const out = {};
    for (const m of s.matchAll(/([a-zA-Z:_-]+)\s*=\s*"([^"]*)"/g)) out[m[1].toLowerCase()] = decode(m[2]);
    return out;
  };
  const meta = {};
  for (const m of head.matchAll(/<meta\s+([^>]*?)\/?>/gi)) {
    const a = attrsOf(m[1]);
    const key = a.property || a.name;
    if (key && a.content !== undefined) meta[key] = a.content;
  }
  const links = [...head.matchAll(/<link\s+([^>]*?)\/?>/gi)].map((m) => attrsOf(m[1]));
  const title = (head.match(/<title>([\s\S]*?)<\/title>/i) || [])[1];
  return {
    meta,
    title: title === undefined ? undefined : decode(title),
    canonical: links.find((l) => l.rel === "canonical")?.href,
  };
}

function pngSize(buf) {
  const sig = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
  if (buf.length < 24 || !buf.subarray(0, 8).equals(sig)) return null;
  return { width: buf.readUInt32BE(16), height: buf.readUInt32BE(20) };
}

function checkPage(html, { origin, route, expected, indexable }) {
  const { meta, title, canonical } = parseHead(html);
  const url = route == null ? undefined : `${origin}${route === "/" ? "/" : route}`;
  const image = `${origin}${SITE.image.path}`;

  check(title === expected.title, `<title> = "${expected.title}"`, `got "${title}"`);
  check(meta.description === expected.description, "meta description", `got "${meta.description}"`);
  check(meta["og:title"] === expected.title, "og:title", `got "${meta["og:title"]}"`);
  check(meta["og:description"] === expected.description, "og:description", `got "${meta["og:description"]}"`);
  check(meta["og:type"] === "website", "og:type = website", `got "${meta["og:type"]}"`);
  check(meta["og:site_name"] === SITE.name, `og:site_name = ${SITE.name}`, `got "${meta["og:site_name"]}"`);
  check(meta["og:locale"] === SITE.locale, `og:locale = ${SITE.locale}`, `got "${meta["og:locale"]}"`);
  check(meta["og:image"] === image, `og:image = ${image}`, `got "${meta["og:image"]}"`);
  check(meta["og:image:width"] === "1200" && meta["og:image:height"] === "630", "og:image width/height = 1200x630");
  check(meta["twitter:card"] === "summary_large_image", "twitter:card = summary_large_image", `got "${meta["twitter:card"]}"`);
  check(meta["twitter:image"] === image, "twitter:image", `got "${meta["twitter:image"]}"`);
  check(meta["twitter:title"] === expected.title, "twitter:title", `got "${meta["twitter:title"]}"`);
  if (url) {
    check(canonical === url, `canonical = ${url}`, `got "${canonical}"`);
    check(meta["og:url"] === url, `og:url = ${url}`, `got "${meta["og:url"]}"`);
  } else {
    check(canonical === undefined && meta["og:url"] === undefined, "no canonical / og:url on fallback page",
      `canonical="${canonical}" og:url="${meta["og:url"]}"`);
  }
  const robots = meta.robots || "";
  check(indexable ? !/noindex/i.test(robots) : /noindex/i.test(robots), indexable ? "robots allows indexing" : "robots = noindex", `got "${robots}"`);
  return meta;
}

async function verifyDist(dir, site) {
  const origin = new URL(site).origin;
  console.log(`\nVerifying build output in ${dir} against ${origin}`);
  const read = (f) => fs.readFileSync(path.join(dir, f), "utf8");

  console.log("\n[ / ]  dist/index.html");
  checkPage(read("index.html"), { origin, route: "/", expected: HOME_META, indexable: true });

  for (const [route, meta] of Object.entries(ROUTES)) {
    if (route === "/") continue;
    console.log(`\n[ ${route} ]  dist${route}/index.html`);
    checkPage(read(`${route.slice(1)}/index.html`), { origin, route, expected: meta, indexable: false });
  }

  console.log("\n[ fallback ]  dist/spa-fallback.html");
  checkPage(read("spa-fallback.html"), { origin, route: null, expected: FALLBACK_META, indexable: false });

  console.log(`\n[ image ]  dist${SITE.image.path}`);
  const buf = fs.readFileSync(path.join(dir, SITE.image.path));
  const size = pngSize(buf);
  check(size && size.width === 1200 && size.height === 630, "PNG is 1200x630", `got ${JSON.stringify(size)}`);
  check(buf.length < 600 * 1024, `file size ${(buf.length / 1024).toFixed(0)} KB (< 600 KB)`);
}

async function fetchText(url, ua) {
  const res = await fetch(url, { headers: { "user-agent": ua, accept: "text/html,*/*" }, redirect: "follow" });
  return { res, body: await res.text() };
}

async function verifyLive(site) {
  const origin = new URL(site).origin;
  check(origin.startsWith("https://"), "site uses HTTPS", origin);
  console.log(`\nVerifying LIVE site ${origin}`);

  let homeMeta;
  for (const [name, ua] of Object.entries(CRAWLERS)) {
    console.log(`\n[ / as ${name} ]`);
    const { res, body } = await fetchText(`${origin}/`, ua);
    check(res.status === 200, "HTTP 200", `got ${res.status}`);
    check((res.headers.get("content-type") || "").includes("text/html"), "content-type text/html", res.headers.get("content-type"));
    homeMeta = checkPage(body, { origin, route: "/", expected: HOME_META, indexable: true });
  }

  console.log("\n[ /jobs ]  must NOT carry homepage metadata");
  {
    const { res, body } = await fetchText(`${origin}/jobs`, CRAWLERS.LinkedIn);
    check(res.status === 200, "HTTP 200", `got ${res.status}`);
    checkPage(body, { origin, route: "/jobs", expected: ROUTES["/jobs"], indexable: false });
  }

  console.log("\n[ unknown URL ]  must serve neutral fallback, not homepage metadata");
  {
    const { body } = await fetchText(`${origin}/this-page-does-not-exist-${Date.now()}`, CRAWLERS.Facebook);
    checkPage(body, { origin, route: null, expected: FALLBACK_META, indexable: false });
  }

  console.log(`\n[ image ]  ${homeMeta?.["og:image"]}`);
  const imageUrl = homeMeta?.["og:image"] || `${origin}${SITE.image.path}`;
  check(imageUrl.startsWith("https://"), "og:image URL is absolute HTTPS", imageUrl);
  const res = await fetch(imageUrl, { headers: { "user-agent": CRAWLERS.Twitter ?? CRAWLERS["X/Twitter"] } });
  check(res.status === 200, "HTTP 200", `got ${res.status}`);
  const type = res.headers.get("content-type") || "";
  check(type.startsWith("image/png"), "content-type image/png", `got "${type}"`);
  const buf = Buffer.from(await res.arrayBuffer());
  const size = pngSize(buf);
  check(size && size.width === 1200 && size.height === 630, "decoded PNG is 1200x630", `got ${JSON.stringify(size)}`);
  check(buf.length < 600 * 1024, `size ${(buf.length / 1024).toFixed(0)} KB (< 600 KB, WhatsApp-safe)`);
}

async function main() {
  const dist = getArg("--dist");
  const url = getArg("--url");
  const site = getArg("--site");

  if (dist !== undefined) {
    if (!site) throw new Error("--dist requires --site https://your-domain.tld");
    await verifyDist(dist || "dist", site);
  } else if (url) {
    await verifyLive(url);
  } else {
    console.error("Usage:\n  node scripts/verify-seo.mjs --dist dist --site https://your-domain.tld\n  node scripts/verify-seo.mjs --url https://your-domain.tld");
    process.exit(2);
  }

  console.log(failures === 0 ? "\nAll checks passed." : `\n${failures} check(s) FAILED.`);
  process.exit(failures === 0 ? 0 : 1);
}

main().catch((err) => {
  console.error(`\nverify-seo error: ${err.message}`);
  process.exit(2);
});
