// _verify_helper.mjs — the Node half of verify_render.py.
//
// Bundles a Remotion project ONCE, lists compositions, then renders a fixed
// set of stills (the "filmstrip") for the requested composition. All policy
// (which frames, what the expectations are, exit codes) lives in the Python
// orchestrator; this file is the thin Remotion-API shim.
//
// Invocation:
//   node _verify_helper.mjs <projectRoot> <compId> <requestJsonPath>
// where requestJson = { scale: number, outDir: string, frames: number[] }.
//
// Emits a single JSON object on stdout:
//   {
//     ok: boolean,                 // bundle + getCompositions succeeded
//     stage: "bundle"|"getCompositions"|"renderStill"|"done",
//     entryPoint: string|null,
//     error: string|null,
//     compositions: [{id,durationInFrames,width,height,fps}],
//     target: {id,durationInFrames,width,height,fps}|null,
//     stills: [{frame, path, ok, error}]
//   }
// Exit code is always 0 unless Node itself crashes — the Python side reads the
// JSON and decides pass/fail. A bundle/getCompositions failure is reported in
// the JSON with ok:false, NOT as a process error.

import { existsSync } from "node:fs";
import { readFile } from "node:fs/promises";
import { createRequire } from "node:module";
import path from "node:path";

const require = createRequire(import.meta.url);

const result = {
  ok: false,
  stage: "bundle",
  entryPoint: null,
  error: null,
  // envError = the failure is environmental/invocation (no entry point, Remotion
  // not installed, bad args) rather than a real gate failure (bundle compile
  // error, missing composition). Python maps envError -> exit 3, else exit 2.
  envError: false,
  compositions: [],
  target: null,
  stills: [],
};

function emit() {
  process.stdout.write(JSON.stringify(result));
}

function findEntryPoint(projectRoot) {
  // Remotion's registerRoot entry. Cover the common scaffolds.
  const candidates = [
    "src/index.ts",
    "src/index.tsx",
    "src/index.js",
    "src/index.jsx",
    "remotion/index.ts",
    "src/Video.tsx",
    "index.ts",
  ];
  for (const c of candidates) {
    const p = path.join(projectRoot, c);
    if (existsSync(p)) return p;
  }
  return null;
}

async function main() {
  const [, , projectRoot, compId, reqPath] = process.argv;
  if (!projectRoot || !compId || !reqPath) {
    result.error =
      "usage: node _verify_helper.mjs <projectRoot> <compId> <requestJsonPath>";
    result.envError = true;
    emit();
    return;
  }

  const req = JSON.parse(await readFile(reqPath, "utf-8"));
  const scale = typeof req.scale === "number" ? req.scale : 1;
  const frames = Array.isArray(req.frames) ? req.frames : [];
  const outDir = req.outDir;

  const entryPoint = findEntryPoint(projectRoot);
  result.entryPoint = entryPoint;
  if (!entryPoint) {
    result.error = `no Remotion entry point found under ${projectRoot} (looked for src/index.ts etc.)`;
    result.envError = true;
    emit();
    return;
  }

  // Resolve the Remotion API from the PROJECT's node_modules, not the plugin's.
  const projectRequire = createRequire(path.join(projectRoot, "package.json"));
  let bundle, getCompositions, renderStill;
  try {
    ({ bundle } = projectRequire("@remotion/bundler"));
    ({ getCompositions, renderStill } = projectRequire("@remotion/renderer"));
  } catch (e) {
    result.error =
      `could not load @remotion/bundler / @remotion/renderer from ${projectRoot}. ` +
      `Run \`npm ci\` in the project. Underlying: ${String(e)}`;
    result.envError = true;
    emit();
    return;
  }

  try {
    result.stage = "bundle";
    const serveUrl = await bundle({
      entryPoint,
      webpackOverride: (c) => c,
    });

    result.stage = "getCompositions";
    const comps = await getCompositions(serveUrl, { inputProps: {} });
    result.compositions = comps.map((c) => ({
      id: c.id,
      durationInFrames: c.durationInFrames,
      width: c.width,
      height: c.height,
      fps: c.fps,
    }));

    const composition = comps.find((c) => c.id === compId);
    if (!composition) {
      result.error = `composition "${compId}" not found (have: ${comps
        .map((c) => c.id)
        .join(", ")})`;
      emit();
      return;
    }
    result.target = {
      id: composition.id,
      durationInFrames: composition.durationInFrames,
      width: composition.width,
      height: composition.height,
      fps: composition.fps,
    };

    // bundle + getCompositions both succeeded — deterministic gates 0/1 pass.
    result.ok = true;

    result.stage = "renderStill";
    for (const frame of frames) {
      const safe = Math.max(
        0,
        Math.min(frame, composition.durationInFrames - 1),
      );
      const out = path.join(
        outDir,
        `frame-${String(safe).padStart(6, "0")}.png`,
      );
      try {
        await renderStill({
          composition,
          serveUrl,
          output: out,
          frame: safe,
          scale,
          inputProps: {},
          overwrite: true,
        });
        result.stills.push({ frame: safe, path: out, ok: true, error: null });
      } catch (e) {
        // A SafeImg/SafeVideo cancelRender() lands here → deterministic still failure.
        result.stills.push({
          frame: safe,
          path: out,
          ok: false,
          error: String(e && e.message ? e.message : e),
        });
      }
    }

    result.stage = "done";
    emit();
  } catch (e) {
    result.error = String(e && e.stack ? e.stack : e);
    emit();
  }
}

main().catch((e) => {
  result.error = String(e && e.stack ? e.stack : e);
  emit();
  process.exitCode = 0; // Python reads JSON; never signal via exit here.
});
