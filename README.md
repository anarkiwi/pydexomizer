# pydexomizer

Pure-Python decompressor ("decrunch") for Commodore exomizer data. Decompression only, no cruncher.

## Install

```
pip install pydexomizer
pip install pydexomizer[speedup]   # optional numba accelerator
```

## Formats

- `raw` - raw exomizer streams (all -P proto variants)
- `mem` - `exomizer mem` PRGs
- `level` - `exomizer level` segments
- `sfx` - self-extracting PRGs, via 6502 emulation

## Usage

```python
from pydexomizer import (
    decrunch_raw, decrunch_mem, decrunch_level, decrunch_sfx,
)

data = decrunch_raw(raw_bytes)                 # -> bytes

res = decrunch_mem(mem_prg_bytes)              # -> DecrunchResult(start, data, entry)
res = decrunch_level(level_bytes)              # -> DecrunchResult(start, data, entry)
res = decrunch_sfx(sfx_prg_bytes)              # -> SfxResult(start, data, entry, cycles)
res.start, res.data
```

## CLI

```
pydexomizer input.prg -f sfx -o output.prg
```

## Development

See [docs/](docs/).

## Acknowledgements

Algorithm derived from Magnus Lind's [exomizer](https://bitbucket.org/magli143/exomizer) (zlib licence), used as the reference implementation.

## Licence

Apache-2.0
