"""Commodore container formats: mem and level PRGs.

Framing was derived from src/exo_main.c (the ``mem`` and ``level`` commands)
and verified byte-for-byte against the reference exomizer.

mem forward:    [load_lo,load_hi][target_hi,target_lo][crunched]
mem backward:   [load_lo,load_hi][crunched][end_lo,end_hi]
level forward:  [start_hi,start_lo][crunched]
level backward: [end_hi,end_lo][reverse(crunched)]

``load`` is the address the crunched PRG itself loads to; the decrunched data
occupies [start, end).
"""

from collections import namedtuple

from .proto import PROTO_DEFAULT
from .rawdec import decrunch_raw

DecrunchResult = namedtuple("DecrunchResult", ["start", "data", "entry"])
DecrunchResult.__new__.__defaults__ = (None,)


def decrunch_mem(prg, forward=False, proto=PROTO_DEFAULT):
    """Decompress a ``exomizer mem`` PRG.

    Args:
        prg: the mem PRG bytes (including its 2-byte load address).
        forward: True if crunched with ``-f`` (forward), else backward (default).
        proto: proto flags (default -P39).

    Returns:
        DecrunchResult(start, data, None).
    """
    prg = bytes(prg)
    if len(prg) < 5:
        raise ValueError("mem PRG too short")
    if forward:
        target = (prg[2] << 8) | prg[3]
        data = decrunch_raw(prg[4:], backward=False, proto=proto)
        return DecrunchResult(target, data)
    end = prg[-2] | (prg[-1] << 8)
    data = decrunch_raw(prg[2:-2], backward=True, proto=proto)
    return DecrunchResult((end - len(data)) & 0xFFFF, data)


def decrunch_level(data, forward=False, proto=PROTO_DEFAULT):
    """Decompress a single ``exomizer level`` segment.

    Args:
        data: the level segment bytes (2-byte address header + stream).
        forward: True if crunched with ``-f`` (forward), else backward (default).
        proto: proto flags (default -P39).

    Returns:
        DecrunchResult(start, data, None).
    """
    data = bytes(data)
    if len(data) < 3:
        raise ValueError("level segment too short")
    addr = (data[0] << 8) | data[1]
    if forward:
        out = decrunch_raw(data[2:], backward=False, proto=proto)
        return DecrunchResult(addr, out)
    out = decrunch_raw(data[2:][::-1], backward=True, proto=proto)
    return DecrunchResult((addr - len(out)) & 0xFFFF, out)


def decrunch_mem_auto(prg, proto=PROTO_DEFAULT):
    """Decompress a mem PRG, trying backward then forward.

    Both directions are attempted; the first that decodes without error is
    returned. Direction is not reliably self-describing, so prefer the explicit
    ``decrunch_mem`` when the crunch direction is known.
    """
    prg = bytes(prg)
    errors = []
    for forward in (False, True):
        try:
            return decrunch_mem(prg, forward=forward, proto=proto)
        except ValueError as exc:
            errors.append(str(exc))
    raise ValueError(f"could not decode mem PRG ({'; '.join(errors)})")
