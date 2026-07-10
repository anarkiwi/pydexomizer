"""Robustness: malformed input must raise ValueError, never crash."""

import pytest

from pydexomizer import decrunch_raw
from pydexomizer.rawdec import _ERR_MSG


def test_empty_input():
    with pytest.raises(ValueError):
        decrunch_raw(b"")


@pytest.mark.parametrize(
    "blob",
    [
        b"\x00",
        b"\x00\x01",
        b"\x01\x02\x03",
        b"\xff" * 8,
        bytes(range(16)),
    ],
)
def test_truncated_or_garbage_does_not_crash(blob):
    # Whatever the bytes, we must get a clean exception, not a segfault/hang.
    with pytest.raises(ValueError):
        decrunch_raw(blob)


def test_error_messages_defined():
    assert set(_ERR_MSG) == {1, 2, 3}
    for msg in _ERR_MSG.values():
        assert isinstance(msg, str) and msg
