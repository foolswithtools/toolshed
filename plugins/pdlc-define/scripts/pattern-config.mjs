#!/usr/bin/env node
// Loader and validator for the per-repo .pattern-config.json. Dependency-free.
// The JSON Schema documenting the same contract lives in
// ../config/pattern-config.schema.json; this module enforces it by hand so
// consumers need only node. One schema, two consumers: the plugin's skills and
// commands (paths, partitions, gates, labels) and lint-issue.mjs (partition and
// spec-path validation).
//
// Module API:
//   loadPatternConfig(repoRoot | explicitFilePath)
//     -> { config, source: "file" | "defaults", path: string | null, findings: [] }
//   Findings non-empty means the file exists but is invalid; config is then the
//   defaults and source is "defaults".
//
// CLI:
//   node pattern-config.mjs validate [--repo <root>] [--config <file>]
//     Exit 0: valid file (or no file, defaults apply). Exit 1: invalid file.
//   node pattern-config.mjs show [--repo <root>] [--config <file>]
//     Prints the effective config as JSON (file values or defaults) plus a
//     "source" field saying which was used.

import { readFileSync, existsSync, statSync } from "node:fs";
import { resolve, join } from "node:path";

export const CONFIG_FILENAME = ".pattern-config.json";

export const DEFAULTS = Object.freeze({
  version: 1,
  spec_dir: "docs/specs",
  known_issues_dir: "docs/known-issues",
  roadmap_path: "docs/ROADMAP.md",
  partitions: [],
  gate_commands: [],
  labels: [],
});

const KNOWN_KEYS = Object.keys(DEFAULTS);

function isRelativePath(p) {
  if (typeof p !== "string" || p.length === 0) return false;
  if (p.startsWith("/") || p.startsWith("\\")) return false;
  return !p.split(/[\\/]/).includes("..");
}

// Returns a list of finding strings; empty means valid.
export function validatePatternConfig(raw) {
  const findings = [];
  if (typeof raw !== "object" || raw === null || Array.isArray(raw)) {
    return ["top level must be a JSON object"];
  }
  for (const k of Object.keys(raw)) {
    if (!KNOWN_KEYS.includes(k)) {
      findings.push(`unknown key "${k}" (known: ${KNOWN_KEYS.join(", ")})`);
    }
  }
  if (raw.version !== 1) {
    findings.push(`"version" must be 1 (got ${JSON.stringify(raw.version)})`);
  }
  if (!isRelativePath(raw.spec_dir)) {
    findings.push('"spec_dir" is required and must be a repo-relative path (no leading slash, no "..")');
  }
  for (const key of ["known_issues_dir", "roadmap_path"]) {
    if (raw[key] !== undefined && !isRelativePath(raw[key])) {
      findings.push(`"${key}" must be a repo-relative path (no leading slash, no "..")`);
    }
  }
  if (raw.partitions !== undefined) {
    if (!Array.isArray(raw.partitions)) {
      findings.push('"partitions" must be an array');
    } else {
      const seen = new Set();
      raw.partitions.forEach((p, i) => {
        if (typeof p !== "object" || p === null || Array.isArray(p)) {
          findings.push(`partitions[${i}] must be an object with a "name"`);
          return;
        }
        if (typeof p.name !== "string" || !/^[a-z0-9][a-z0-9-]*$/.test(p.name)) {
          findings.push(`partitions[${i}].name must match ^[a-z0-9][a-z0-9-]*$`);
        } else if (seen.has(p.name)) {
          findings.push(`duplicate partition name "${p.name}"`);
        } else {
          seen.add(p.name);
        }
        for (const k of Object.keys(p)) {
          if (!["name", "description"].includes(k)) {
            findings.push(`partitions[${i}] has unknown key "${k}"`);
          }
        }
        if (p.description !== undefined && typeof p.description !== "string") {
          findings.push(`partitions[${i}].description must be a string`);
        }
      });
    }
  }
  if (raw.gate_commands !== undefined) {
    if (!Array.isArray(raw.gate_commands)) {
      findings.push('"gate_commands" must be an array');
    } else {
      raw.gate_commands.forEach((g, i) => {
        if (typeof g !== "object" || g === null || Array.isArray(g)) {
          findings.push(`gate_commands[${i}] must be an object with "name" and "run"`);
          return;
        }
        for (const k of ["name", "run"]) {
          if (typeof g[k] !== "string" || g[k].length === 0) {
            findings.push(`gate_commands[${i}].${k} must be a non-empty string`);
          }
        }
        for (const k of Object.keys(g)) {
          if (!["name", "run"].includes(k)) {
            findings.push(`gate_commands[${i}] has unknown key "${k}"`);
          }
        }
      });
    }
  }
  if (raw.labels !== undefined) {
    if (!Array.isArray(raw.labels) || raw.labels.some((l) => typeof l !== "string" || l.length === 0)) {
      findings.push('"labels" must be an array of non-empty strings');
    } else if (new Set(raw.labels).size !== raw.labels.length) {
      findings.push('"labels" must not contain duplicates');
    }
  }
  return findings;
}

// target: a repo root (the file is looked up as <root>/.pattern-config.json)
// or a direct path to a config file.
export function loadPatternConfig(target) {
  const abs = resolve(target);
  let path = null;
  if (existsSync(abs) && statSync(abs).isFile()) {
    path = abs;
  } else if (existsSync(join(abs, CONFIG_FILENAME))) {
    path = join(abs, CONFIG_FILENAME);
  }
  if (!path) {
    return { config: { ...DEFAULTS }, source: "defaults", path: null, findings: [] };
  }
  let raw;
  try {
    raw = JSON.parse(readFileSync(path, "utf8"));
  } catch (e) {
    return {
      config: { ...DEFAULTS },
      source: "defaults",
      path,
      findings: [`not parseable as JSON: ${e.message}`],
    };
  }
  const findings = validatePatternConfig(raw);
  if (findings.length > 0) {
    return { config: { ...DEFAULTS }, source: "defaults", path, findings };
  }
  return { config: { ...DEFAULTS, ...raw }, source: "file", path, findings: [] };
}

// CLI entry point.
const invokedDirectly =
  process.argv[1] && resolve(process.argv[1]) === new URL(import.meta.url).pathname;

if (invokedDirectly) {
  const argv = process.argv.slice(2);
  const cmd = argv[0];
  let target = ".";
  for (let i = 1; i < argv.length; i++) {
    if (argv[i] === "--repo" || argv[i] === "--config") target = argv[++i];
  }
  if (cmd !== "validate" && cmd !== "show") {
    console.log("usage: pattern-config.mjs <validate|show> [--repo <root>] [--config <file>]");
    process.exit(cmd === "--help" || cmd === "-h" ? 0 : 2);
  }
  const result = loadPatternConfig(target);
  if (result.findings.length > 0) {
    console.error(`INVALID ${result.path}:`);
    for (const f of result.findings) console.error(`  ERROR: ${f}`);
    process.exit(1);
  }
  if (cmd === "validate") {
    console.log(
      result.source === "file"
        ? `OK: ${result.path}`
        : `OK: no ${CONFIG_FILENAME} found; template defaults apply`
    );
  } else {
    console.log(JSON.stringify({ source: result.source, ...result.config }, null, 2));
  }
  process.exit(0);
}
