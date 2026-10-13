// Pure helpers that turn route metadata into <head> entries.
// Shared by the build plugin (serialize to HTML string) and the browser
// (apply to the live document). No imports from Vite, React or the DOM.

import { SITE } from "./routes.js";

export function joinUrl(siteUrl, path) {
  return `${String(siteUrl).replace(/\/+$/, "")}${path}`;
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

const metaName = (name, content) => ({
  tag: "meta",
  sel: `meta[name="${name}"]`,
  attrs: { name, content },
});
const metaProp = (property, content) => ({
  tag: "meta",
  sel: `meta[property="${property}"]`,
  attrs: { property, content },
});

/**
 * @param meta     { title, description, robots }
 * @param ctx      { siteUrl: "https://example.com" (origin only),
 *                   pathname: "/" | "/jobs" | null }
 * pathname === null  -> omit canonical and og:url
 */
export function buildHeadEntries(meta, { siteUrl, pathname }) {
  const pageUrl = pathname == null ? null : joinUrl(siteUrl, pathname === "/" ? "/" : pathname);
  const image = joinUrl(siteUrl, SITE.image.path);

  const entries = [
    { tag: "title", sel: "title", text: meta.title },
    metaName("description", meta.description),
    metaName("robots", meta.robots),
  ];

  if (pageUrl) {
    entries.push({
      tag: "link",
      sel: 'link[rel="canonical"]',
      attrs: { rel: "canonical", href: pageUrl },
    });
  }

  entries.push(
    metaProp("og:type", SITE.ogType),
    metaProp("og:site_name", SITE.name),
    metaProp("og:locale", SITE.locale),
    metaProp("og:title", meta.title),
    metaProp("og:description", meta.description),
  );
  if (pageUrl) entries.push(metaProp("og:url", pageUrl));
  entries.push(
    metaProp("og:image", image),
    metaProp("og:image:secure_url", image),
    metaProp("og:image:type", SITE.image.type),
    metaProp("og:image:width", String(SITE.image.width)),
    metaProp("og:image:height", String(SITE.image.height)),
    metaProp("og:image:alt", SITE.image.alt),
    metaName("twitter:card", SITE.twitterCard),
    metaName("twitter:title", meta.title),
    metaName("twitter:description", meta.description),
    metaName("twitter:image", image),
    metaName("twitter:image:alt", SITE.image.alt),
  );
  return entries;
}

export function serializeHead(entries, indent = "    ") {
  return entries
    .map((e) => {
      if (e.tag === "title") return `${indent}<title>${escapeHtml(e.text)}</title>`;
      const attrs = Object.entries(e.attrs)
        .map(([k, v]) => `${k}="${escapeHtml(v)}"`)
        .join(" ");
      return `${indent}<${e.tag} ${attrs} />`;
    })
    .join("\n");
}

// Every selector this module can manage, so stale ones (canonical / og:url)
// can be removed when navigating to a route that does not define them.
const MANAGED_SELECTORS = buildHeadEntries(
  { title: "", description: "", robots: "" },
  { siteUrl: "https://placeholder.invalid", pathname: "/" },
).map((e) => e.sel);

export function applyHead(entries, doc) {
  const head = doc.head;
  const wanted = new Set();

  for (const entry of entries) {
    wanted.add(entry.sel);
    if (entry.tag === "title") {
      doc.title = entry.text;
      continue;
    }
    let el = head.querySelector(entry.sel);
    if (!el) {
      el = doc.createElement(entry.tag);
      head.appendChild(el);
    }
    for (const [key, value] of Object.entries(entry.attrs)) {
      el.setAttribute(key, value);
    }
  }

  for (const sel of MANAGED_SELECTORS) {
    if (!wanted.has(sel)) {
      const stale = head.querySelector(sel);
      if (stale) stale.remove();
    }
  }
}
