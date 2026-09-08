# legion-ec-decode

Read-only decode of the `legion-laptop` kernel module's EC field map against a Lenovo
Yoga Pro 9 14IRP8 (this chassis doesn't ship an official Legion, but the EC layout
matches `model_j1cn`'s offsets closely enough to reuse them for reverse-engineering fan
behavior).

## What it does

Reads the full `0x600` byte window at physical address `0xFE0B0400` via `/dev/mem` and
interprets it using `legion-laptop`'s `model_j1cn` field offsets — fan RPM/curve points,
CPU/GPU temp inputs, power mode, temp curve/accel/decel points — then runs a handful of
plausibility checks (RPM in a sane range, temp in a sane range, fan curve non-trivial)
so you can tell whether the offset map actually applies to this hardware. Never writes
to the EC, and never loads the `legion-laptop` module itself.

## Usage

```
sudo ./legion-ec-decode.py           one-shot decode
sudo ./legion-ec-decode.py --watch   sample every 2s until Ctrl-C
```

Needs root, and Secure Boot must stay off (kernel lockdown blocks `/dev/mem` otherwise).
