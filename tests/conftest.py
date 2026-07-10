"""Test fixtures.

Correctness is validated against the real exomizer cruncher: sample payloads
are crunched with it at test time and the library must reproduce the original
bytes (and, for sfx, must match ``exomizer desfx``). The exomizer binary is
located via the ``EXOMIZER`` environment variable or on ``PATH``. No exomizer
source or binaries are vendored in this repository; CI builds it on the fly.
"""

import os
import random
import shutil
import subprocess

import pytest

EXOMIZER = os.environ.get("EXOMIZER") or shutil.which("exomizer")

requires_exomizer = pytest.mark.skipif(
    EXOMIZER is None,
    reason="exomizer binary not found (set EXOMIZER or add it to PATH)",
)


def _payloads():
    rnd = random.Random(1234)
    return {
        "text": b"THE QUICK BROWN FOX 0123456789 " * 100,
        "zeros": bytes(2000),
        "rand": bytes(rnd.randrange(256) for _ in range(3000)),
        "struct": (bytes(range(256)) * 20)[:5000],
        "small": b"AB" * 7 + b"hello",
        "single": b"Q",
    }


@pytest.fixture(scope="session")
def payloads():
    return _payloads()


@pytest.fixture(scope="session")
def exomizer():
    if EXOMIZER is None:
        pytest.skip("exomizer not available")
    return EXOMIZER


def run_exomizer(exo, tmp_path, args, payload, name, suffix, addr=None):
    """Crunch ``payload`` and return the crunched bytes."""
    src = tmp_path / f"{name}.bin"
    src.write_bytes(payload)
    out = tmp_path / f"{name}.{suffix}"
    infile = f"{src}@{addr}" if addr is not None else str(src)
    cmd = [exo] + args + ["-q", "-o", str(out), infile]
    subprocess.run(cmd, check=True, capture_output=True)
    return out.read_bytes()


def run_desfx(exo, tmp_path, sfx_bytes, name):
    """Decrunch an sfx PRG with the reference desfx; return (start, data)."""
    src = tmp_path / f"{name}.sfx"
    src.write_bytes(sfx_bytes)
    out = tmp_path / f"{name}.desfx"
    subprocess.run(
        [exo, "desfx", "-q", "-o", str(out), str(src)],
        check=True,
        capture_output=True,
    )
    blob = out.read_bytes()
    return blob[0] | (blob[1] << 8), blob[2:]
