# dgpu-fan-fallback-test

Tests whether the EC runs a fixed fallback fan speed on a Lenovo Yoga Pro 9 14IRP8 when
the discrete GPU is powered down.

## Hypothesis being tested

EC bytes `+0xB2` and `+0xB5` read 0 while the RTX 4060 is runtime-suspended, and the EC
responds to the blind thermal zone by holding both fans at a constant ~2500 RPM
regardless of temperature. Keeping the GPU awake should populate those sensors; if the
fans then drop, the fix for the noise is GPU power state, not the fan curve.

## What it does

Phase 1 baseline (GPU power management left on `auto`) → phase 2 GPU pinned `on` →
phase 3 restored to `auto`. Each phase samples the EC window plus GPU runtime-power
status every `STEP` seconds for `PHASE` seconds, logging to a TSV. The only write is to
the GPU's `power/control` sysfs attribute, always restored to `auto` on exit (including
Ctrl-C). `/dev/mem` is opened read-only throughout.

## Usage

```
sudo bash dgpu-fan-fallback-test.sh
sudo STEP=10 PHASE=300 LOG=/tmp/dgpu-test.tsv bash dgpu-fan-fallback-test.sh
```

`LOG` defaults to `~/dgpu-fan-fallback-test.tsv` for the invoking (sudo) user. Needs
root and an NVIDIA GPU present under `/sys/bus/pci/devices`.
