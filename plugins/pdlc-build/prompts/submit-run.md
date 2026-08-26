# submit-run: hand a GitHub issue to factory as a run

Take a GitHub issue, write it as a factory work item under a real work-item id,
start the run against a factory checkout, and report the run id back. This is the
shared procedure both harnesses run; the Claude Code `/submit-run` command and the
pi `submit-run` prompt both execute exactly these steps.

Prepend the constraints preamble (`operator-constraints`) before you act.

## Inputs

- The GitHub issue: `<owner/repo>#<number>` (or a URL to one).
- The factory checkout directory (the repo that holds the `factory` binary and
  `scripts/scoped-creds.sh`).
- The work directory to create for this run (a fresh path; `factory init` refuses
  to overwrite an initialized dir).
- The backend and model. For a live build use `backend = pi`, `model =
  z-ai/glm-5.3` (the cheapest ratified builder), `effort = high`. For a dry
  structural check with zero model spend use `backend = mock`.

## Pinned factory invocations (verbatim)

Pinned at authoring time against factory `main` (`factory 0.1.0`, commit
`ff10bd0`). factory selects backend, model, effort, image, egress, and limits
from `<work-dir>/factory.config` keys, never from CLI flags; the CLI takes only a
positional `<dir>`. Re-verify against the factory checkout before a run (the
kickoff preflight rule): `factory --help` and the `factory.config` template
`factory init` writes.

1. Scaffold the work directory:

   ```
   factory init <work-dir>
   ```

2. Write the work item to `<work-dir>/work-item.txt`. The first line carries the
   real work-item id; factory#7's run-identity convention for a GitHub-derived
   item is `gh-<owner/repo>#<number>`. Then the title, a blank line, and the body:

   ```
   id: gh-<owner/repo>#<number>
   <issue title>

   <issue body>
   ```

3. Select the live builder in `<work-dir>/factory.config` (replacing the default
   `backend = mock` line):

   ```
   factory-config v1
   backend = pi
   model = z-ai/glm-5.3
   effort = high
   ```

4. Make the work directory a git repository and commit the scaffold before the
   run. factory runs each attempt in a git worktree of the work dir's HEAD, so an
   uninitialized work dir fails the agent step outright:

   ```
   ( cd <work-dir> \
     && git init -q \
     && git -c user.email=op@localhost -c user.name=op add -A \
     && git -c user.email=op@localhost -c user.name=op commit -q -m "scaffold" )
   ```

   For the app's own gates (build, typecheck) to run rather than escalate on a
   missing toolchain, provision the app type's toolchain into the work dir first
   (for the wedge, the pinned TypeScript devDependencies under `support/`, per the
   factory checkout's `docs/PREREQUISITES.md`); commit it in the scaffold so the
   attempt worktree carries it. Without it the run still completes to an honest
   verdict, it just escalates on the build gate.

5. Start the run through the factory checkout's scoped-credential wrapper, so the
   run gets only `OPENROUTER_API_KEY` and nothing else:

   ```
   scripts/scoped-creds.sh pi -- ./target/release/factory run <work-dir>
   ```

   Run this in the foreground (or poll in-session): a live run killed by an ending
   turn wastes its spend.

## Steps

1. Fetch the issue body: `gh issue view <number> --repo <owner/repo> --json
   title,body -q '.title, .body'` (or read a local issue file when the issue is not
   on GitHub). Do not invent a body; if the fetch fails, stop and report.
2. Run `factory init <work-dir>`. If it refuses because the dir is initialized,
   pick a fresh path rather than deleting someone's work.
3. Write `work-item.txt` with the `id: gh-<owner/repo>#<number>` line, the title,
   and the fetched body verbatim.
4. Set `factory.config` to the live builder block above (or `backend = mock` for a
   zero-spend structural check).
5. For a live run: read credits first with `/budget-check` (pre), launch the run
   through `scripts/scoped-creds.sh pi -- ...`, then read credits again (post) and
   append the ledger row. Stay in-session until the run process exits.
6. Read the run id back from `<work-dir>/.factory/last-run.txt`: the id is
   `work_item_id` plus `attempt_id` (for example `gh-<owner/repo>#<number> / AT-1`).
   The verdict file is at
   `<work-dir>/.factory/verdicts/<work_item_id>/<attempt_id>.verdict`.

## Report

Report the run id (`work_item_id` and `attempt_id`), the outcome line factory
printed (`Merged`, `Escalated`, or a refusal), the verdict file path, and, for a
live run, the pre and post credits figures with the settled delta. Do not declare
a run landed unless the verdict file says `land = true`; hand the verdict to
`run-status` for the honest read. When factory created a merge branch on a real
land, report the branch and leave the merge to the human.
