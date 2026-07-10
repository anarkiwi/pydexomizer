"""Command line interface: decompress exomizer data to a Commodore PRG."""

import argparse
import sys

from . import __version__
from .container import decrunch_level, decrunch_mem
from .proto import PROTO_DEFAULT
from .rawdec import decrunch_raw
from .sfx import decrunch_sfx


def _prg(start, data):
    return bytes([start & 0xFF, (start >> 8) & 0xFF]) + data


def build_parser():
    """Build the argument parser for the pydexomizer command."""
    p = argparse.ArgumentParser(
        prog="pydexomizer",
        description="Decompress Commodore exomizer data (decrunch only).",
    )
    p.add_argument("--version", action="version", version=f"pydexomizer {__version__}")
    p.add_argument("infile", help="input file")
    p.add_argument("-o", "--outfile", help="output file (default: stdout)")
    p.add_argument(
        "-f",
        "--format",
        choices=["raw", "mem", "level", "sfx"],
        default="sfx",
        help="input format (default: sfx)",
    )
    p.add_argument(
        "-b",
        "--backward",
        action="store_true",
        help="raw: stream was crunched backwards (-b)",
    )
    p.add_argument(
        "--forward",
        action="store_true",
        help="mem/level: stream was crunched forwards (-f)",
    )
    p.add_argument(
        "-a",
        "--load-address",
        help="raw: prepend this load address (hex ok, e.g. 0x1000) to make a PRG",
    )
    p.add_argument(
        "-P",
        "--proto",
        type=lambda s: int(s, 0),
        default=PROTO_DEFAULT,
        help=f"proto (-P) bitfield, default {PROTO_DEFAULT}",
    )
    p.add_argument(
        "--entry",
        type=lambda s: int(s, 0),
        default=None,
        help="sfx: entry address (default: auto-detect)",
    )
    return p


def main(argv=None):
    """Decompress the input file and write a PRG to the output or stdout."""
    args = build_parser().parse_args(argv)
    with open(args.infile, "rb") as handle:
        data = handle.read()

    if args.format == "raw":
        out = decrunch_raw(data, backward=args.backward, proto=args.proto)
        if args.load_address is not None:
            out = _prg(int(args.load_address, 0), out)
    elif args.format == "mem":
        res = decrunch_mem(data, forward=args.forward, proto=args.proto)
        out = _prg(res.start, res.data)
    elif args.format == "level":
        res = decrunch_level(data, forward=args.forward, proto=args.proto)
        out = _prg(res.start, res.data)
    else:  # sfx
        res = decrunch_sfx(data, entry=args.entry)
        out = _prg(res.start, res.data)

    if args.outfile:
        with open(args.outfile, "wb") as handle:
            handle.write(out)
    else:
        sys.stdout.buffer.write(out)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
