#!/usr/bin/env python3
"""Reference solution: count points on y^2 = x^3 + a x + b over F_p.

Usage: python count.py p a b
Prints #E(F_p), including the point at infinity.

Method (Mestre's baby-step giant-step):
  1. Hasse: N = #E(F_p) lies in [p + 1 - 2*sqrt(p), p + 1 + 2*sqrt(p)].
  2. Take a random point P. Baby-step giant-step finds one N0 in that
     interval with N0 * P = O, in about p^(1/4) group operations.
  3. Factor N0 to get the exact order of P. Every valid N is a multiple of it.
  4. The quadratic twist E' has N' = 2p + 2 - N points, so points on E'
     give a second congruence on N. Combine congruences (CRT) on random
     points of E and E' until exactly one N is left in the Hasse interval.
     Mestre's theorem guarantees this ends for p > 229.

Pure Python 3 standard library only.
"""
import math
import random
import sys

# ---------------------------------------------------------------------------
# Number theory helpers
# ---------------------------------------------------------------------------

_MR_BASES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)


def is_prime(n):
    """Deterministic Miller-Rabin, correct for n < 3.3 * 10^24."""
    if n < 2:
        return False
    for q in _MR_BASES:
        if n % q == 0:
            return n == q
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for a in _MR_BASES:
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


def pollard_rho(n, rng):
    if n % 2 == 0:
        return 2
    while True:
        c = rng.randrange(1, n)
        f = lambda v: (v * v + c) % n
        x = y = rng.randrange(2, n)
        d = 1
        while d == 1:
            x = f(x)
            y = f(f(y))
            d = math.gcd(abs(x - y), n)
        if d != n:
            return d


def prime_factors(n, rng):
    """Set of distinct prime factors of n."""
    out = set()
    stack = [n]
    while stack:
        m = stack.pop()
        if m == 1:
            continue
        for q in (2, 3, 5, 7, 11, 13):
            if m % q == 0:
                out.add(q)
                while m % q == 0:
                    m //= q
        if m == 1:
            continue
        if is_prime(m):
            out.add(m)
            continue
        d = pollard_rho(m, rng)
        stack.extend((d, m // d))
    return out


def legendre(n, p):
    n %= p
    if n == 0:
        return 0
    return 1 if pow(n, (p - 1) // 2, p) == 1 else -1


def sqrt_mod(n, p):
    """Tonelli-Shanks square root of a quadratic residue n modulo prime p."""
    n %= p
    if n == 0:
        return 0
    if p % 4 == 3:
        return pow(n, (p + 1) // 4, p)
    q, s = p - 1, 0
    while q % 2 == 0:
        q //= 2
        s += 1
    z = 2
    while legendre(z, p) != -1:
        z += 1
    m, c, t, r = s, pow(z, q, p), pow(n, q, p), pow(n, (q + 1) // 2, p)
    while t != 1:
        i, t2 = 0, t
        while t2 != 1:
            t2 = t2 * t2 % p
            i += 1
        b = pow(c, 1 << (m - i - 1), p)
        m, c, t, r = i, b * b % p, t * b * b % p, r * b % p
    return r


def crt(r1, m1, r2, m2):
    """Solve x = r1 mod m1, x = r2 mod m2. Returns (r, lcm) or None."""
    g = math.gcd(m1, m2)
    if (r2 - r1) % g:
        return None
    l = m1 // g * m2
    k = ((r2 - r1) // g) * pow(m1 // g, -1, m2 // g) % (m2 // g)
    return (r1 + m1 * k) % l, l


# ---------------------------------------------------------------------------
# Elliptic curve arithmetic (affine coordinates, None = point at infinity)
# ---------------------------------------------------------------------------

class Curve:
    def __init__(self, p, a, b):
        self.p, self.a, self.b = p, a % p, b % p

    def add(self, P, Q):
        if P is None:
            return Q
        if Q is None:
            return P
        p = self.p
        x1, y1 = P
        x2, y2 = Q
        if x1 == x2:
            if (y1 + y2) % p == 0:
                return None
            lam = (3 * x1 * x1 + self.a) * pow(2 * y1, -1, p) % p
        else:
            lam = (y2 - y1) * pow(x2 - x1, -1, p) % p
        x3 = (lam * lam - x1 - x2) % p
        return x3, (lam * (x1 - x3) - y1) % p

    def neg(self, P):
        return None if P is None else (P[0], (-P[1]) % self.p)

    def mul(self, k, P):
        if k < 0:
            return self.mul(-k, self.neg(P))
        R = None
        while k:
            if k & 1:
                R = self.add(R, P)
            P = self.add(P, P)
            k >>= 1
        return R

    def random_point(self, rng):
        p = self.p
        while True:
            x = rng.randrange(p)
            rhs = (x * x * x + self.a * x + self.b) % p
            if legendre(rhs, p) >= 0:
                y = sqrt_mod(rhs, p)
                if rng.random() < 0.5:
                    y = (-y) % p
                return x, y


def hasse_interval(p):
    w = math.isqrt(4 * p)  # floor(2 * sqrt(p))
    return p + 1 - w, p + 1 + w


def find_multiple(curve, P, lo, hi):
    """Baby-step giant-step: some N in [lo, hi] with N * P = O."""
    width = hi - lo
    m = math.isqrt(width) + 1
    baby = {}
    R = None
    for j in range(m):  # baby steps: j * P
        baby.setdefault(R, j)
        R = curve.add(R, P)
    step = curve.mul(m, P)
    G = curve.mul(lo, P)  # giant steps: (lo + i*m) * P
    for i in range(m + 2):
        j = baby.get(curve.neg(G))
        if j is not None:
            n = lo + i * m + j
            if n <= hi + m and curve.mul(n, P) is None:
                return n
        G = curve.add(G, step)
    raise ArithmeticError("no multiple found; inputs violate assumptions")


def point_order(curve, P, multiple, rng):
    order = multiple
    for q in prime_factors(multiple, rng):
        while order % q == 0 and curve.mul(order // q, P) is None:
            order //= q
    return order


def count_points(p, a, b, seed=None):
    rng = random.Random(seed if seed is not None else (p * 1000003 + a * 101 + b))
    lo, hi = hasse_interval(p)
    E = Curve(p, a, b)
    d = 2
    while legendre(d, p) != -1:
        d += 1
    T = Curve(p, a * d * d, b * d * d * d)  # quadratic twist: #T = 2p + 2 - #E

    residue, modulus = 0, 1  # constraint: N = residue mod modulus
    for attempt in range(200):
        curve, on_twist = (E, False) if attempt % 2 == 0 else (T, True)
        P = curve.random_point(rng)
        n0 = find_multiple(curve, P, lo, hi)
        k = point_order(curve, P, n0, rng)
        # Points on E: N = 0 mod k.  Points on twist: 2p + 2 - N = 0 mod k.
        target = (2 * p + 2) % k if on_twist else 0
        combined = crt(residue, modulus, target, k)
        if combined is None:
            raise ArithmeticError("inconsistent congruences")
        residue, modulus = combined
        first = lo + (residue - lo) % modulus
        if first <= hi and first + modulus > hi:
            return first
    raise ArithmeticError("did not converge")


def main(argv):
    if len(argv) != 4:
        print("usage: count.py p a b", file=sys.stderr)
        return 2
    p, a, b = (int(v) for v in argv[1:])
    print(count_points(p, a, b))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
