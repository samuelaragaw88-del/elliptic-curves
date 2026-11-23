"""Tests for the ec-point-count-bsgs task.

Expected counts in cases.json were computed offline and checked independently
(Hasse bound, group law on the curve and its twist, CM theory for special
curves). The agent never sees this file or cases.json.

The last test makes fresh random curves at test time. Their answers are not
stored anywhere; the agent's output is checked with the group law instead, so
a lookup table cannot pass.
"""
import json
import math
import os
import random
import subprocess
import sys
import time

import pytest

APP_DIR = os.environ.get("APP_DIR", "/app")
SCRIPT = os.path.join(APP_DIR, "count.py")
TIME_LIMIT = 10.0
CASES = json.load(open(os.path.join(os.path.dirname(__file__), "cases.json")))


def run(p, a, b):
    start = time.monotonic()
    proc = subprocess.run(
        [sys.executable, SCRIPT, str(p), str(a), str(b)],
        capture_output=True, text=True, timeout=TIME_LIMIT + 2, cwd=APP_DIR,
    )
    elapsed = time.monotonic() - start
    assert proc.returncode == 0, f"exit code {proc.returncode}: {proc.stderr[-500:]}"
    assert elapsed <= TIME_LIMIT, f"took {elapsed:.1f} s (limit {TIME_LIMIT} s)"
    out = proc.stdout.strip()
    assert out.isdigit(), f"output must be one integer, got {out[:80]!r}"
    return int(out)


def case_id(c):
    return f"p={c['p']}"


# --- Independent group-law checker (separate from the reference solution) ---

def _is_prime(n):
    if n < 2:
        return False
    small = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)
    for q in small:
        if n % q == 0:
            return n == q
    d, s = n - 1, 0
    while d % 2 == 0:
        d, s = d // 2, s + 1
    for a in small:
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


def _scalar_mult_is_identity(n, x, y, a, p):
    """True if n * (x, y) is the point at infinity, using Jacobian coordinates."""
    def dbl(P):
        X, Y, Z = P
        if Y == 0:
            return (1, 1, 0)
        S = 4 * X * Y * Y % p
        M = (3 * X * X + a * pow(Z, 4, p)) % p
        X3 = (M * M - 2 * S) % p
        return X3, (M * (S - X3) - 8 * pow(Y, 4, p)) % p, 2 * Y * Z % p

    def add(P, Q):
        if P[2] == 0:
            return Q
        if Q[2] == 0:
            return P
        X1, Y1, Z1 = P
        X2, Y2, Z2 = Q
        U1, U2 = X1 * Z2 * Z2 % p, X2 * Z1 * Z1 % p
        S1, S2 = Y1 * pow(Z2, 3, p) % p, Y2 * pow(Z1, 3, p) % p
        if U1 == U2:
            return dbl(P) if S1 == S2 else (1, 1, 0)
        H, R = (U2 - U1) % p, (S2 - S1) % p
        X3 = (R * R - H ** 3 - 2 * U1 * H * H) % p
        Y3 = (R * (U1 * H * H - X3) - S1 * H ** 3) % p
        return X3, Y3, H * Z1 * Z2 % p

    R, P = (1, 1, 0), (x % p, y % p, 1)
    while n:
        if n & 1:
            R = add(R, P)
        P = dbl(P)
        n >>= 1
    return R[2] == 0


def _random_point(a, b, p, rng):
    while True:
        x = rng.randrange(p)
        rhs = (x ** 3 + a * x + b) % p
        if rhs == 0:
            return x, 0
        if pow(rhs, (p - 1) // 2, p) == 1 and p % 4 == 3:
            return x, pow(rhs, (p + 1) // 4, p)


def _group_law_ok(p, a, b, n, rng, rounds=12):
    w = math.isqrt(4 * p)
    if not (p + 1 - w <= n <= p + 1 + w):
        return False
    d = 2
    while pow(d, (p - 1) // 2, p) != p - 1:
        d += 1
    at, bt = a * d * d % p, b * d ** 3 % p
    for _ in range(rounds):
        if not _scalar_mult_is_identity(n, *_random_point(a, b, p, rng), a, p):
            return False
        if not _scalar_mult_is_identity(2 * p + 2 - n, *_random_point(at, bt, p, rng), at, p):
            return False
    return True


# ------------------------------------------------------------------------------

def test_script_exists():
    assert os.path.isfile(SCRIPT), f"{SCRIPT} was not created"


@pytest.mark.parametrize("c", CASES["examples"], ids=case_id)
def test_examples(c):
    assert run(c["p"], c["a"], c["b"]) == c["count"]


@pytest.mark.parametrize("c", CASES["generic"], ids=case_id)
def test_hidden_curves(c):
    assert run(c["p"], c["a"], c["b"]) == c["count"]


@pytest.mark.parametrize("c", CASES["special"], ids=case_id)
def test_special_curves(c):
    """a = 0 or b = 0: CM curves, including supersingular ones with p + 1 points."""
    assert run(c["p"], c["a"], c["b"]) == c["count"]


@pytest.mark.parametrize("c", CASES["full_two_torsion"], ids=case_id)
def test_full_two_torsion(c):
    """Non-cyclic groups containing Z/2 x Z/2."""
    assert run(c["p"], c["a"], c["b"]) == c["count"]


def test_fresh_random_curves():
    """New curves every run; output checked by Hasse bound and group law only."""
    rng = random.SystemRandom()
    for _ in range(5):
        while True:
            p = rng.randrange(10 ** 11, 10 ** 13) | 3  # p = 3 mod 4 keeps square roots simple
            if _is_prime(p):
                break
        a, b = rng.randrange(p), rng.randrange(p)
        if (4 * a ** 3 + 27 * b * b) % p == 0:
            continue
        n = run(p, a, b)
        assert _group_law_ok(p, a, b, n, rng), f"wrong count {n} for p={p} a={a} b={b}"
