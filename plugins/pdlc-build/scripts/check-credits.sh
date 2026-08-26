#!/usr/bin/env bash
# check-credits.sh: read the OpenRouter credits balance and, optionally, append a
# ledger row. Wrapped by pdlc-build's budget-check action for pre-run and post-run
# checks around a metered factory run.
#
# The authoritative metered figure is OpenRouter's GET /api/v1/credits field
# data.total_usage (nine decimals): the generations API is by-request-id only and
# the pi backend surfaces no ids, so the credits delta is the ledger of record.
# The credits read is not a model call and costs nothing.
#
# The credential is read from OPENROUTER_API_KEY in the environment (inject it
# least-privilege via a factory checkout's scripts/scoped-creds.sh pi -- ...). The
# key is never echoed, logged, or written to the ledger.
#
# Usage:
#   check-credits.sh read   [--from-file <json>]
#   check-credits.sh append --ledger <path> --phase <pre|post> --label <label> \
#                           [--from-file <json>]
#
# --from-file reads a credits-API JSON payload from a file instead of calling the
# network (used by the self-test and by anyone reconciling a captured snapshot).
#
# The plugin user brings their own ledger: --ledger is required for append and is
# never defaulted to a path this plugin owns.
#
# Exit 0 on success; exit 1 on an API or parse failure; exit 2 on a usage error.
set -u

CREDITS_URL="${OPENROUTER_CREDITS_URL:-https://openrouter.ai/api/v1/credits}"

usage() {
  cat >&2 <<'EOF'
Usage:
  check-credits.sh read   [--from-file <json>]
  check-credits.sh append --ledger <path> --phase <pre|post> --label <label> [--from-file <json>]
EOF
}

if [ "$#" -lt 1 ]; then
  usage
  exit 2
fi

cmd="$1"
shift

case "$cmd" in
  read|append) ;;
  *) echo "check-credits.sh: unknown command '$cmd'" >&2; usage; exit 2 ;;
esac

from_file=""
ledger=""
phase=""
label=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --from-file) from_file="${2:-}"; shift 2 ;;
    --ledger)    ledger="${2:-}"; shift 2 ;;
    --phase)     phase="${2:-}"; shift 2 ;;
    --label)     label="${2:-}"; shift 2 ;;
    *) echo "check-credits.sh: unknown argument '$1'" >&2; usage; exit 2 ;;
  esac
done

if ! command -v node >/dev/null 2>&1; then
  echo "check-credits.sh: node is required for JSON parsing" >&2
  exit 1
fi

# fetch_payload: print the raw credits JSON to stdout, from a file or the API.
fetch_payload() {
  if [ -n "$from_file" ]; then
    if [ ! -f "$from_file" ]; then
      echo "check-credits.sh: --from-file not found: $from_file" >&2
      return 1
    fi
    cat "$from_file"
    return 0
  fi

  if [ -z "${OPENROUTER_API_KEY:-}" ]; then
    echo "check-credits.sh: OPENROUTER_API_KEY is not set (inject it via scoped-creds.sh pi)" >&2
    return 1
  fi
  if ! command -v curl >/dev/null 2>&1; then
    echo "check-credits.sh: curl is required for the live credits read" >&2
    return 1
  fi
  # The key is passed to curl via an env-var reference, never interpolated into a
  # logged command line.
  curl -fsS -H "Authorization: Bearer ${OPENROUTER_API_KEY}" "$CREDITS_URL"
}

# extract_usage: read data.total_usage from the JSON on stdin, print to 9 decimals.
extract_usage() {
  node -e '
    let raw = "";
    process.stdin.on("data", (d) => (raw += d));
    process.stdin.on("end", () => {
      let obj;
      try { obj = JSON.parse(raw); } catch (e) {
        console.error("check-credits.sh: credits payload is not valid JSON");
        process.exit(1);
      }
      const u = obj && obj.data && obj.data.total_usage;
      if (typeof u !== "number" || Number.isNaN(u)) {
        console.error("check-credits.sh: data.total_usage missing or not a number");
        process.exit(1);
      }
      process.stdout.write(u.toFixed(9));
    });
  '
}

payload="$(fetch_payload)" || exit 1
usage_val="$(printf '%s' "$payload" | extract_usage)" || exit 1

case "$cmd" in
  read)
    printf '%s\n' "$usage_val"
    ;;
  append)
    if [ -z "$ledger" ]; then
      echo "check-credits.sh: append requires --ledger <path>" >&2
      usage
      exit 2
    fi
    case "$phase" in
      pre|post) ;;
      *) echo "check-credits.sh: append requires --phase pre|post" >&2; exit 2 ;;
    esac
    if [ -z "$label" ]; then
      echo "check-credits.sh: append requires --label <label>" >&2
      exit 2
    fi
    ledger_dir="$(dirname "$ledger")"
    if [ ! -d "$ledger_dir" ]; then
      echo "check-credits.sh: ledger directory does not exist: $ledger_dir" >&2
      exit 2
    fi
    ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    printf '%s\t%s\t%s\t%s\n' "$ts" "$phase" "$label" "$usage_val" >> "$ledger"
    printf '%s\n' "$usage_val"
    ;;
  *)
    echo "check-credits.sh: unknown command '$cmd'" >&2
    usage
    exit 2
    ;;
esac
