#!/usr/bin/env node
// Helper for run-pi-smoke-tests.sh. Uses pi's own SDK, resolved from the pi
// binary already on PATH (never a hardcoded machine path), to prove an
// installed pdlc-build package surfaces the shared skills/ and prompts/
// directories through pi's real startup resolver. No model call, no provider key.
//
// Env in:
//   PI_PKG_ROOT          root of the installed @earendil-works/pi-coding-agent
//                         package (the directory containing dist/index.js)
//   PI_CODING_AGENT_DIR  isolated pi agent dir
// Reads pi settings from process.cwd().
//
// Prints "SKILLS=<n>" and "PROMPTS=<n>" lines plus one "  skill: <path>" or
// "  prompt: <path>" line per discovered resource. Exits 1 if the resolver
// throws, or if any discovered resource resolves outside a skills/ or prompts/
// directory (which would mean pi is loading something other than the shared core).

import { join, sep } from "node:path";

const pkgRoot = process.env.PI_PKG_ROOT;
if (!pkgRoot) {
  console.error("PI_PKG_ROOT is not set");
  process.exit(2);
}

const { DefaultPackageManager, SettingsManager } = await import(join(pkgRoot, "dist/index.js"));

const cwd = process.cwd();
const agentDir = process.env.PI_CODING_AGENT_DIR;
const settingsManager = SettingsManager.create(cwd, agentDir);
const packageManager = new DefaultPackageManager({ cwd, agentDir, settingsManager });

const resolved = await packageManager.resolve();
const skillPaths = resolved.skills.map((s) => s.path);
const promptPaths = resolved.prompts.map((p) => p.path);

const outsideShared = [...skillPaths, ...promptPaths].filter(
  (p) => !p.includes(`${sep}skills${sep}`) && !p.includes(`${sep}prompts${sep}`),
);
if (outsideShared.length > 0) {
  console.error("resources resolved outside skills/ or prompts/:", outsideShared);
  process.exit(1);
}

console.log(`SKILLS=${skillPaths.length}`);
for (const p of skillPaths) console.log(`  skill: ${p}`);
console.log(`PROMPTS=${promptPaths.length}`);
for (const p of promptPaths) console.log(`  prompt: ${p}`);
