# syntax=docker/dockerfile:1

# Stage 1: build the reference exomizer binary (cacheable dependency layer).
# Uses the same base image as the test stage so the binary's glibc matches.
FROM python:3.12-slim AS exobuild
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential git bison flex ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN git clone https://bitbucket.org/magli143/exomizer.git /exomizer
RUN cd /exomizer/src && make exomizer

# Stage 2: install the package and run the pytest + coverage suite.
FROM python:3.12-slim AS test
COPY --from=exobuild /exomizer/src/exomizer /usr/local/bin/exomizer
ENV EXOMIZER=/usr/local/bin/exomizer
WORKDIR /app

# Install dependencies first so they cache independently of source changes.
COPY pyproject.toml README.md ./
COPY LICENSE ./
COPY src/ ./src/
RUN pip install --no-cache-dir -e .[test]

# Source that changes often is copied last.
COPY tests/ ./tests/

# First run exercises the numba-compiled path (correctness). The second runs
# with the JIT disabled so coverage can trace the otherwise-compiled decoder.
CMD ["sh", "-c", "pytest -q && NUMBA_DISABLE_JIT=1 pytest --cov=pydexomizer --cov-report=term-missing --cov-fail-under=85"]
