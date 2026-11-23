# Terminal-Bench task: counting points on elliptic curves

A complete, verified [Terminal-Bench](https://www.tbench.ai/) task in the
[Harbor](https://docs.harborframework.com/) format, written by **Samuel Aragaw**
(MSc, Mathematics and Computer Science, Al-Azhar University).

The agent must write a program that prints the exact number of points on

    y^2 = x^3 + a x + b   over F_p,   10^11 < p < 10^13,

in under 10 seconds per curve, with no computer algebra system that already does this.

## Why the task is hard for the right reason

| Approach | Steps for p ~ 10^13 | Result |
| --- | --- | --- |
| Count x values one by one | ~10^13 | Times out on every test |
| Guess p + 1 | 1 | Fails 23 of 28 tests |
| Hasse bound + baby-step giant-step + twist (Mestre) | ~4·p^(1/4), a few thousand | Passes, about 0.05 s per curve |

Passing needs three ideas from number theory, not luck or a hidden rule:

1. **Hasse's theorem**: the count N satisfies |N − (p + 1)| ≤ 2√p, so N lies in an interval of width about 4√p.
2. **Baby-step giant-step**: for a random point P, find N₀ in that interval with N₀·P = O in about p^(1/4) group operations, then factor N₀ to get the exact order of P.
3. **Making the answer unique**: if the order of P leaves more than one candidate, use more points, and points on the quadratic twist, which has 2p + 2 − N points (Mestre's method).

## Repository layout

```
ec-point-count-bsgs/          # the task, in Harbor format
├── instruction.md            # what the agent reads
├── task.toml                 # metadata, time limits, no network
├── environment/
│   ├── Dockerfile            # Python 3.12 + SymPy; no PARI/Sage/Magma
│   └── examples.txt          # 3 public examples with answers
├── solution/
│   ├── solve.sh              # oracle: installs the reference solution
│   └── count.py              # reference solution (standard library only)
└── tests/
    ├── test.sh               # runs pytest, writes reward 1 or 0
    ├── test_outputs.py       # 28 tests
    └── cases.json            # hidden expected answers (never shown to the agent)
tools/
├── make_cases.py             # generates and verifies all test cases
├── brute_force_check.py      # reference vs direct counting on 300 curves
├── check_with_pari.py        # optional: recompute every answer with PARI/GP
├── naive_count.py            # the brute-force approach, to show it fails
└── run_local.sh              # run the task without Docker
```

## How the expected answers are verified

An answer key is only as good as its checks. Every expected count is confirmed
in ways that do not depend on the reference solution being right:

| Check | What it proves | Covers |
| --- | --- | --- |
| Direct counting, p + 1 + Σ (x³+ax+b / p) | The algorithm is correct | 300 random curves, p from 300 to 40,000 |
| CM theory via Cornacchia's algorithm | Trace is one of the values allowed for j = 0 or j = 1728 curves | All 8 special curves (a = 0 or b = 0) |
| Group law: N·P = O on E and (2p+2−N)·Q = O on the twist, 25 points each | N is a multiple of the group exponent within the Hasse interval | All 26 stored cases |
| PARI/GP `ellcard` (optional, `tools/check_with_pari.py`) | Agreement with an independent, widely used system | All 26 stored cases |

## The tests

| Test | Cases | Why |
| --- | --- | --- |
| `test_script_exists` | 1 | Basic outcome |
| `test_examples` | 3 | The public examples |
| `test_hidden_curves` | 12 | Unseen random curves; stops hard-coded answers |
| `test_special_curves` | 8 | a = 0 or b = 0, including supersingular curves with exactly p + 1 points |
| `test_full_two_torsion` | 3 | Non-cyclic groups containing Z/2 × Z/2 |
| `test_fresh_random_curves` | 5 new curves per run | Answers exist nowhere; checked with the Hasse bound and the group law, so no lookup table can pass |

Every run must exit cleanly, print one integer and finish within 10 seconds.

## Results

| Solution | Result |
| --- | --- |
| Reference (`solution/count.py`) | 28 / 28 tests passed in 5 of 5 runs, about 1 s for the whole suite |
| Brute force (`tools/naive_count.py`) | Every example times out at 10 s; reward 0 |
| Always print p + 1 | 23 of 28 tests fail; reward 0 |
| Reference answer + 1 | Caught by `test_fresh_random_curves` |

## Run it yourself

Without Docker (needs Python 3.8+ and pytest):

```bash
python3 tools/brute_force_check.py      # reference vs direct counting
python3 tools/make_cases.py             # regenerate and re-verify all cases
bash tools/run_local.sh                 # reference solution -> reward 1
bash tools/run_local.sh naive           # brute force -> reward 0
python3 tools/check_with_pari.py        # optional, needs PARI/GP
```

With Docker, exactly as the verifier sees it:

```bash
docker build -t ec-point-count ec-point-count-bsgs/environment
docker run --rm \
  -v "$PWD/ec-point-count-bsgs/solution:/solution:ro" \
  -v "$PWD/ec-point-count-bsgs/tests:/tests:ro" \
  ec-point-count bash -c "bash /solution/solve.sh && bash /tests/test.sh; cat /logs/verifier/reward.txt"
```

## License

MIT, see `LICENSE`.
