#!/usr/bin/env python3
"""Cross-check the reference solution against direct counting on small primes.

Direct count: #E(F_p) = p + 1 + sum over x of legendre(x^3 + a x + b, p).
This is independent of the baby-step giant-step code. It is only fast for
small p, which is exactly why the task needs a better method for p ~ 10^12.

Usage: python tools/brute_force_check.py [number_of_curves]
"""
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ec-point-count-bsgs", "solution"))
from count import count_points, is_prime, legendre  # noqa: E402


def direct_count(p, a, b):
    return p + 1 + sum(legendre(x * x * x + a * x + b, p) for x in range(p))


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    rng = random.Random(2026)
    checked = 0
    while checked < n:
        p = rng.randrange(300, 40000)
        if not is_prime(p):
            continue
        a, b = rng.randrange(p), rng.randrange(p)
        if (4 * a ** 3 + 27 * b ** 2) % p == 0:
            continue
        expected = direct_count(p, a, b)
        got = count_points(p, a, b)
        if got != expected:
            print(f"MISMATCH p={p} a={a} b={b}: direct={expected} bsgs={got}")
            return 1
        checked += 1
    print(f"OK: {checked} random curves over primes 300..40000 match direct counting")
    return 0


if __name__ == "__main__":
    sys.exit(main())
