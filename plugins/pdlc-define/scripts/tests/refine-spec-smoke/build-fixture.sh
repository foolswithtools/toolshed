#!/usr/bin/env bash
# Builds the refine-spec cold-session smoke fixture: a tiny consumer repo with
# a deliberately flawed vision document (three stances: one defensible, one
# factually wrong, one vague), a two-entry decision log, and a docs/panel/ of
# two persona memos for critic casting. Everything here is synthetic and
# names nothing private.
#
# Usage: build-fixture.sh <dest-dir>
# Creates <dest-dir> (must not already exist as a repo) and populates it.
set -eu

dest="${1:-}"
if [ -z "$dest" ]; then
  echo "usage: build-fixture.sh <dest-dir>" >&2
  exit 2
fi

mkdir -p "$dest/docs/panel" "$dest/docs/decisions"

cat > "$dest/docs/VISION.md" <<'EOF'
# Ledger: vision

Ledger is a small self-hosted expense tracker for a household of a few users.
This document states the product's current stances. It is a draft awaiting
refinement.

## Stance 1: CLI first, GUI later

The first shippable Ledger is a command-line tool. A web GUI is worth building
only after the core import-and-report loop earns daily use. Shipping the CLI
first keeps the surface small and the feedback fast.

## Stance 2: Postgres from day one

Ledger must run Postgres from the first release. SQLite cannot serve more than
one reader at a time, so a household with two people looking at their expenses
at once would corrupt the database. A real server database is the only safe
option even at this tiny scale.

## Stance 3: it should feel good to use

Ledger should be fast and delightful. The experience should spark joy and users
should love reaching for it. That is the bar.
EOF

cat > "$dest/docs/decisions/DECISIONS.md" <<'EOF'
# Ledger: decision log

Stamped decisions only. The repo owner stamps; nothing lands here without an
explicit owner decision.

## D-001: single-household scope (stamped 2026-07-30)

Ledger targets one household, not multi-tenant SaaS. Every scaling choice is
read through that lens.

## D-002: plain-text import format (stamped 2026-08-05)

Ledger imports CSV exports from banks, not a proprietary binary format. Import
code stays inspectable and testable against fixture files.
EOF

cat > "$dest/docs/panel/skeptical-buyer.md" <<'EOF'
# Panel persona: the skeptical buyer

You are a careful household decision-maker evaluating whether to adopt a new
tool. You have been burned by abandonware. You ask: what does this do that a
spreadsheet does not, what is the switching cost, and what happens to my data
if the project dies. You are unmoved by adjectives; you want a concrete reason
to change your routine. You pressure-test vague value claims until they name a
specific job the tool does better than the status quo.
EOF

cat > "$dest/docs/panel/burned-operator.md" <<'EOF'
# Panel persona: the burned operator

You are the person who will actually run this thing on a home server at 11pm
when it breaks. You have carried a pager. You ask about backups, restore drills,
upgrade paths, and what the failure modes look like when nobody is watching. You
are deeply suspicious of infrastructure chosen for imagined scale rather than
real load, because you are the one who has to maintain it.
EOF

cat > "$dest/CONVENTIONS.md" <<'EOF'
# Ledger: repo conventions

- Document economy: this repo keeps a deliberately small doc set (VISION,
  DECISIONS, panel memos, this file). Do not create new top-level documents
  without flagging this rule first and getting an explicit go-ahead.
- Style gate: prose uses plain sentences. No em dashes.
- Commit style: every commit message states why, not just what.
EOF

# Make it a git repo so the session can commit per the consumer workflow and so
# "no new documents created" is checkable from the working tree.
if command -v git >/dev/null 2>&1; then
  (
    cd "$dest"
    git init -q
    git config user.email "smoke@example.invalid"
    git config user.name "smoke fixture"
    git add -A
    git commit -q -m "chore: seed Ledger fixture (vision, decisions, panel)"
  )
fi

echo "fixture built at $dest"
