// Library-backed Lottie recolor (screencast-cut Phase 2).
//
// The canonical recolor path named in the plan: it parses the Lottie with
// @lottiefiles/lottie-js (MIT) and rewrites every FLAT fill/stroke color to a
// target hex. This is the richer sibling of the pure-Python flat-fill recolor in
// scripts/lottie_ingest.py — both produce the same flat-fill result; the library
// understands the full shape model, so this is the one to extend for more shape
// types later. BEST-EFFORT by design: gradients, animated colors and expression-
// driven colors are left untouched and listed in the report.
//
//   node recolor_lottie.mjs <in.json> <#rrggbb> [out.json]
//
// @lottiefiles/lottie-js is a dependency of the OUTPUT Remotion project (where
// the recolor is run), not of this scripts/ dir — so we resolve it from the
// project root (cwd, or $LOTTIE_PROJECT_ROOT) the same way verify's Node helper
// resolves @remotion/* from its target project.
//
// Prints a JSON report ({recolored, skipped[]}) to stdout. If out.json is given,
// writes the recolored animation there. It never writes into a committed/bundled
// location on its own — the BYO licensing rule (a user's file stays at their own
// path) is the caller's responsibility.

import { readFileSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";
import { pathToFileURL } from "node:url";

function hexToRgba(hex) {
  const h = hex.replace(/^#/, "");
  if (h.length !== 6 && h.length !== 8) {
    throw new Error(`color must be #rrggbb or #rrggbbaa, got ${hex}`);
  }
  const r = parseInt(h.slice(0, 2), 16) / 255;
  const g = parseInt(h.slice(2, 4), 16) / 255;
  const b = parseInt(h.slice(4, 6), 16) / 255;
  const a = h.length === 8 ? parseInt(h.slice(6, 8), 16) / 255 : 1;
  return [r, g, b, a].map((v) => Math.round(v * 1e6) / 1e6);
}

// Walk the parsed shape tree (the library renames Lottie `it` → `shapes` on
// groups) and recolor flat fills/strokes. Gradient/animated/expression colors
// are reported, not touched.
function recolor(animation, rgba, FillCtorNames) {
  const report = { recolored: 0, skipped: [] };

  const visit = (shapes) => {
    for (const shape of shapes || []) {
      const cn = shape.constructor.name;
      if (cn === "FillShape" || cn === "StrokeShape") {
        const color = shape.color;
        if (color && typeof color.expression === "string" && color.expression.trim()) {
          report.skipped.push({ kind: cn, reason: "expression-driven color" });
        } else if (color && color.animated) {
          report.skipped.push({ kind: cn, reason: "animated color" });
        } else if (color) {
          const next = [rgba[0], rgba[1], rgba[2], rgba[3]];
          color.value = next;
          color.values = next;
          report.recolored += 1;
        }
      } else if (cn === "GradientFillShape" || cn === "GradientStrokeShape") {
        report.skipped.push({ kind: cn, reason: "gradient (not themeable)" });
      }
      if (shape.shapes) visit(shape.shapes);
    }
  };

  for (const layer of animation.layers || []) {
    if (layer.shapes) visit(layer.shapes);
  }
  return report;
}

async function loadLib() {
  const projectRoot = process.env.LOTTIE_PROJECT_ROOT || process.cwd();
  const req = createRequire(path.join(projectRoot, "package.json"));
  let libPath;
  try {
    libPath = req.resolve("@lottiefiles/lottie-js");
  } catch (e) {
    throw new Error(
      `@lottiefiles/lottie-js not found from ${projectRoot}. Install it in the ` +
        `Remotion project (npm i -D @lottiefiles/lottie-js) or set ` +
        `$LOTTIE_PROJECT_ROOT.\n${e.message}`,
    );
  }
  return import(pathToFileURL(libPath).href);
}

async function main() {
  const [, , inPath, hex, outPath] = process.argv;
  if (!inPath || !hex) {
    console.error("usage: node recolor_lottie.mjs <in.json> <#rrggbb> [out.json]");
    process.exit(1);
  }
  const { Animation } = await loadLib();
  const data = JSON.parse(readFileSync(inPath, "utf-8"));
  const rgba = hexToRgba(hex);
  const animation = new Animation().fromJSON(data);
  const report = recolor(animation, rgba);
  const out = animation.toJSON();
  if (outPath) {
    writeFileSync(outPath, JSON.stringify(out) + "\n", "utf-8");
    report.out = outPath;
  }
  process.stdout.write(JSON.stringify(report));
}

main().catch((err) => {
  console.error(String(err && err.message ? err.message : err));
  process.exit(1);
});
