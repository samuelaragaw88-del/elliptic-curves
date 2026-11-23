#!/usr/bin/env python3
"""Generate the public examples and the hidden test cases, and verify every answer.

Each expected count is computed by the reference solution and then checked
independently of it:

  * Hasse bound: |N - (p + 1)| <= 2 sqrt(p).
  * Group law: N * P = O for 25 random points P on E, and
    (2p + 2 - N) * Q = O for 25 random points Q on the quadratic twist.
  * CM theory (special curves only), using Cornacchia's algorithm, which shares
    no code with baby-step giant-step:
      - y^2 = x^3 + b,  p = 2 mod 3: N = p + 1 (supersingular).
      - y^2 = x^3 + b,  p = 1 mod 3: p = u^2 + 3v^2 and the trace is one of
        +-2u, +-(u + 3v), +-(u - 3v).
      - y^2 = x^3 + a x, p = 3 mod 4: N = p + 1 (supersingular).
      - y^2 = x^3 + a x, p = 1 mod 4: p = u^2 + v^2 and the trace is one of
        +-2u, +-2v.
  * Optional: tools/check_with_pari.gp recomputes every count with PARI/GP.

Usage: python tools/make_cases.py
Writes ec-point-count-bsgs/environment/examples.txt and
ec-point-count-bsgs/tests/cases.json.
"""
import json
import math
import os
import random
import sys

ROOT = os.path.join(os.path.dirname(__file__), "..", "ec-point-count-bsgs")
sys.path.insert(0, os.path.join(ROOT, "solution"))
from count import Curve, count_points, hasse_interval, is_prime, legendre, sqrt_mod  # noqa: E402

LO_P, HI_P = 10 ** 11, 10 ** 13


def cornacchia(d, p):
    """Find (u, v) with u^2 + d v^2 = p, or None."""
    r0 = sqrt_mod(-d % p, p)
    if r0 is None or (r0 * r0 + d) % p:
        return None
    if r0 < p // 2:
        r0 = p - r0
    a, b = p, r0
    limit = math.isqrt(p)
    while b > limit:
        a, b = b, a % b
    rest = p - b * b
    if rest % d:
        return None
    v2 = rest // d
    v = math.isqrt(v2)
    return (b, v) if v * v == v2 else None


def cm_traces(p, a, b):
    """Possible traces from CM theory, or None if the curve is not special."""
    if a % p == 0:
        if p % 3 == 2:
            return {0}
        u, v = cornacchia(3, p)
        return {s * t for s in (1, -1) for t in (2 * u, u + 3 * v, u - 3 * v)}
    if b % p == 0:
        if p % 4 == 3:
            return {0}
        u, v = cornacchia(1, p)
        return {s * t for s in (1, -1) for t in (2 * u, 2 * v)}
    return None


def verify(p, a, b, n, rng):
    lo, hi = hasse_interval(p)
    assert lo <= n <= hi, "Hasse bound"
    E = Curve(p, a, b)
    d = 2
    while legendre(d, p) != -1:
        d += 1
    T = Curve(p, a * d * d, b * d ** 3)
    for _ in range(25):
        assert E.mul(n, E.random_point(rng)) is None, "N * P != O"
        assert T.mul(2 * p + 2 - n, T.random_point(rng)) is None, "twist check"
    traces = cm_traces(p, a, b)
    if traces is not None:
        assert (p + 1 - n) in traces, "CM trace check"
        return "group law + CM"
    return "group law"


def random_prime(rng, cond=lambda p: True):
    while True:
        p = rng.randrange(LO_P, HI_P) | 1
        if is_prime(p) and cond(p):
            return p


def nonsingular(p, a, b):
    return (4 * a ** 3 + 27 * b ** 2) % p != 0


def full_two_torsion(rng):
    """Curve with three roots r1 + r2 + r3 = 0, so E has Z/2 x Z/2 inside."""
    while True:
        p = random_prime(rng)
        r1, r2 = rng.randrange(1, p), rng.randrange(1, p)
        r3 = (-r1 - r2) % p
        if len({r1, r2, r3}) < 3:
            continue
        a = (r1 * r2 + r1 * r3 + r2 * r3) % p
        b = (-r1 * r2 * r3) % p
        if nonsingular(p, a, b):
            return p, a, b


def main():
    rng = random.Random(20261122)
    groups = {"examples": [], "generic": [], "special": [], "full_two_torsion": []}

    def add(group, p, a, b):
        n = count_points(p, a, b)
        how = verify(p, a, b, n, rng)
        groups[group].append({"p": p, "a": a, "b": b, "count": n, "verified_by": how})

    for _ in range(3):
        p = random_prime(rng)
        add("examples", p, rng.randrange(p), rng.randrange(p))
    for _ in range(12):
        p = random_prime(rng)
        a, b = rng.randrange(p), rng.randrange(p)
        if nonsingular(p, a, b):
            add("generic", p, a, b)
    for cond, kind in [(lambda p: p % 3 == 1, "a0"), (lambda p: p % 3 == 2, "a0"),
                       (lambda p: p % 4 == 1, "b0"), (lambda p: p % 4 == 3, "b0")]:
        for _ in range(2):
            p = random_prime(rng, cond)
            x = rng.randrange(1, p)
            add("special", p, 0, x) if kind == "a0" else add("special", p, x, 0)
    for _ in range(3):
        add("full_two_torsion", *full_two_torsion(rng))

    with open(os.path.join(ROOT, "environment", "examples.txt"), "w") as f:
        f.write("# p a b -> number of points on y^2 = x^3 + a x + b over F_p\n")
        for c in groups["examples"]:
            f.write(f"{c['p']} {c['a']} {c['b']} -> {c['count']}\n")
    hidden = {k: v for k, v in groups.items()}
    with open(os.path.join(ROOT, "tests", "cases.json"), "w") as f:
        json.dump(hidden, f, indent=2)
        f.write("\n")
    total = sum(len(v) for v in groups.values())
    print(f"Wrote {total} verified cases:")
    for k, v in groups.items():
        print(f"  {k:17s} {len(v):2d}  ({', '.join(sorted({c['verified_by'] for c in v}))})")


if __name__ == "__main__":
    main()
