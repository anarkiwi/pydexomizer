"""BASIC SYS-line entry-point detection.

Port of ``find_sys`` from src/exo_util.c of the reference exomizer.
"""

# CBM (0x9e), Apple ][ (0x8c) and Oric (0xbf) SYS/CALL tokens.
_SYS_TOKENS = (0x9E, 0x8C, 0xBF)


def find_sys(buf, sys_token=-1):
    """Find the SYS/CALL entry address in a tokenised BASIC line.

    Args:
        buf: memory starting at the BASIC text start.
        sys_token: specific token to match, or -1 for any known token.

    Returns:
        (entry, stub_len). entry is -1 if none was found.
    """
    outstart = -1
    state = 1
    i = 4  # skip link and line number
    n = len(buf)
    while i < 1000 and i < n and buf[i] != 0:
        c = buf[i]
        if state == 1:
            if (sys_token == -1 and c in _SYS_TOKENS) or c == sys_token:
                state = 2
        elif state == 2:
            if c in (0x20, 0x28):  # space or '('
                i += 1
                continue
            state = 3
            # fall through
        if state == 3:
            j = i
            while j < n and 0x30 <= buf[j] <= 0x39:
                j += 1
            if j > i:
                outstart = int(bytes(buf[i:j]).decode("ascii"))
            else:
                outstart = -1
            state = 4
        i += 1
    stub_len = i + 3
    return outstart, stub_len
