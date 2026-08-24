#!/usr/bin/env node
// Pattern issue-body linter. Dependency-free. Schema lives in schema.json
// beside this file unless overridden with --config.
//
// Usage:
//   node lint-issue.mjs <body-file> [--genre feature|bug|bootstrap|decision]
//                       [--title "feat(scope): ..."] [--repo <root>]
//                       [--plan-root <root>] [--config <schema.json>]
//
// The body file may carry its title as a first line of the form
// "Title: feat(scope): ..." and an optional "Genre: <name>" line right after,
// both consumed before section parsing. A body Genre line wins over --genre.
// Spec anchors resolve against --plan-root (default: the nearest ancestor of
// the body file containing a plan/ directory) or --repo. Planned: `path`
// markers are informational anchors into artifacts outside both roots; they
// satisfy anchor presence but get no existence check.
// Exit 0 when clean, exit 1 with a readable finding list otherwise.

import { readFileSync, existsSync, statSync } from "node:fs";
import { resolve, dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

function parseArgs(argv) {
  const args = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (
      a === "--genre" || a === "--title" || a === "--repo" ||
      a === "--config" || a === "--plan-root"
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
    "usage: lint-issue.mjs <body-file> [--genre feature|bug|bootstrap|decision] " +
      '[--title "..."] [--repo <root>] [--plan-root <root>] [--config <schema.json>]'
  );
  process.exit(args.help ? 0 : 2);
}

const here = dirname(fileURLToPath(import.meta.url));
const schemaPath = args.config ? resolve(args.config) : join(here, "schema.json");
const schema = JSON.parse(readFileSync(schemaPath, "utf8"));

const bodyPath = resolve(args._[0]);
let body = readFileSync(bodyPath, "utf8");

// Optional embedded title line.
let title = args.title || null;
const titleLine = body.match(/^Title:\s*(.+)\r?\n/);
if (titleLine) {
  if (!title) title = titleLine[1].trim();
  body = body.slice(titleLine[0].length);
}

// Optional embedded genre line (wins over --genre).
let genreName = args.genre || "feature";
const genreLine = body.match(/^Genre:\s*([a-z]+)\s*\r?\n/);
if (genreLine) {
  genreName = genreLine[1];
  body = body.slice(genreLine[0].length);
}
const genre = schema.genres[genreName];
if (!genre) {
  console.error(`unknown genre "${genreName}"; known: ${Object.keys(schema.genres).join(", ")}`);
  process.exit(2);
}

// Plan root: explicit flag, else nearest ancestor of the body file with plan/.
let planRoot = args["plan-root"] ? resolve(args["plan-root"]) : null;
if (!planRoot) {
  let d = dirname(bodyPath);
  for (let i = 0; i < 10; i++) {
    if (existsSync(join(d, "plan")) && statSync(join(d, "plan")).isDirectory()) {
      planRoot = d;
      break;
    }
    const up = dirname(d);
    if (up === d) break;
    d = up;
  }
}

const findings = [];
const err = (code, msg) => findings.push({ code, msg });

// 1. Title grammar.
if (title) {
  if (!new RegExp(schema.titlePattern).test(title)) {
    err("TITLE_GRAMMAR", `title does not match conventional-commit grammar: "${title}"`);
  }
} else {
  err("TITLE_MISSING", "no title given (pass --title or a first line 'Title: ...')");
}

// 2. Minimum body size.
if (body.trim().length < schema.minBodyChars) {
  err(
    "BODY_TOO_SHORT",
    `body is ${body.trim().length} chars; minimum is ${schema.minBodyChars} (a shorter body is not an issue yet)`
  );
}

// 3. Banned characters (C4).
for (const { char, name } of schema.bannedCharacters) {
  const where = [];
  if (body.includes(char)) where.push("body");
  if (title && title.includes(char)) where.push("title");
  if (where.length) err("BANNED_CHAR", `${name} found in ${where.join(" and ")}`);
}

// Section parse: heading -> text until the next heading.
const sections = {};
const order = [];
{
  const lines = body.split(/\r?\n/);
  let current = null;
  let preamble = [];
  for (const line of lines) {
    const m = line.match(/^##\s+(.+?)\s*$/);
    if (m) {
      current = m[1];
      order.push(current);
      sections[current] = [];
    } else if (current) {
      sections[current].push(line);
    } else {
      preamble.push(line);
    }
  }
  sections.__preamble = preamble;
}
const sectionText = (name) => (sections[name] || []).join("\n");
const findHeading = (want) =>
  order.find((h) => h.toLowerCase().startsWith(want.toLowerCase()));

// 4. Required sections, present and in order.
{
  let lastIdx = -1;
  for (const want of genre.requiredSections) {
    const found = findHeading(want);
    if (!found) {
      err("SECTION_MISSING", `required section "## ${want}" not found`);
      continue;
    }
    const idx = order.indexOf(found);
    if (idx < lastIdx) {
      err("SECTION_ORDER", `section "## ${found}" appears out of order`);
    }
    lastIdx = Math.max(lastIdx, idx);
  }
}

// 5. Spec anchor in the preamble (before the first heading).
if (genre.requireSpecAnchor) {
  const pre = sections.__preamble.join("\n");
  const m = pre.match(new RegExp(schema.specAnchorPattern));
  if (!m) {
    err("SPEC_ANCHOR_MISSING", "no spec anchor line (expected: spec: `<path>` before the first section)");
  } else if (args.repo || planRoot) {
    const specPath = m[1].split("#")[0];
    const roots = [planRoot, args.repo ? resolve(args.repo) : null].filter(Boolean);
    if (!roots.some((r) => existsSync(join(r, specPath)))) {
      err(
        "SPEC_PATH_MISSING",
        `spec path does not exist under --plan-root or --repo: ${specPath}`
      );
    }
  }
}

// 6. New:/Existing:/Planned: anchor discipline plus the at-least-one-anchor rule.
// Planned: marks integration points living outside both roots (another repo, a
// not-yet-created repo); informational, no existence check.
const newPaths = [];
const existingAnchors = [];
const plannedPaths = [];
for (const line of body.split(/\r?\n/)) {
  let m = line.match(/\bNew:\s*`([^`]+)`/);
  if (m) newPaths.push(m[1]);
  m = line.match(/\bExisting[^:`]*:\s*`([^`]+)`/);
  if (m) existingAnchors.push(m[1]);
  m = line.match(/\bPlanned:\s*`([^`]+)`/);
  if (m) plannedPaths.push(m[1]);
}
{
  const roots = [args.repo ? resolve(args.repo) : null, planRoot].filter(Boolean);
  if (roots.length) {
    for (const p of newPaths) {
      const bare = p.split(":")[0];
      if (roots.some((r) => existsSync(join(r, bare)))) {
        err("NEW_PATH_EXISTS", `New: path already exists in repo: ${bare}`);
      }
    }
    for (const p of existingAnchors) {
      const [bare, lineNo] = p.split(":");
      const hit = roots.map((r) => join(r, bare)).find((f) => existsSync(f));
      if (!hit) {
        err("EXISTING_PATH_MISSING", `Existing: path not found in repo: ${bare}`);
      } else if (lineNo && statSync(hit).isFile()) {
        const len = readFileSync(hit, "utf8").split(/\r?\n/).length;
        if (Number(lineNo) > len) {
          err("ANCHOR_LINE_OOB", `anchor ${bare}:${lineNo} exceeds file length ${len}`);
        }
      }
    }
  }
}
if (genre.requireFileLineAnchor) {
  const any =
    existingAnchors.length > 0 ||
    plannedPaths.length > 0 ||
    newPaths.length > 0 ||
    new RegExp(schema.fileAnchorPattern).test(body);
  if (!any) {
    err("NO_FILE_ANCHOR", "no file:line anchor (or Planned: marker) found anywhere in the body");
  }
}
if (genre.requireNewPath && newPaths.length === 0) {
  err("NO_NEW_PATH", "bootstrap genre requires at least one New: `path` entry");
}

// 7. Test plan names at least one test path, or carries an explicit Verify:
// line (documents and process deliverables verify by command or checklist).
if (genre.testPlanSection) {
  const heading = findHeading(genre.testPlanSection);
  if (heading) {
    const text = sectionText(heading);
    const hasPath = new RegExp(schema.testPathPattern).test(text);
    const hasVerify = /^\s*(?:[-*]\s*)?Verify:/m.test(text);
    if (!hasPath && !hasVerify) {
      err(
        "TEST_PLAN_NO_PATH",
        `"## ${heading}" names no recognizable test file path and no Verify: line`
      );
    }
  }
}

// 8. Relative-date words anywhere in the body.
for (const w of schema.relativeDateWords) {
  const re = new RegExp(`\\b${w.replace(/ /g, "\\s+")}\\b`, "i");
  if (re.test(body)) {
    err("RELATIVE_DATE", `relative date phrase "${w}" found; use absolute dates (YYYY-MM-DD)`);
  }
}

// 9. Banned vague phrases in acceptance criteria (whole body for genres without one).
{
  const scope = genre.acceptanceSection
    ? sectionText(findHeading(genre.acceptanceSection) || "")
    : body;
  for (const p of schema.bannedAcceptancePhrases) {
    if (scope.toLowerCase().includes(p)) {
      err("VAGUE_ACCEPTANCE", `banned phrase "${p}" in acceptance criteria; state a falsifiable behavior`);
    }
  }
}

// 10. Blocked-by discipline.
if (genre.blockedBySection) {
  const heading = findHeading(genre.blockedBySection);
  if (heading) {
    const text = sectionText(heading);
    const ok = new RegExp(schema.issueRefPattern).test(text) || /\bnone\b/i.test(text);
    if (!ok) {
      err(
        "BLOCKED_BY_EMPTY",
        `"## ${heading}" must list issue refs (#N or local [NNN]) or say "none"`
      );
    }
  }
}

if (findings.length === 0) {
  console.log(`OK: ${args._[0]} (genre: ${genreName})`);
  process.exit(0);
} else {
  console.error(`FINDINGS for ${args._[0]} (genre: ${genreName}):`);
  for (const f of findings) console.error(`  ERROR ${f.code}: ${f.msg}`);
  console.error(`${findings.length} finding(s).`);
  process.exit(1);
}
