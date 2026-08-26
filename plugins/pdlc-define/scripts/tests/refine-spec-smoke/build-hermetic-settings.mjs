#!/usr/bin/env node
// Reads `claude plugin list --json` from stdin and writes a settings JSON
// object (to stdout) that disables every installed plugin named
// "pdlc-define", regardless of which marketplace nickname it was installed
// under on this machine.
//
// The smoke loads the plugin under test with `--plugin-dir`, but a
// user-scope install of the same plugin (e.g. from the toolshed
// marketplace, installed under any local nickname) otherwise wins over
// `--plugin-dir` and can silently shadow the checkout with a stale version.
// Disabling by discovered id rather than a hardcoded marketplace name keeps
// this hermetic on any machine, not just the one it was written on.
let data = '';
process.stdin.on('data', (chunk) => {
  data += chunk;
});
process.stdin.on('end', () => {
  let installed = [];
  try {
    installed = JSON.parse(data || '[]');
  } catch {
    installed = [];
  }

  const disabled = {};
  if (Array.isArray(installed)) {
    for (const plugin of installed) {
      if (plugin && typeof plugin.id === 'string' && plugin.id.split('@')[0] === 'pdlc-define') {
        disabled[plugin.id] = false;
      }
    }
  }

  process.stdout.write(`${JSON.stringify({ enabledPlugins: disabled })}\n`);
});
