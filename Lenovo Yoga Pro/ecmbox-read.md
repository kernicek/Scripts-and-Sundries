# ecmbox-read

Read-only EC mailbox probe for a Lenovo Yoga Pro 9 14IRP8, Gen 8 — tests whether the
newer Gen 9 fan-control mailbox protocol also answers on this Gen 8 chassis.

## What it does

Issues *only* the query subcommand (`0x63`) from
[EsenbUS/yoga-pro-9i-gen9-fan-control](https://github.com/EsenbUS/yoga-pro-9i-gen9-fan-control)
against I/O ports `0x5C0`/`0x5C4`, then cross-checks the answer against the known-good
fan bytes read from the memory-mapped EC window at `0xFE0B0400` (`+0x06` fan1, `+0xFE`
fan2). Re-reads the window afterwards to confirm the probe changed nothing.

The set subcommands (`0x61`/`0x62`) are deliberately not implemented, so this binary
cannot change fan speed even if invoked wrongly.

Prints a verdict: `MATCH` if the mailbox reading is close to the EC-window reading (the
Gen 9 protocol is valid here too), a null/0xFF answer (command likely unsupported,
don't attempt to write), `MISMATCH` (different semantics, don't attempt to write), or
`TIMEOUT` (protocol doesn't answer at all on this generation).

## Usage

```
gcc -O2 -o ecmbox-read ecmbox-read.c
sudo ./ecmbox-read
```

Requires Secure Boot off (kernel lockdown blocks `ioperm` and `/dev/mem` otherwise).
