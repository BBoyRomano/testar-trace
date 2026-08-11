import type { StateModel } from "./types.ts";

type StateNode = StateModel["graph"]["nodes"][number];

export function stateNodeDisplayName(node: StateNode): string {
  const sourceLabel = (node.title ?? node.label)
    .trim()
    .replace(/^S\d+\s*·\s*/u, "")
    .trim();
  const normalizedLabel = urlLike(sourceLabel) ? pageName(sourceLabel) : sourceLabel;
  const fallback = pageName(node.url);
  const label = normalizedLabel || fallback;
  return label === node.id || /^(?:state|untitled state)$/iu.test(label) ? fallback : label;
}

function urlLike(value: string): boolean {
  return /^(?:[a-z][a-z\d+.-]*:\/\/|\/)/iu.test(value);
}

function pageName(value: string | undefined): string {
  if (value === undefined || value.trim() === "") return "";
  try {
    const url = new URL(value, "https://state-model.invalid");
    const segment = url.pathname.split("/").filter(Boolean).at(-1);
    if (segment === undefined) return "Home";
    return decodeURIComponent(segment)
      .replace(/\.[a-z\d]+$/iu, "")
      .replaceAll(/[-_]+/gu, " ")
      .replace(/^./u, (character) => character.toLocaleUpperCase());
  } catch {
    return "";
  }
}
