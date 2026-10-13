import { useEffect } from "react";
import { useLocation } from "react-router-dom";
import { matchRouteMeta } from "../seo/routes";
import { buildHeadEntries, applyHead } from "../seo/head";

// __SITE_URL__ is injected at build time by vite-plugin-seo.js.
const SITE_URL =
  typeof __SITE_URL__ !== "undefined" ? __SITE_URL__ : window.location.origin;

/**
 * Keeps <head> metadata in sync with the current route during client-side
 * navigation. Crawlers do NOT depend on this: the same metadata is already in
 * the static HTML served for each URL. This component exists so that
 * navigating Jobs -> Resources -> back to "/" always restores the homepage
 * values instead of leaving another page's metadata behind.
 */
export default function RouteMeta() {
  const { pathname } = useLocation();

  useEffect(() => {
    const { meta, path } = matchRouteMeta(pathname);
    applyHead(buildHeadEntries(meta, { siteUrl: SITE_URL, pathname: path }), document);
  }, [pathname]);

  return null;
}
