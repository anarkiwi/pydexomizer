"""Unit tests for helpers and proto branches not reachable via exomizer.

Current exomizer always emits big-endian, byte-aligned streams, so the
little-endian (ror) and align-start decode branches are exercised here
directly. These assert clean error handling, not round-trips.
"""

import pytest

from pydexomizer.proto import (
    PFLAG_BITS_ALIGN_START,
    PFLAG_BITS_COPY_GT_7,
    PFLAG_BITS_ORDER_BE,
)
from pydexomizer.rawdec import decrunch_raw
from pydexomizer.sfx import _C64Memory, _largest_written_region


def test_little_endian_branch_does_not_crash():
    # order_be = 0 (ror). Garbage input must raise, not segfault.
    with pytest.raises(ValueError):
        decrunch_raw(bytes(64), proto=PFLAG_BITS_COPY_GT_7)


def test_align_start_branch_does_not_crash():
    proto = PFLAG_BITS_ORDER_BE | PFLAG_BITS_COPY_GT_7 | PFLAG_BITS_ALIGN_START
    with pytest.raises(ValueError):
        decrunch_raw(bytes(64), proto=proto)


def test_four_bit_table_read_branch():
    # copy_gt_7 = 0 selects the 4-bit table read path in table init.
    with pytest.raises(ValueError):
        decrunch_raw(bytes(64), proto=PFLAG_BITS_ORDER_BE)


def test_c64_memory_len_and_slice():
    mem = _C64Memory()
    assert len(mem) == 65536
    mem[0x1234] = 0xAB
    assert mem[0x1234] == 0xAB
    assert bytes(mem[0x1234:0x1235]) == b"\xab"


def test_c64_memory_io_bank_write_suppressed():
    mem = _C64Memory()
    mem.ram[1] = 0x37  # IO visible (bits 0-2 set, bit 2 set)
    mem[0xD020] = 0x0E
    assert mem.ram[0xD020] == 0  # write to IO dropped, RAM untouched
    mem.ram[1] = 0x30  # bank IO out (bits 0-1 clear)
    mem[0xD021] = 0x06
    assert mem.ram[0xD021] == 0x06  # now RAM under IO is written


def test_c64_memory_trace():
    mem = _C64Memory()
    mem.trace = True
    mem[0x4000] = 1
    mem[0x4001] = 2
    mem[0x5000] = 9
    assert _largest_written_region(mem.written) == (0x4000, 0x4002)


def test_largest_written_region_empty():
    assert _largest_written_region(bytearray(16)) == (0, 0)
