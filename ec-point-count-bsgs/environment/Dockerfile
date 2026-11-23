# Python with SymPy, and nothing that already implements elliptic-curve point
# counting (no PARI/GP, Sage or Magma). Pin the base image by digest before
# publishing, e.g. FROM python:3.12-slim-bookworm@sha256:<digest>.
FROM python:3.12-slim-bookworm

RUN pip install --no-cache-dir sympy==1.13.3 pytest==8.3.4

WORKDIR /app
COPY examples.txt /app/examples.txt
