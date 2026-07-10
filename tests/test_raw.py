"""Raw stream round-trip tests against the reference exomizer."""

import pytest

from pydexomizer import decrunch_raw

from .conftest import requires_exomizer, run_exomizer

PAYLOAD_NAMES = ["text", "zeros", "rand", "struct", "small", "single"]


@requires_exomizer
@pytest.mark.parametrize("name", PAYLOAD_NAMES)
@pytest.mark.parametrize("compat", [False, True], ids=["seq", "compat"])
def test_raw_forward(exomizer, payloads, tmp_path, name, compat):
    payload = payloads[name]
    args = ["raw"] + (["-c"] if compat else [])
    crunched = run_exomizer(exomizer, tmp_path, args, payload, name, "rawf")
    assert decrunch_raw(crunched) == payload


@requires_exomizer
@pytest.mark.parametrize("name", PAYLOAD_NAMES)
@pytest.mark.parametrize("compat", [False, True], ids=["seq", "compat"])
def test_raw_backward(exomizer, payloads, tmp_path, name, compat):
    payload = payloads[name]
    args = ["raw", "-b"] + (["-c"] if compat else [])
    crunched = run_exomizer(exomizer, tmp_path, args, payload, name, "rawb")
    assert decrunch_raw(crunched, backward=True) == payload


@requires_exomizer
def test_raw_no_encoding_table_flag_still_default(exomizer, payloads, tmp_path):
    # A stream crunched with the default proto decodes with the default proto.
    payload = payloads["text"]
    crunched = run_exomizer(exomizer, tmp_path, ["raw"], payload, "t", "rawf")
    assert decrunch_raw(crunched) == payload


# 39=default, 55=four offset tables, 7/23=no offset reuse, 3=no implicit literal.
@requires_exomizer
@pytest.mark.parametrize("proto", [39, 55, 7, 23, 3])
def test_raw_proto_variants(exomizer, payloads, tmp_path, proto):
    payload = payloads["struct"]
    crunched = run_exomizer(
        exomizer, tmp_path, ["raw", "-P", str(proto)], payload, "p", "rawf"
    )
    assert decrunch_raw(crunched, proto=proto) == payload
