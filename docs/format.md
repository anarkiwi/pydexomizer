# exomizer formats

Reference notes for the formats pydexomizer decodes. Terminology follows the
reference exomizer (https://bitbucket.org/magli143/exomizer).

## Raw bitstream

An exomizer raw stream is a decrunch table followed by a bit-packed sequence of
literal and sequence (copy) commands.

- **Embedded decrunch table.** The stream carries an embedded table of encoding
  parameters, 52 entries in the default layout or 68 entries when four offset
  tables are enabled (the `4_OFFSET_TABLES` proto flag). The decoder reads this
  table to initialise its length/offset base and bit-count arrays before
  decoding commands.
- **Gamma-coded length index.** Each command begins with a gamma-coded index.
  The index selects the meaning of the command and, for sequences, the length
  bucket used to read the sequence length.
- **End marker.** A gamma index of 16 marks the end of the stream.
- **Literal block.** A gamma index of 17 introduces a literal block (a run of
  bytes copied verbatim from the stream).
- **Offset tables selected by length threshold.** The offset (distance) for a
  copy is decoded using an offset table chosen by the sequence length: short
  sequences use a different offset table than longer ones. With
  `4_OFFSET_TABLES` there are four such tables keyed on the length.

### Proto (-P) bitfield

The `-P` value selects encoding variants. Bits:

| Bit | Value | Name              | Meaning                                             |
|-----|-------|-------------------|-----------------------------------------------------|
| 0   | 1     | BITS_ORDER_BE     | bit-reading order is big-endian                     |
| 1   | 2     | BITS_COPY_GT_7    | copy counts greater than 7 handled in bit reads     |
| 2   | 4     | IMPL_1LITERAL     | an implicit leading literal                         |
| 3   | 8     | BITS_ALIGN_START  | align bit reads at the start                        |
| 4   | 16    | 4_OFFSET_TABLES   | use four offset tables (68-entry decrunch table)    |
| 5   | 32    | REUSE_OFFSET      | allow reuse of the previous offset                  |

The default is `-P39` (bits 0, 1, 2, 5 = 1 + 2 + 4 + 32).

## Container framings

The Commodore container commands wrap a raw stream with a small address header.
`load` is the address the crunched PRG itself loads to; the decrunched data
occupies `[start, end)`.

```
mem forward:    [load_lo,load_hi][target_hi,target_lo][crunched]
mem backward:   [load_lo,load_hi][crunched][end_lo,end_hi]
level forward:  [start_hi,start_lo][crunched]
level backward: [end_hi,end_lo][reverse(crunched)]
```

Backward streams are decoded in reverse; for `level backward` the crunched
bytes themselves are stored reversed.

## sfx handling

Self-extracting PRGs embed a 6502 decrunch stub. pydexomizer decodes them the
same way the reference `desfx` command does: by emulating the stub rather than
re-implementing it. Using a jennings 6502 CPU:

1. Load the PRG payload into a 64 KiB RAM image at its load address.
2. Set `mem[1] = 0x37` (default C64 bank configuration).
3. Set the program counter to the SYS entry (found by parsing the BASIC `SYS`
   line), or to the load address if no SYS line is present.
4. Set the stack pointer to `0xf6`.
5. Run a **setup phase** until `pc < 0x400 && sp == 0xf6`.
6. Run the **decrunch phase** (`pc < 0x400`), tracing every write to RAM.

The output is the largest contiguous region written during the decrunch phase.

When the IO area is banked in and visible, writes to `$D000-$DFFF` are dropped
(they would hit IO registers, not RAM), matching `mem_access_write` in
`desfx.c`.

**Degenerate case.** For trivially tiny payloads (e.g. a 1-byte output) the
"largest written region" heuristic can select a small zeropage scratch region
instead of the intended output. This exactly matches upstream `desfx`
behaviour and is preserved deliberately.

## Testing / oracle

There is no vendored exomizer source or binary. The test suite builds the real
exomizer from source (`cd src && make exomizer`) and uses that binary as an
oracle: it crunches sample data with the C tool, decrunches with pydexomizer,
and asserts the round trip reproduces the original. The binary is located via
the `EXOMIZER` environment variable or on `PATH`. In CI the build happens in a
cached Docker stage so the oracle is compiled once and reused across test runs.
