"""Core Exomizer raw bitstream decoder.

Faithful port of ``dec_ctx_decrunch`` and friends from src/exodec.c of the
reference exomizer distribution (Magnus Lind, zlib licence). Supports every
``-P`` proto variant; the default is -P39.

The decode core operates on numpy uint8 arrays with a fixed 64 KiB output
bound (the Commodore address space), which keeps it numba-friendly. numba is
used as an optional accelerator when available. All input reads and output
writes are bounds-checked and report an error code rather than reading out of
bounds, so malformed input raises cleanly instead of crashing.
"""

import numpy as np

from .proto import (
    PFLAG_4_OFFSET_TABLES,
    PFLAG_BITS_ALIGN_START,
    PFLAG_BITS_COPY_GT_7,
    PFLAG_BITS_ORDER_BE,
    PFLAG_IMPL_1LITERAL,
    PFLAG_REUSE_OFFSET,
    PROTO_DEFAULT,
)

try:  # optional acceleration; the code runs identically without numba
    from numba import njit

    _HAVE_NUMBA = True
except ImportError:  # pragma: no cover - exercised only without numba

    _HAVE_NUMBA = False

    def njit(*args, **kwargs):
        """No-op stand-in for numba.njit when numba is not installed."""

        def wrap(func):
            return func

        if len(args) == 1 and callable(args[0]) and not kwargs:
            return args[0]
        return wrap


_OUT_MAX = 65536

ERR_NONE = 0
ERR_INPUT_UNDERRUN = 1
ERR_OUTPUT_OVERFLOW = 2
ERR_BAD_OFFSET = 3

_ERR_MSG = {
    ERR_INPUT_UNDERRUN: "unexpected end of crunched input",
    ERR_OUTPUT_OVERFLOW: "decrunched output exceeds 64 KiB",
    ERR_BAD_OFFSET: "back-reference points before start of output",
}


@njit(cache=True)
def _read_bits(inp, inlen, inpos, bitbuf, count, order_be, copy_gt_7):
    """Read ``count`` bits. Returns (val, inpos, bitbuf, err)."""
    byte_copy = 0
    val = 0
    err = ERR_NONE
    if copy_gt_7:
        while count > 7:
            byte_copy = count >> 3
            count &= 7
    while count > 0:
        count -= 1
        if order_be:
            carry = 1 if (bitbuf & 0x80) != 0 else 0
            bitbuf = (bitbuf << 1) & 0xFF
        else:
            carry = bitbuf & 0x01
            bitbuf = bitbuf >> 1
        if bitbuf == 0:
            if inpos >= inlen:
                return val, inpos, bitbuf, ERR_INPUT_UNDERRUN
            bitbuf = inp[inpos]
            inpos += 1
            if order_be:
                carry = 1 if (bitbuf & 0x80) != 0 else 0
                bitbuf = ((bitbuf << 1) & 0xFF) | 0x01
            else:
                carry = bitbuf & 0x01
                bitbuf = (bitbuf >> 1) | 0x80
        val = (val << 1) | carry
    while byte_copy > 0:
        byte_copy -= 1
        if inpos >= inlen:
            return val, inpos, bitbuf, ERR_INPUT_UNDERRUN
        val = (val << 8) | inp[inpos]
        inpos += 1
    return val, inpos, bitbuf, err


@njit(cache=True)
def _decode(inp, flags):
    """Decode a forward raw stream. Returns (out_array, out_len, err)."""
    order_be = 1 if (flags & PFLAG_BITS_ORDER_BE) else 0
    copy_gt_7 = 1 if (flags & PFLAG_BITS_COPY_GT_7) else 0
    impl_1literal = 1 if (flags & PFLAG_IMPL_1LITERAL) else 0
    align_start = 1 if (flags & PFLAG_BITS_ALIGN_START) else 0
    four_off = 1 if (flags & PFLAG_4_OFFSET_TABLES) else 0
    reuse = 1 if (flags & PFLAG_REUSE_OFFSET) else 0

    out = np.zeros(_OUT_MAX, dtype=np.uint8)
    inlen = inp.shape[0]
    inpos = 0
    if inlen == 0:
        return out, 0, ERR_INPUT_UNDERRUN
    if align_start:
        bitbuf = 0
    else:
        bitbuf = inp[inpos]
        inpos += 1

    # --- table init ------------------------------------------------------
    end = 68 if four_off else 52
    table_lo = np.zeros(end, dtype=np.int64)
    table_bi = np.zeros(end, dtype=np.int64)
    table_bit = np.zeros(4, dtype=np.int64)
    table_off = np.zeros(4, dtype=np.int64)
    table_bit[0] = 2
    table_bit[1] = 4
    table_bit[2] = 4
    if four_off:
        table_bit[3] = 4
        table_off[0] = 64
        table_off[1] = 48
        table_off[2] = 32
        table_off[3] = 16
    else:
        table_off[0] = 48
        table_off[1] = 32
        table_off[2] = 16

    a = 0
    b = 0
    for i in range(end):
        if i & 0xF:
            a += 1 << b
        else:
            a = 1
        table_lo[i] = a
        if copy_gt_7:
            b, inpos, bitbuf, err = _read_bits(
                inp, inlen, inpos, bitbuf, 3, order_be, copy_gt_7
            )
            if err:
                return out, 0, err
            hi, inpos, bitbuf, err = _read_bits(
                inp, inlen, inpos, bitbuf, 1, order_be, copy_gt_7
            )
            if err:
                return out, 0, err
            b |= hi << 3
        else:
            b, inpos, bitbuf, err = _read_bits(
                inp, inlen, inpos, bitbuf, 4, order_be, copy_gt_7
            )
            if err:
                return out, 0, err
        table_bi[i] = b

    # --- main decode loop ------------------------------------------------
    outlen = 0
    threshold = 4 if four_off else 3
    reuse_offset_state = 1
    literal = 1
    offset = 0
    started = 0

    while True:
        do_literal = 0
        length = 0

        if impl_1literal and started == 0:
            started = 1
            length = 1
            literal = 1
            do_literal = 1
        else:
            reuse_offset_state = (reuse_offset_state << 1) | literal
            literal = 0
            bit, inpos, bitbuf, err = _read_bits(
                inp, inlen, inpos, bitbuf, 1, order_be, copy_gt_7
            )
            if err:
                return out, 0, err
            if bit:
                length = 1
                literal = 1
                do_literal = 1
            else:
                val = 0
                while True:
                    gbit, inpos, bitbuf, err = _read_bits(
                        inp, inlen, inpos, bitbuf, 1, order_be, copy_gt_7
                    )
                    if err:
                        return out, 0, err
                    if gbit != 0:
                        break
                    val += 1
                    if val > 17:
                        return out, 0, ERR_INPUT_UNDERRUN
                if val == 16:
                    break  # end of stream
                if val == 17:
                    length, inpos, bitbuf, err = _read_bits(
                        inp, inlen, inpos, bitbuf, 16, order_be, copy_gt_7
                    )
                    if err:
                        return out, 0, err
                    literal = 1
                    do_literal = 1
                else:
                    extra, inpos, bitbuf, err = _read_bits(
                        inp, inlen, inpos, bitbuf, table_bi[val], order_be, copy_gt_7
                    )
                    if err:
                        return out, 0, err
                    length = table_lo[val] + extra

                    reuse_offset = 0
                    if reuse and (reuse_offset_state & 3) == 1:
                        reuse_offset, inpos, bitbuf, err = _read_bits(
                            inp, inlen, inpos, bitbuf, 1, order_be, copy_gt_7
                        )
                        if err:
                            return out, 0, err
                    if not reuse_offset:
                        idx = (length if length <= threshold else threshold) - 1
                        sel, inpos, bitbuf, err = _read_bits(
                            inp,
                            inlen,
                            inpos,
                            bitbuf,
                            table_bit[idx],
                            order_be,
                            copy_gt_7,
                        )
                        if err:
                            return out, 0, err
                        val = table_off[idx] + sel
                        extra, inpos, bitbuf, err = _read_bits(
                            inp,
                            inlen,
                            inpos,
                            bitbuf,
                            table_bi[val],
                            order_be,
                            copy_gt_7,
                        )
                        if err:
                            return out, 0, err
                        offset = table_lo[val] + extra

        if do_literal:
            if outlen + length > _OUT_MAX:
                return out, 0, ERR_OUTPUT_OVERFLOW
            for _ in range(length):
                if inpos >= inlen:
                    return out, 0, ERR_INPUT_UNDERRUN
                out[outlen] = inp[inpos]
                inpos += 1
                outlen += 1
        else:
            src = outlen - offset
            if src < 0:
                return out, 0, ERR_BAD_OFFSET
            if outlen + length > _OUT_MAX:
                return out, 0, ERR_OUTPUT_OVERFLOW
            for _ in range(length):
                out[outlen] = out[src]
                src += 1
                outlen += 1

    return out, outlen, ERR_NONE


def decrunch_raw(data, backward=False, proto=PROTO_DEFAULT):
    """Decompress a raw exomizer stream.

    Args:
        data: crunched bytes as produced by ``exomizer raw``.
        backward: True for streams crunched with ``-b`` (decrunch backwards).
        proto: proto flags controlling the bit stream format (default -P39).

    Returns:
        The decompressed bytes.

    Raises:
        ValueError: if the stream is malformed or truncated.
    """
    buf = bytes(data)
    if backward:
        buf = buf[::-1]
    inp = np.frombuffer(buf, dtype=np.uint8).astype(np.int64)
    out, outlen, err = _decode(inp, int(proto))
    if err:
        raise ValueError(_ERR_MSG.get(err, "invalid exomizer stream"))
    result = out[:outlen].tobytes()
    if backward:
        result = result[::-1]
    return result
