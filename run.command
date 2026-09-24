#!/bin/bash
# Start plotedit. Double-click this file on a Mac, or run ./run.command
#
# ⭐ Jerry, 2026.09.24: "it would be nice to set it up so that users that aren't
# familiar with it at all could download it and run it."
#
# ⚠ Everything it does is reversible and stays inside this folder: it makes a
# .venv here, installs the Python packages into THAT, and starts a server on
# your own machine. It does not touch your system Python and it installs
# nothing globally. Deleting this folder removes every trace except the plots
# you saved.
set -euo pipefail
cd "$(dirname "$0")"

say() { printf '\n  %s\n' "$*"; }
die() { printf '\n  ✗ %s\n\n' "$*" >&2; read -r -p "  Press return to close." _; exit 1; }

# --- Python ---------------------------------------------------------------
PY=""
for c in python3.12 python3.11 python3; do
  if command -v "$c" >/dev/null 2>&1; then
    v=$("$c" -c 'import sys; print("%d.%d" % sys.version_info[:2])' 2>/dev/null || echo 0)
    # ⚠ Checked, not assumed. macOS ships a python3 that is often too old, and
    # the failure it produces otherwise is a wall of pip errors that says
    # nothing about the actual problem.
    if [ "$(printf '%s\n3.10\n' "$v" | sort -V | head -1)" = "3.10" ]; then PY="$c"; break; fi
  fi
done
[ -n "$PY" ] || die "plotedit needs Python 3.10 or newer.
    Install it from https://www.python.org/downloads/ and run this again."

# --- dependencies, in a folder of our own ---------------------------------
if [ ! -d .venv ]; then
  say "First run — setting up. This takes a minute, and only happens once."
  "$PY" -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r server/requirements.txt

# --- the editor -----------------------------------------------------------
# A release download already has web/dist. A git clone does not, so build it if
# Node is here — and say plainly what is missing if it is not, rather than
# starting a server that serves a 503.
if [ ! -f web/dist/index.html ]; then
  if command -v npm >/dev/null 2>&1; then
    say "Building the editor (first run only)…"
    (cd web && npm install --silent && npm run build >/dev/null)
  else
    die "The editor has not been built, and Node is not installed.
    Either download a release (which has it built already),
    or install Node from https://nodejs.org and run this again."
  fi
fi

say "Starting plotedit — your browser will open in a moment."
say "Leave this window open while you work. Close it, or press ctrl-C, to stop."
exec python server/serve.py
