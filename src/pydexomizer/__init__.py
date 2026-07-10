"""pydexomizer: a pure-Python decompressor for Commodore exomizer data.

Decompresses (never compresses) the output of the exomizer cruncher:

* ``decrunch_raw``   - raw streams (``exomizer raw``), all -P proto variants.
* ``decrunch_mem``   - ``exomizer mem`` PRGs.
* ``decrunch_level`` - ``exomizer level`` segments.
* ``decrunch_sfx``   - self-extracting PRGs (``exomizer sfx``), via 6502 emulation.

See the proto module for the -P bit flags; the default is -P39.
"""

from .container import (
    DecrunchResult,
    decrunch_level,
    decrunch_mem,
    decrunch_mem_auto,
)
from .proto import (
    MAX_OFFSET,
    PFLAG_4_OFFSET_TABLES,
    PFLAG_BITS_ALIGN_START,
    PFLAG_BITS_COPY_GT_7,
    PFLAG_BITS_ORDER_BE,
    PFLAG_IMPL_1LITERAL,
    PFLAG_REUSE_OFFSET,
    PROTO_DEFAULT,
)
from .rawdec import decrunch_raw
from .sfx import SfxResult, decrunch_sfx

__version__ = "0.1.0"

__all__ = [
    "decrunch_raw",
    "decrunch_mem",
    "decrunch_mem_auto",
    "decrunch_level",
    "decrunch_sfx",
    "DecrunchResult",
    "SfxResult",
    "PROTO_DEFAULT",
    "MAX_OFFSET",
    "PFLAG_BITS_ORDER_BE",
    "PFLAG_BITS_COPY_GT_7",
    "PFLAG_IMPL_1LITERAL",
    "PFLAG_BITS_ALIGN_START",
    "PFLAG_4_OFFSET_TABLES",
    "PFLAG_REUSE_OFFSET",
    "__version__",
]
