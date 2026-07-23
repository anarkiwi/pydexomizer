"""Self-extracting (sfx) PRG decompression.

Replicates ``decrunch_sfx`` from src/desfx.c of the reference exomizer by
running the 6502 sfx stub on a jennings CPU emulator and tracing the writes it
makes, then returning the largest contiguous written region as the output.
"""

from collections import namedtuple

from jennings.devices.mpu6502 import MPU

from .basic import find_sys

SfxResult = namedtuple("SfxResult", ["start", "data", "entry", "cycles"])


class _C64Memory:
    """64 KiB RAM with C64 IO-bank write suppression and write tracing.

    Mirrors mem_access_write/read from src/desfx.c: when the IO area is banked
    in and visible, writes to $D000-$DFFF are dropped (they would hit IO, not
    RAM). Writes are recorded when tracing is enabled.
    """

    def __init__(self):
        self.ram = bytearray(65536)
        self.trace = False
        self.written = bytearray(65536)

    def __len__(self):
        return 65536

    def __getitem__(self, addr):
        if isinstance(addr, slice):
            return self.ram[addr]
        return self.ram[addr]

    def __setitem__(self, addr, value):
        ram = self.ram
        b1 = ram[1]
        if (b1 & 4) == 4 and (b1 & 3) != 0 and 0xD000 <= addr < 0xE000:
            return
        ram[addr] = value & 0xFF
        if self.trace:
            self.written[addr] = 1


def _largest_written_region(written):
    best_start = best_end = 0
    best_len = -1
    i = 0
    n = len(written)
    while i < n:
        if written[i]:
            j = i
            while j < n and written[j]:
                j += 1
            if j - i > best_len:
                best_len = j - i
                best_start = i
                best_end = j
            i = j
        else:
            i += 1
    return best_start, best_end


def _entry_point(ram, load_addr, entry):
    if entry is not None:
        return entry
    run, _ = find_sys(memoryview(ram)[load_addr:])
    if run != -1:
        return run
    return load_addr


def decrunch_sfx(prg, entry=None, max_steps=8_000_000):
    """Decompress a self-extracting exomizer PRG.

    Runs the 6502 sfx stub on an emulated CPU (the same approach as the
    reference ``exomizer desfx`` command) and returns the largest contiguous
    region written during decrunching.

    Args:
        prg: the .prg bytes (2-byte load address followed by the payload).
        entry: address at which to start executing the stub (i.e. the SYS
            target), auto-detected from the BASIC SYS line if None. This is the
            stub entry, not the decrunched program's entry.
        max_steps: safety bound on emulated instructions; a wrong entry that
            never converges raises RuntimeError instead of looping forever.

    Returns:
        SfxResult(start, data, entry, cycles). ``entry`` is where the stub
        jumped after decrunching (the decrunched program's entry point).
    """
    load_addr = prg[0] | (prg[1] << 8)
    mem = _C64Memory()
    body = prg[2:]
    mem.ram[load_addr : load_addr + len(body)] = body
    mem.ram[1] = 0x37

    run = _entry_point(mem.ram, load_addr, entry)

    cpu = MPU(memory=mem)
    cpu.pc = run
    cpu.sp = 0xF6
    cpu.p = 0

    steps = 0
    # setup phase: run until control drops into low memory with a clean stack
    while cpu.pc >= 0x0400 or cpu.sp != 0xF6:
        cpu.step()
        steps += 1
        if steps > max_steps:
            raise RuntimeError("sfx setup did not converge")

    mem.trace = True
    # decrunch phase: runs in low memory until it jumps to the decrunched code
    while cpu.pc < 0x0400:
        cpu.step()
        steps += 1
        if steps > max_steps:
            raise RuntimeError("sfx decrunch did not converge")

    start, end = _largest_written_region(mem.written)
    data = bytes(mem.ram[start:end])
    return SfxResult(start, data, cpu.pc, cpu.processorCycles)
