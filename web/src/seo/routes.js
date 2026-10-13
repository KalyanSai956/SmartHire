// Single source of truth for SmartHire link-preview / SEO metadata.
//
// Used in two places so they can never drift apart:
//   1. vite-plugin-seo.js  -> writes the metadata into the STATIC HTML at build
//                             time (what WhatsApp, LinkedIn, Telegram, Discord
//                             and Google read, because they do not run React).
//   2. src/components/RouteMeta.jsx -> keeps <head> correct during client-side
//                             navigation, so the homepage values are restored
//                             when the user comes back to "/".
//
// This file must stay free of JSX / browser / Vite-only APIs.

export const SITE = {
  name: "SmartHire",
  locale: "en_IN",
  ogType: "website",
  twitterCard: "summary_large_image",
  image: {
    path: "/og-image.png",
    type: "image/png",
    width: 1200,
    height: 630,
    alt: "SmartHire - AI-Powered Resume & Job Matching",
  },
};

const INDEXABLE = "index, follow, max-image-preview:large";
const PRIVATE = "noindex, nofollow";

export const HOME_META = {
  title: "SmartHire | AI-Powered Resume & Job Matching",
  description:
    "Discover relevant jobs, optimize your resume with ATS-friendly suggestions, and prepare for interviews with SmartHire.",
  robots: INDEXABLE,
};

// Default for any URL that is not listed below (404s, unknown paths).
// No canonical / og:url is emitted for it because the real path is unknown
// when the static fallback page is generated.
export const FALLBACK_META = {
  title: "SmartHire | AI-Powered Career Workspace",
  description:
    "SmartHire brings resume analysis, job matching and interview preparation together in one AI-powered career workspace.",
  robots: PRIVATE,
};

// Signed-in workspace pages. They redirect to "/" for visitors, so they are
// kept out of search results, but they still get a clean title/description and
// the same share image if someone pastes the link.
export const ROUTES = {
  "/": HOME_META,
  "/dashboard": {
    title: "Dashboard | SmartHire",
    description:
      "Your SmartHire career workspace: resume analyses, job matches and interview preparation in one place.",
    robots: PRIVATE,
  },
  "/analyze": {
    title: "Resume Analysis | SmartHire",
    description:
      "Upload your resume and get ATS-friendly suggestions, keyword gaps and actionable improvements with SmartHire.",
    robots: PRIVATE,
  },
  "/history": {
    title: "Analysis History | SmartHire",
    description:
      "Review your previous SmartHire resume analyses and download your reports.",
    robots: PRIVATE,
  },
  "/jobs": {
    title: "Jobs | SmartHire",
    description:
      "Discover jobs that match your profile, skills and target roles with SmartHire.",
    robots: PRIVATE,
  },
  "/interview-prep": {
    title: "Interview Prep | SmartHire",
    description:
      "Prepare for interviews with role-focused questions and AI-assisted practice on SmartHire.",
    robots: PRIVATE,
  },
  "/resources": {
    title: "Resources | SmartHire",
    description:
      "Career and resume resources to help you prepare stronger applications with SmartHire.",
    robots: PRIVATE,
  },
  "/settings": {
    title: "AI Settings | SmartHire",
    description: "Manage your AI provider settings on SmartHire.",
    robots: PRIVATE,
  },
  "/onboarding": {
    title: "Get Started | SmartHire",
    description:
      "Set up your SmartHire career profile to get relevant job matches and resume insights.",
    robots: PRIVATE,
  },
  "/admin": {
    title: "Admin | SmartHire",
    description: "SmartHire administration.",
    robots: PRIVATE,
  },
};

// Dynamic route /analysis/:id (cannot be pre-generated statically).
export const ANALYSIS_META = {
  title: "Resume Analysis Report | SmartHire",
  description:
    "Your SmartHire resume analysis report with ATS score, keyword coverage and improvement suggestions.",
  robots: PRIVATE,
};

export function normalizePath(pathname) {
  const clean = (pathname || "/").split("?")[0].split("#")[0];
  const trimmed = clean.replace(/\/+$/, "");
  return trimmed === "" ? "/" : trimmed;
}

/**
 * Resolve metadata for a pathname.
 * Returns { meta, path } where `path` is the canonical path to advertise, or
 * null when no canonical/og:url should be emitted.
 */
export function matchRouteMeta(pathname) {
  const path = normalizePath(pathname);
  if (Object.prototype.hasOwnProperty.call(ROUTES, path)) {
    return { meta: ROUTES[path], path };
  }
  if (/^\/analysis\/[^/]+$/.test(path)) {
    return { meta: ANALYSIS_META, path };
  }
  return { meta: FALLBACK_META, path: null };
}
