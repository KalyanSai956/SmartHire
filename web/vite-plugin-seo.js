// Build-time SEO / link-preview plugin for SmartHire.
//
// Why this exists: the app is a client-rendered SPA, so index.html used to be
// an empty shell. Link-preview crawlers (WhatsApp, LinkedIn, Telegram, Discord,
// Facebook, X) do not execute JavaScript, so they never saw any metadata.
//
// What it does (no headless browser, no SSR server needed - Vercel just serves
// static files):
//   1. Injects the homepage <title>, description, canonical, Open Graph and
//      Twitter tags into index.html (served for "/").
//   2. After the build, emits one static HTML file per known route
//      (dist/jobs/index.html, dist/resources/index.html, ...) with that
//      route's own metadata. Vercel serves real files before applying rewrites.
//   3. Emits dist/spa-fallback.html with neutral default metadata. vercel.json
//      rewrites every unknown URL (404s, /analysis/:id) to this file, so the
//      homepage metadata is never served for other URLs.
//
// The production origin is NEVER hard-coded. It comes from, in order:
//   VITE_SITE_URL                   (Vercel env var, shell env var or .env file)
//   VERCEL_PROJECT_PRODUCTION_URL   (set automatically by Vercel at build time)
// A production build fails with a clear message if neither is available.

import fs from "node:fs";
import path from "node:path";
import { HOME_META, ROUTES, FALLBACK_META } from "./src/seo/routes.js";
import { buildHeadEntries, serializeHead } from "./src/seo/head.js";

const MARKER = "<!-- seo:meta -->";
const START = "<!-- seo:start -->";
const END = "<!-- seo:end -->";
const DEV_FALLBACK_ORIGIN = "http://localhost:5173";

export function resolveSiteUrl(env, { required }) {
  const explicit = (env.VITE_SITE_URL || "").trim();
  const vercel = (env.VERCEL_PROJECT_PRODUCTION_URL || "").trim();
  const raw = explicit || (vercel ? `https://${vercel}` : "");

  if (!raw) {
    if (!required) return DEV_FALLBACK_ORIGIN;
    throw new Error(
      "[seo] Production site URL is not set. Set VITE_SITE_URL to your real " +
        "production origin (for example https://your-domain.tld) in the Vercel " +
        "project's Environment Variables, or in a local .env file, then rebuild.",
    );
  }

  let url;
  try {
    url = new URL(raw);
  } catch {
    throw new Error(`[seo] VITE_SITE_URL is not a valid URL: "${raw}"`);
  }
  if (url.pathname !== "/" || url.search || url.hash) {
    throw new Error(
      `[seo] VITE_SITE_URL must be an origin only (no path, query or hash): "${raw}"`,
    );
  }
  if (required && url.protocol !== "https:") {
    throw new Error(`[seo] VITE_SITE_URL must use https:// in production: "${raw}"`);
  }
  return url.origin;
}

function withSeoBlock(html, entries) {
  const block = `${START}\n${serializeHead(entries)}\n    ${END}`;
  const pattern = new RegExp(`${START}[\\s\\S]*?${END}`);
  if (!pattern.test(html)) {
    throw new Error("[seo] seo:start/seo:end block not found in built index.html");
  }
  return html.replace(pattern, () => block);
}

/** Writes per-route static pages next to dist/index.html. Exported for tests. */
export function emitSeoPages({ outDir, siteUrl }) {
  const indexPath = path.join(outDir, "index.html");
  const indexHtml = fs.readFileSync(indexPath, "utf8");
  const written = [];

  for (const [route, meta] of Object.entries(ROUTES)) {
    if (route === "/") continue;
    const html = withSeoBlock(indexHtml, buildHeadEntries(meta, { siteUrl, pathname: route }));
    const file = path.join(outDir, route.slice(1), "index.html");
    fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.writeFileSync(file, html);
    written.push(path.relative(outDir, file));
  }

  const fallbackHtml = withSeoBlock(
    indexHtml,
    buildHeadEntries(FALLBACK_META, { siteUrl, pathname: null }),
  );
  fs.writeFileSync(path.join(outDir, "spa-fallback.html"), fallbackHtml);
  written.push("spa-fallback.html");
  return written;
}

export default function seoPlugin(options = {}) {
  let siteUrl = DEV_FALLBACK_ORIGIN;
  let outDir = "";
  let isBuild = false;

  return {
    name: "smarthire-seo",

    async config(userConfig, { command, mode }) {
      isBuild = command === "build";
      const loadEnv = options.loadEnv ?? (await import("vite")).loadEnv;
      const fileEnv = loadEnv(mode, userConfig.root ?? process.cwd(), "VITE_");
      // Real environment (Vercel dashboard / shell) wins over .env files.
      siteUrl = resolveSiteUrl({ ...fileEnv, ...process.env }, { required: isBuild });
      return { define: { __SITE_URL__: JSON.stringify(siteUrl) } };
    },

    configResolved(resolved) {
      outDir = path.resolve(resolved.root, resolved.build.outDir);
    },

    transformIndexHtml: {
      order: "pre",
      handler(html) {
        if (!html.includes(MARKER)) {
          throw new Error(`[seo] ${MARKER} placeholder missing from index.html <head>`);
        }
        const entries = buildHeadEntries(HOME_META, { siteUrl, pathname: "/" });
        return html.replace(MARKER, () => `${START}\n${serializeHead(entries)}\n    ${END}`);
      },
    },

    writeBundle() {
      if (!isBuild) return;
      const written = emitSeoPages({ outDir, siteUrl });
      console.log(`\n[seo] site URL: ${siteUrl}`);
      console.log(`[seo] wrote ${written.length} static pages: ${written.join(", ")}`);
    },
  };
}
