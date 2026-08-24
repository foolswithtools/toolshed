#!/usr/bin/env node
// Kickoff preflight. Refuses to hand a stale or malformed issue body to a
// fresh worker session. Dependency-free, two layers:
//
//   1. Invokes the plugin's issue-body linter (lint-issue.mjs, lane A)
//      unmodified as a subprocess and folds its findings in verbatim. This
//      catches missing sections, bad title grammar, an Existing: anchor
//      whose file is gone, or a line number past end of file.
//   2. Adds an anchor-freshness check the linter does not do. The plugin's
//      own issue-authoring convention names the anchored symbol in a second
//      backtick span right after the file:line anchor (see
//      prompts/github-issue-template.md, "Existing prior art to fold in:
//      `<path:line>` `<functionName>`"). For every anchor written that way,
//      this greps the anchor's target file for that symbol within a 20-line
//      window either side of the anchor line. A line count still in range
//      does not mean the code at that line is still what the issue
//      describes; that is exactly the drift the linter's line-length check
//      cannot see.
//
// Usage:
//   node kickoff-preflight.mjs <body-file> [--genre feature|bug|bootstrap|decision]
//                              [--title "..."] [--repo <root>] [--plan-root <root>]
//                              [--config <schema.json>] [--pattern-config <path>]
//
// Exit 0 with "PREFLIGHT PASS" and per-anchor freshness (last commit date
// touching the anchor's file, when the repo is a git checkout) when clean.
// Exit 1 with a combined "PREFLIGHT REFUSED" finding list otherwise. The
// caller (the /kickoff command) must never produce a kickoff prompt when
// this exits nonzero.

import { readFileSync, existsSync, statSync } from "node:fs";
import { resolve, dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const ANCHOR_WINDOW = 20;

const here = dirname(fileURLToPath(import.meta.url));
const linterPath = join(here, "lint-issue.mjs");

function parseArgs(argv) {
  const args = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (
      a === "--genre" || a === "--title" || a === "--repo" ||
      a === "--config" || a === "--plan-root" || a === "--pattern-config"
    ) {
      args[a.slice(2)] = argv[++i];
    } else if (a === "--help" || a === "-h") {
      args.help = true;
    } else {
      args._.push(a);
    }
  }
  return args;
}

const args = parseArgs(process.argv.slice(2));
if (args.help || args._.length !== 1) {
  console.log(
    "usage: kickoff-preflight.mjs <body-file> [--genre feature|bug|bootstrap|decision] " +
      '[--title "..."] [--repo <root>] [--plan-root <root>] [--config <schema.json>] ' +
      "[--pattern-config <.pattern-config.json>]"
  );
  process.exit(args.help ? 0 : 2);
}

const bodyArg = args._[0];
const bodyPath = resolve(bodyArg);
const body = readFileSync(bodyPath, "utf8");

// --- Layer 1: the real linter, invoked unmodified, not reimplemented. ---
const linterArgv = [linterPath, bodyPath];
if (args.genre) linterArgv.push("--genre", args.genre);
if (args.title) linterArgv.push("--title", args.title);
if (args.repo) linterArgv.push("--repo", args.repo);
if (args.config) linterArgv.push("--config", args.config);
if (args["plan-root"]) linterArgv.push("--plan-root", args["plan-root"]);
if (args["pattern-config"]) linterArgv.push("--pattern-config", args["pattern-config"]);

const lintRun = spawnSync(process.execPath, linterArgv, { encoding: "utf8" });
const findings = [];
if (lintRun.status !== 0) {
  const combined = `${lintRun.stdout || ""}${lintRun.stderr || ""}`;
  let matched = false;
  for (const line of combined.split(/\r?\n/)) {
    const m = line.match(/^\s*ERROR (\S+): (.+)$/);
    if (m) {
      matched = true;
      findings.push({ code: m[1], msg: m[2], source: "linter" });
    }
  }
  if (!matched) {
    // A usage error or crash the finding-line regex did not match: surface
    // it raw rather than swallowing it.
    findings.push({
      code: "LINTER_ERROR",
      msg: combined.trim() || `lint-issue.mjs exited ${lintRun.status}`,
      source: "linter",
    });
  }
}

// --- Layer 2: anchor-symbol freshness. ---
// Existing:-style anchor followed by a second backtick span naming the
// symbol, e.g. "Existing prior art to fold in: `src/example.ts:10` `exampleHandler`".
const anchorRe = /\bExisting[^:`]*:\s*`([^`]+)`(?:\s+`([^`]+)`)?/g;
const roots = [
  args.repo ? resolve(args.repo) : null,
  args["plan-root"] ? resolve(args["plan-root"]) : null,
].filter(Boolean);

const freshness = [];
let m;
while ((m = anchorRe.exec(body)) !== null) {
  const anchor = m[1];
  const symbol = m[2];
  const [barePath, lineNoRaw] = anchor.split(":");
  const lineNo = lineNoRaw ? Number(lineNoRaw) : null;
  if (!symbol || !lineNo || roots.length === 0) continue; // nothing more to verify here

  const hit = roots.map((r) => join(r, barePath)).find((f) => existsSync(f) && statSync(f).isFile());
  if (!hit) continue; // already flagged by the linter (EXISTING_PATH_MISSING)

  const lines = readFileSync(hit, "utf8").split(/\r?\n/);
  if (lineNo > lines.length) continue; // already flagged by the linter (ANCHOR_LINE_OOB)

  const start = Math.max(0, lineNo - 1 - ANCHOR_WINDOW);
  const end = Math.min(lines.length, lineNo - 1 + ANCHOR_WINDOW + 1);
  const window = lines.slice(start, end).join("\n");
  if (!window.includes(symbol)) {
    findings.push({
      code: "ANCHOR_SYMBOL_DRIFT",
      msg: `${barePath}:${lineNo} \`${symbol}\` not found within ${ANCHOR_WINDOW} lines either side (anchor has rotted; re-verify against current main)`,
      source: "preflight",
    });
  } else {
    freshness.push({ path: barePath, line: lineNo, symbol });
  }
}

function gitDate(root, relPath) {
  const r = spawnSync("git", ["-C", root, "log", "-1", "--format=%ad", "--date=short", "--", relPath], {
    encoding: "utf8",
  });
  if (r.status === 0 && r.stdout.trim()) return r.stdout.trim();
  return null;
}

if (findings.length === 0) {
  console.log(`PREFLIGHT PASS: ${bodyArg}`);
  if (freshness.length > 0) {
    console.log("anchor freshness:");
    for (const f of freshness) {
      const root = roots.find((r) => existsSync(join(r, f.path)));
      const date = root ? gitDate(root, f.path) : null;
      console.log(`  ${f.path}:${f.line} \`${f.symbol}\`${date ? ` (last touched ${date})` : " (freshness unknown: no git history for this file)"}`);
    }
  }
  process.exit(0);
} else {
  console.error(`PREFLIGHT REFUSED: ${bodyArg}`);
  for (const f of findings) console.error(`  ERROR ${f.code} [${f.source}]: ${f.msg}`);
  console.error(`${findings.length} finding(s). Fix the issue body, not this prompt.`);
  process.exit(1);
}
