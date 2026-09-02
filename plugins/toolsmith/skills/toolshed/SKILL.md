---
name: toolshed
description: Use when the user asks what tools, skills, or plugins are available, says "check the toolshed", or wants to know whether an existing tool already covers the task before building something new. Lists installed toolshed skills with their descriptions.
version: 0.1.0
disable-model-invocation: false
---

# Toolshed listing

List the tools already available so the user can reuse instead of rebuild.

## Steps

1. Run the enumerator from the plugin root:

   `bash "${CLAUDE_PLUGIN_ROOT}/scripts/list-toolshed.sh"`

2. Present the result as a short list, grouped if long. For each tool give its
   name and its one-line description.

3. If the user described a task, say plainly whether any listed tool looks like
   a fit, and name it. If nothing fits, say so in one line and continue; do not
   invent a match.
