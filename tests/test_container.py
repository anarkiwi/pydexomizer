"""mem and level container round-trip tests against the reference exomizer."""

import pytest

from pydexomizer import decrunch_level, decrunch_mem, decrunch_mem_auto

from .conftest import requires_exomizer, run_exomizer

PAYLOAD_NAMES = ["text", "zeros", "rand", "struct", "small"]
ADDR = "0x2000"


@requires_exomizer
@pytest.mark.parametrize("name", PAYLOAD_NAMES)
def test_mem_backward(exomizer, payloads, tmp_path, name):
    payload = payloads[name]
    prg = run_exomizer(exomizer, tmp_path, ["mem"], payload, name, "memb", addr=ADDR)
    res = decrunch_mem(prg)
    assert res.data == payload
    assert res.start == 0x2000


@requires_exomizer
@pytest.mark.parametrize("name", PAYLOAD_NAMES)
def test_mem_forward(exomizer, payloads, tmp_path, name):
    payload = payloads[name]
    prg = run_exomizer(
        exomizer, tmp_path, ["mem", "-f"], payload, name, "memf", addr=ADDR
    )
    res = decrunch_mem(prg, forward=True)
    assert res.data == payload
    assert res.start == 0x2000


@requires_exomizer
@pytest.mark.parametrize("name", PAYLOAD_NAMES)
def test_mem_auto(exomizer, payloads, tmp_path, name):
    payload = payloads[name]
    prg = run_exomizer(exomizer, tmp_path, ["mem"], payload, name, "memb", addr=ADDR)
    assert decrunch_mem_auto(prg).data == payload


@requires_exomizer
@pytest.mark.parametrize("name", PAYLOAD_NAMES)
def test_level_backward(exomizer, payloads, tmp_path, name):
    payload = payloads[name]
    seg = run_exomizer(
        exomizer, tmp_path, ["level"], payload, name, "levb", addr="0x4000"
    )
    res = decrunch_level(seg)
    assert res.data == payload
    assert res.start == 0x4000


@requires_exomizer
@pytest.mark.parametrize("name", PAYLOAD_NAMES)
def test_level_forward(exomizer, payloads, tmp_path, name):
    payload = payloads[name]
    seg = run_exomizer(
        exomizer, tmp_path, ["level", "-f"], payload, name, "levf", addr="0x4000"
    )
    res = decrunch_level(seg, forward=True)
    assert res.data == payload
    assert res.start == 0x4000


def test_mem_too_short():
    with pytest.raises(ValueError):
        decrunch_mem(b"\x00\x01")


def test_level_too_short():
    with pytest.raises(ValueError):
        decrunch_level(b"\x00")


def test_mem_auto_fails_cleanly():
    with pytest.raises(ValueError):
        decrunch_mem_auto(b"\x00\x01\x02\x03\x04\x05")
