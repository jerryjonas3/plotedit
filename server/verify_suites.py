#!/usr/bin/env python3
"""Test the tests: break each suite on purpose and check it actually fails.

    cd server && python3 verify_suites.py

⭐ WHY THIS EXISTS. Twice on 2026.09.23 a suite printed its pass/fail verdict in
the MIDDLE of the file, so anything appended after it ran without affecting the
exit code — the suite could report failures and still exit 0. Both were found by
accident. A suite that can pass while failing is worse than no suite, because it
is the thing you stop checking.

⚠ And the first two attempts to prove a break were themselves broken: one
mutated a line the assertion never looked at, the other inserted an unindented
statement into an indented block so the run died of IndentationError and "exited
1" for the wrong reason. Hence the care below — the poison goes in at TOP LEVEL
only, and a run that dies of a syntax error is reported as unverified, not as a
pass.

    A test you have never watched fail is not yet a test.
"""
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).parent
POISON = "DELIBERATE BREAK — inserted by verify_suites.py"


def _inject(src):
    """(broken_source, where) — a failure recorded at TOP LEVEL, mid-file."""
    lines = src.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if line.startswith("check("):
            return "".join(lines[:i]) + f'check("{POISON}", 1, 2)\n' + "".join(lines[i:]), i + 1
        if line.startswith("fails.append("):
            return "".join(lines[:i]) + f'fails.append("{POISON}")\n' + "".join(lines[i:]), i + 1
    # Suites that only record failures inside loops: put it after the first
    # top-level print that follows the loop.
    for i, line in enumerate(lines):
        if line.startswith("print(") and i > len(lines) // 3:
            kind = "fails.append" if "fails" in src else "check"
            stmt = (f'fails.append("{POISON}")\n' if kind == "fails.append"
                    else f'check("{POISON}", 1, 2)\n')
            return "".join(lines[:i + 1]) + stmt + "".join(lines[i + 1:]), i + 2
    return None, None


def main():
    bad = []
    print(f"{'suite':20s} {'break':>9}  {'exit':>4}  {'named':>5}  verdict")
    print("-" * 64)
    for f in sorted(HERE.glob("test_*.py")):
        src = f.read_text()
        broken, where = _inject(src)
        if broken is None:
            print(f"{f.name:20s} {'—':>9}  could not inject — UNVERIFIED")
            bad.append(f.name)
            continue
        f.write_text(broken)
        try:
            r = subprocess.run([sys.executable, f.name], cwd=HERE,
                               capture_output=True, text=True, timeout=180)
        finally:
            f.write_text(src)          # always put it back, even on a crash
        syntax = "SyntaxError" in r.stderr or "IndentationError" in r.stderr
        named = POISON in r.stdout
        ok = r.returncode == 1 and named and not syntax
        note = "ok" if ok else ("UNVERIFIED (my injection broke the file)" if syntax
                                else "🔴 REPORTS SUCCESS WHILE FAILING")
        print(f"{f.name:20s} {'line ' + str(where):>9}  {r.returncode:>4}  {str(named):>5}  {note}")
        if not ok:
            bad.append(f.name)

    print()
    if bad:
        print(f"{len(bad)} suite(s) could not be shown to fail: {', '.join(bad)}")
        return 1
    print("every suite fails when broken, and names what broke")
    return 0


if __name__ == "__main__":
    sys.exit(main())
