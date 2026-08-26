# pdlc-build

The build-phase companion to a running factory. pdlc-define owns the issue
discipline (writing a self-contained issue is valuable with or without a
factory); pdlc-build owns the actions a person takes against a factory that has
landed work for real.

Four operator actions, one job each: hand a GitHub issue to factory as a run,
read a run's verdict honestly, triage an escalation into a fixed issue, and check
credits before and after a metered run.

Two harnesses, one shared core: the skill and the four action procedures under
this directory are the only copy. The Claude Code plugin (`.claude-plugin/plugin.json`,
`commands/`) and the pi package (`package.json`'s `pi` key) both point at the same
`skills/` and `prompts/` directories; neither harness gets a duplicated copy.

## Commands

| Command | Job | Delineation |
|---|---|---|
| `/submit-run` | Fetch a GitHub issue, write it as a factory work item under a real work-item id, start the run, report the run id | pdlc-build acts against a running factory; pdlc-define wrote the issue |
| `/run-status` | Read the run's verdict and present the two scores and the two confidence legs without collapsing them | pdlc-build reads factory's verdict; pdlc-define reviews the branch |
| `/escalation-triage` | Walk an escalated run's reasons and produce a corrected issue body (that lints clean) or a documented retry decision | pdlc-build fixes the issue behind an escalation; pdlc-define authored the original |
| `/budget-check` | Read credits pre-run and post-run and append a row to a ledger you supply | pdlc-build meters a factory run; pdlc-define has no spend surface |

One line: pdlc-define defines the work; pdlc-build runs it through the factory and
reads what came back.

## What it ships

| Path | What it is |
|---|---|
| `skills/operating-factory-runs/SKILL.md` | The discipline behind the four actions: consume the interface, read the verdict honestly, fix the issue behind an escalation, meter every run |
| `prompts/submit-run.md` | Shared procedure: issue to work item to run to run id, with the pinned factory invocations |
| `prompts/run-status.md` | Shared procedure: read the verdict, keep the two scores and two legs apart |
| `prompts/escalation-triage.md` | Shared procedure: walk the reasons, fix the issue or document a retry |
| `prompts/budget-check.md` | Shared procedure: pre/post credits and a ledger append |
| `prompts/operator-constraints.md` | The constraints preamble every action carries |
| `commands/*.md` | The four Claude Code commands; each is a thin wrapper that runs its shared procedure, no reimplementation |
| `scripts/check-credits.sh` | The credits wrapper budget-check uses: reads OpenRouter `GET /api/v1/credits` `data.total_usage` to nine decimals, appends a ledger row |
| `scripts/check-links.sh` | Repo-side check that no skill/command/prompt references anything outside the plugin |
| `scripts/check-public-hygiene.sh` | Deny-list sweep proving no file under the plugin tree contains a banned string (deny list supplied at run time, never committed) |
| `scripts/check-no-pi-duplication.sh` | Proves the pi manifest points at the shared `skills/` and `prompts/`, no file elsewhere duplicates their content, and every command wraps a shared procedure |
| `package.json` | The pi package manifest: `pi.skills` and `pi.prompts` reference `./skills` and `./prompts` directly, no copy |
| `scripts/tests/` | The plugin's verification suite (`sh scripts/tests/run-tests.sh`) and the pi package smoke test (`sh scripts/tests/run-pi-smoke-tests.sh`) |

## Install (Claude Code)

```
/plugin marketplace add https://github.com/foolswithtools/toolshed.git
/plugin install pdlc-build@toolshed
```

The skill loads on demand; the four commands register as `/submit-run`,
`/run-status`, `/escalation-triage`, `/budget-check`. Shared procedures resolve
from `${CLAUDE_PLUGIN_ROOT}/prompts/`.

## pi package

pi is the second harness (the factory's own backend, and the client team's daily
driver), so the same skill and action procedures install with one pi command.
`package.json` carries the pi manifest (the `pi` key), pointing at the shared
`skills/` and `prompts/` directories this plugin already ships; nothing is copied
for pi.

```json
{
  "pi": {
    "skills": ["./skills"],
    "prompts": ["./prompts"]
  }
}
```

Install (verified against pi 0.84.2):

```
pi install /path/to/toolshed/plugins/pdlc-build
```

This is the narrowest form pi 0.84.2 supports for a plugin nested inside a larger
repo: pi's `git:` source has no subpath syntax, so clone first, then install the
subdirectory as a local path (the same convention pdlc-define documents). Add `-l`
to install project-locally instead of to user settings.

In pi the four actions are the shared procedure prompts; the credits script runs
from the installed package path directly:

```
bash /path/to/toolshed/plugins/pdlc-build/scripts/check-credits.sh read
```

`scripts/tests/run-pi-smoke-tests.sh` installs the package into an isolated,
throwaway pi settings scope (never `~/.pi/agent`), confirms pi's own resolver
discovers the skill and all action procedures, runs the credits script against a
fixture, and runs `check-no-pi-duplication.sh`. It makes no model call and needs
no provider key; it skips (exit 0) if `pi` is not on `PATH`.

## What a live run needs

A `/submit-run` live build (`backend = pi`, `model = z-ai/glm-5.3`, `effort =
high`) runs against a factory checkout and spends OpenRouter credits. It needs:

- A factory checkout with the `factory` binary built and its
  `scripts/scoped-creds.sh` wrapper (see the factory checkout's `docs/QUICKSTART.md`
  and `docs/CREDENTIALS.md`).
- Docker, for the agent container (build it with the factory checkout's
  `scripts/build-agent-pi-image.sh`) and the held-out executor (a node-bearing
  image, pulled on first use).
- The work directory initialized as a git repo with the scaffold committed before
  the run (factory runs each attempt in a git worktree of the work dir's HEAD).
- For the app's own build and typecheck gates to pass rather than escalate, the
  app type's toolchain provisioned into the work dir (for the wedge, the pinned
  TypeScript devDependencies under `support/`, per the factory checkout's
  `docs/PREREQUISITES.md`).

## Reading the verdict honestly

Two scores, never merged:

- `framework-portability: PASS|FAIL` - did the loop run to a written verdict at
  all (host-tooling independent).
- `app-buildability: PASS|PARTIAL|FAIL` - did the app's own gates actually execute
  and pass (from `validation_rate`).

And `land` is a two-leg AND of the confidence leg (`confidence_land`, driven by
blocking gates plus the held-out rate against its threshold and the gap against
its gap-threshold) and the governance leg (`governance_cleared`). `/run-status`
prints both scores and both legs separately and carries the `thresholds:
uncalibrated defaults` banner when factory prints it.

## The pdlc family

pdlc-build is the second plugin in the `pdlc-*` family, covering phase 5 (Build).
See the toolshed README for the family table.
