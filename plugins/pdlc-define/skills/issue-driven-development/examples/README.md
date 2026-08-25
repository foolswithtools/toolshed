# Worked examples

Two synthetic, fully worked feature-slice issues showing the anatomy from
`${CLAUDE_PLUGIN_ROOT}/prompts/github-issue-template.md` Genre 1 end to end: header with a spec
anchor, why-this-slice, scope with verbatim interfaces, integration points
with `file:line` anchors, a test plan written first, falsifiable acceptance
criteria, out of scope, blocked-by, and docs as definition of done.

Both are written against `fixture-repo/`, an invented codebase for a
fictional trail-mapping app ("Trailmark"). Nothing here is a real product;
the fixture exists only so the linter has real files to resolve anchors
against.

```
fixture-repo/
  docs/specs/2026-08-01-trailmark-data.md
  src/trails/list.ts
```

Lint either example against the fixture:

```
node ${CLAUDE_PLUGIN_ROOT}/scripts/lint-issue.mjs \
  ${CLAUDE_PLUGIN_ROOT}/skills/issue-driven-development/examples/issue-1-elevation-profile.md \
  --genre feature \
  --repo ${CLAUDE_PLUGIN_ROOT}/skills/issue-driven-development/examples/fixture-repo

node ${CLAUDE_PLUGIN_ROOT}/scripts/lint-issue.mjs \
  ${CLAUDE_PLUGIN_ROOT}/skills/issue-driven-development/examples/issue-2-waypoint-search.md \
  --genre feature \
  --repo ${CLAUDE_PLUGIN_ROOT}/skills/issue-driven-development/examples/fixture-repo
```

Both exit 0.
