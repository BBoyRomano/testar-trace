export type PathHighlightColors = {
  weak: string;
  strong: string;
  border: string;
  labelBackground: string;
};

const PATH_COLORS: readonly PathHighlightColors[] = [
  { weak: "#c0c9f0", strong: "#3857d6", border: "#2946bd", labelBackground: "#eef1ff" },
  { weak: "#f1d6a8", strong: "#a66307", border: "#7a4803", labelBackground: "#fff6e5" },
  { weak: "#d9c9ee", strong: "#7651c9", border: "#5b3ca3", labelBackground: "#f4f0ff" },
  { weak: "#b7dedb", strong: "#007d79", border: "#005d5d", labelBackground: "#e6f7f6" },
  { weak: "#e8bed6", strong: "#9f1853", border: "#7d123f", labelBackground: "#fff0f6" },
  { weak: "#b9ddea", strong: "#0f6f9c", border: "#075577", labelBackground: "#eaf7fc" },
  { weak: "#ccddb2", strong: "#4d6f18", border: "#3a5510", labelBackground: "#f1f8e8" },
  { weak: "#ecc6bb", strong: "#b44b35", border: "#843626", labelBackground: "#fff2ee" },
  { weak: "#e4d79f", strong: "#8a6a00", border: "#654e00", labelBackground: "#fffbe8" },
  { weak: "#d9c9c0", strong: "#72584b", border: "#513e35", labelBackground: "#f8f3f0" },
];

export const PATH_TONE_COUNT = PATH_COLORS.length;

export function pathHighlightColors(index: number): PathHighlightColors {
  const normalized = ((index % PATH_TONE_COUNT) + PATH_TONE_COUNT) % PATH_TONE_COUNT;
  return PATH_COLORS[normalized] ?? PATH_COLORS[0]!;
}

export function pathToneVariables(index: number): string {
  const colors = pathHighlightColors(index);
  return `--path-accent:${colors.strong};--path-weak:${colors.weak};--path-soft:${colors.labelBackground};--path-text:${colors.border}`;
}
