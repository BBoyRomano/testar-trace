import type { ViewName } from "./types.ts";

export type AppRoute = { view: Exclude<ViewName, "result"> } | { view: "result"; runId: string };

const STATIC_ROUTES: Record<Exclude<ViewName, "result">, string> = {
  analyses: "/analyses",
  "new-analysis": "/analyses/new",
  requirements: "/analyses/new/requirements",
  "state-models": "/analyses/new/state-models",
};

export function routePath(view: Exclude<ViewName, "result">): string;
export function routePath(view: "result", runId: string): string;
export function routePath(view: ViewName, runId = ""): string {
  if (view !== "result") return STATIC_ROUTES[view];
  if (runId === "") throw new Error("A result route requires an analysis id.");
  return `/analyses/${encodeURIComponent(runId)}`;
}

export function parseRoute(pathname: string): AppRoute | null {
  const path = normalizePath(pathname);
  for (const [view, route] of Object.entries(STATIC_ROUTES)) {
    if (path === route) return { view: view as Exclude<ViewName, "result"> };
  }
  const match = /^\/analyses\/([^/]+)$/.exec(path);
  if (match?.[1] === undefined) return null;
  try {
    return { view: "result", runId: decodeURIComponent(match[1]) };
  } catch {
    return null;
  }
}

function normalizePath(pathname: string): string {
  if (pathname === "/") return pathname;
  return pathname.replace(/\/+$/, "");
}
