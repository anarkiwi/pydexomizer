"""Command line interface tests."""

import pytest

from pydexomizer.cli import main

from .conftest import requires_exomizer, run_exomizer


@requires_exomizer
def test_cli_sfx_to_prg(exomizer, payloads, tmp_path):
    payload = payloads["struct"]
    prg = run_exomizer(
        exomizer, tmp_path, ["sfx", "0x2000"], payload, "c", "sfx", addr="0x2000"
    )
    infile = tmp_path / "in.sfx"
    infile.write_bytes(prg)
    out = tmp_path / "out.prg"
    assert main([str(infile), "-f", "sfx", "-o", str(out)]) == 0
    blob = out.read_bytes()
    assert blob[0] | (blob[1] << 8) == 0x2000
    assert blob[2:] == payload


@requires_exomizer
def test_cli_mem(exomizer, payloads, tmp_path):
    payload = payloads["text"]
    prg = run_exomizer(exomizer, tmp_path, ["mem"], payload, "m", "memb", addr="0x1000")
    infile = tmp_path / "in.mem"
    infile.write_bytes(prg)
    out = tmp_path / "out.prg"
    assert main([str(infile), "-f", "mem", "-o", str(out)]) == 0
    assert out.read_bytes()[2:] == payload


@requires_exomizer
def test_cli_level(exomizer, payloads, tmp_path):
    payload = payloads["struct"]
    seg = run_exomizer(
        exomizer, tmp_path, ["level"], payload, "l", "levb", addr="0x4000"
    )
    infile = tmp_path / "in.lev"
    infile.write_bytes(seg)
    out = tmp_path / "out.prg"
    assert main([str(infile), "-f", "level", "-o", str(out)]) == 0
    assert out.read_bytes()[2:] == payload


@requires_exomizer
def test_cli_raw_with_load_address_to_stdout(
    exomizer, payloads, tmp_path, capsysbinary
):
    payload = payloads["small"]
    raw = run_exomizer(exomizer, tmp_path, ["raw"], payload, "r", "rawf")
    infile = tmp_path / "in.raw"
    infile.write_bytes(raw)
    assert main([str(infile), "-f", "raw", "-a", "0x0801"]) == 0
    captured = capsysbinary.readouterr()
    assert captured.out == b"\x01\x08" + payload


@requires_exomizer
def test_cli_raw_backward(exomizer, payloads, tmp_path, capsysbinary):
    payload = payloads["text"]
    raw = run_exomizer(exomizer, tmp_path, ["raw", "-b"], payload, "rb", "rawb")
    infile = tmp_path / "in.rawb"
    infile.write_bytes(raw)
    assert main([str(infile), "-f", "raw", "-b"]) == 0
    assert capsysbinary.readouterr().out == payload


def test_cli_version(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert "pydexomizer" in capsys.readouterr().out
