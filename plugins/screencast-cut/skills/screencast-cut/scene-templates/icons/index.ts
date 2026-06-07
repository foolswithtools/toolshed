// Curated local icon floor — the always-present, offline, brand-tunable baseline
// the recipe engine animates. Each entry is the normalized SVG (viewBox + path
// d-strings) produced by `scripts/icon_svg.py` from the committed `*.svg`
// sources; the Iconify puller (`scripts/fetch_icon.py`) appends to `icons.json`
// in the same shape. See `THIRD-PARTY-NOTICES` for sources and licenses.

import type { IconDef } from "../AnimatedIcon";
import iconsJson from "./icons.json";

export interface IconRegistryEntry extends IconDef {
  /** Iconify set the icon came from (e.g. "lucide"). */
  set: string;
  /** SPDX license id of that set (e.g. "ISC"). */
  license: string;
}

export const icons = iconsJson as Record<string, IconRegistryEntry>;

export type IconName = keyof typeof iconsJson;

/** Resolve an icon by name; returns undefined if it isn't in the floor. */
export function getIcon(name: string): IconDef | undefined {
  return icons[name];
}
