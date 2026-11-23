Write a Python program `/app/count.py` that counts points on elliptic curves over large prime fields.

Running

```
python3 /app/count.py p a b
```

must print exactly one integer on standard output: the number of points on the curve

    y^2 = x^3 + a*x + b

over the finite field with p elements, **including the point at infinity**.

Inputs:

- p is a prime with 10^11 < p < 10^13.
- a and b are integers with 0 <= a, b < p, and 4a^3 + 27b^2 is not 0 mod p (the curve is non-singular).

Requirements:

- The answer must be exact.
- Each run must finish within 10 seconds on one CPU core.
- Use only Python 3 and the packages already installed. There is no network access.

Three example inputs with their correct answers are in `/app/examples.txt`.
