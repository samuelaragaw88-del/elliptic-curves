#!/usr/bin/env python3
"""Optional extra check: recompute every expected count with PARI/GP's ellcard.

Needs PARI/GP installed (Ubuntu/Debian: sudo apt install pari-gp; macOS:
brew install pari). PARI is a completely separate implementation, so a match
here is a strong confirmation of tests/cases.json.

Usage: python tools/check_with_pari.py
"""
import json
import os
import shutil
import subprocess
import sys

ROOT = os.path.join(os.path.dirname(__file__), "..", "ec-point-count-bsgs")


def main():
    if not shutil.which("gp"):
        print("PARI/GP (gp) is not installed; see the header of this file.")
        return 2
    cases = json.load(open(os.path.join(ROOT, "tests", "cases.json")))
    flat = [c for group in cases.values() for c in group]
    script = "\n".join(
        f"print(ellcard(ellinit([{c['a']},{c['b']}],{c['p']})));" for c in flat
    ) + "\nquit;\n"
    out = subprocess.run(["gp", "-q", "-f"], input=script, capture_output=True,
                         text=True, check=True).stdout.split()
    bad = [(c, int(v)) for c, v in zip(flat, out) if int(v) != c["count"]]
    for c, v in bad:
        print(f"MISMATCH p={c['p']} a={c['a']} b={c['b']}: cases.json={c['count']} PARI={v}")
    if len(out) != len(flat):
        print(f"PARI returned {len(out)} values for {len(flat)} cases")
        return 1
    if bad:
        return 1
    print(f"OK: all {len(flat)} counts in tests/cases.json match PARI/GP ellcard")
    return 0


if __name__ == "__main__":
    sys.exit(main())
