"""sfx round-trip tests: the emulator-based decruncher must match desfx."""

import pytest

from pydexomizer import decrunch_sfx
from pydexomizer.basic import find_sys

from .conftest import requires_exomizer, run_desfx, run_exomizer

PAYLOAD_NAMES = ["text", "zeros", "rand", "struct", "small"]


@requires_exomizer
@pytest.mark.parametrize("name", PAYLOAD_NAMES)
def test_sfx_matches_payload(exomizer, payloads, tmp_path, name):
    payload = payloads[name]
    prg = run_exomizer(
        exomizer, tmp_path, ["sfx", "0x2000"], payload, name, "sfx", addr="0x2000"
    )
    res = decrunch_sfx(prg)
    assert res.data == payload
    assert res.start == 0x2000
    assert res.entry == 0x2000
    assert res.cycles > 0


@requires_exomizer
@pytest.mark.parametrize("name", PAYLOAD_NAMES + ["single"])
def test_sfx_matches_desfx(exomizer, payloads, tmp_path, name):
    payload = payloads[name]
    prg = run_exomizer(
        exomizer, tmp_path, ["sfx", "0x2000"], payload, name, "sfx", addr="0x2000"
    )
    ref_start, ref_data = run_desfx(exomizer, tmp_path, prg, name)
    res = decrunch_sfx(prg)
    assert res.start == ref_start
    assert res.data == ref_data


@requires_exomizer
def test_sfx_explicit_stub_entry(exomizer, payloads, tmp_path):
    # Passing the real stub entry (the BASIC SYS target) explicitly matches
    # auto-detection. The stub entry is NOT the decrunched program's entry.
    payload = payloads["struct"]
    prg = run_exomizer(
        exomizer, tmp_path, ["sfx", "0x2000"], payload, "e", "sfx", addr="0x2000"
    )
    stub_entry, _ = find_sys(prg[2:])
    assert stub_entry != -1
    forced = decrunch_sfx(prg, entry=stub_entry)
    assert forced.data == payload


@requires_exomizer
def test_sfx_wrong_entry_raises(exomizer, payloads, tmp_path):
    # A bogus entry must fail fast, not hang.
    prg = run_exomizer(
        exomizer,
        tmp_path,
        ["sfx", "0x2000"],
        payloads["small"],
        "w",
        "sfx",
        addr="0x2000",
    )
    with pytest.raises(RuntimeError):
        decrunch_sfx(prg, entry=0x2000, max_steps=200_000)
