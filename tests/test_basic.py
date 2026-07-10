"""BASIC SYS-line entry detection."""

from pydexomizer.basic import find_sys


def _basic_line(sys_addr, token=0x9E):
    # link word, line number, token, digits, end-of-line, end-of-program.
    digits = str(sys_addr).encode("ascii")
    return bytes([0x0B, 0x08, 0x0A, 0x00, token]) + digits + b"\x00\x00\x00"


def test_find_cbm_sys():
    entry, stub = find_sys(_basic_line(2061))
    assert entry == 2061
    assert stub > 0


def test_find_with_space_and_paren():
    line = bytes([0x0B, 0x08, 0x0A, 0x00, 0x9E, 0x20, 0x28]) + b"49152\x00\x00\x00"
    entry, _ = find_sys(line)
    assert entry == 49152


def test_specific_token():
    entry, _ = find_sys(_basic_line(4096, token=0x8C), sys_token=0x8C)
    assert entry == 4096


def test_no_sys_returns_minus_one():
    entry, _ = find_sys(bytes([0x0B, 0x08, 0x0A, 0x00]) + b"REM HI\x00\x00\x00")
    assert entry == -1


def test_empty_line():
    entry, _ = find_sys(bytes([0x00, 0x00, 0x00, 0x00, 0x00]))
    assert entry == -1


def test_sys_without_number():
    # SYS token immediately followed by a non-digit yields no address.
    line = bytes([0x0B, 0x08, 0x0A, 0x00, 0x9E]) + b"X\x00\x00\x00"
    entry, _ = find_sys(line)
    assert entry == -1
