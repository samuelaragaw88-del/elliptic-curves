#!/usr/bin/env python3
"""The obvious approach: count x values one by one. Correct, but about p steps.

It is here to show that the task is hard for the right reason: this program
gives the right answer for small p and times out for p ~ 10^12.

Usage: python tools/naive_count.py p a b
"""
import sys


def main():
    p, a, b = (int(v) for v in sys.argv[1:4])
    total = p + 1
    half = (p - 1) // 2
    for x in range(p):
        r = (x * x * x + a * x + b) % p
        if r:
            total += 1 if pow(r, half, p) == 1 else -1
    print(total)


if __name__ == "__main__":
    main()
