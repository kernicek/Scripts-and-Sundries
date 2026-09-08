# ecport-probe

Passive I/O port probe: are `0x5C0`/`0x5C4` (the candidate EC mailbox ports used by
[ecmbox-read](ecmbox-read.md)) actually decoded on a Lenovo Yoga Pro 9 14IRP8 at all?

## What it does

Samples each candidate port five times, 200μs apart, and classifies it:

- `0xFF, port not decoded` — all five reads are `0xFF`.
- `stable, decoded` — all five reads agree on a non-`0xFF` value.
- `varying, decoded and live` — the reads change between samples.

Runs the same classification against the known-good ACPI EC status port (`0x66`, as a
reference for what "decoded" looks like) and a port expected to be undecoded (`0x5D4`),
then scans the `0x5C1`-`0x5C7` neighborhood. Read-only — no `outb` anywhere in the
program, so nothing is ever written to the EC.

## Usage

```
gcc -O2 -o ecport-probe ecport-probe.c
sudo ./ecport-probe
```
