# legion-ec-capture

Read-only EC RAM capture for a Lenovo Yoga Pro 9 14IRP8, to spot which byte tracks fan
speed by comparing the EC window across load states.

## What it does

Samples the DSDT-declared ERAX window at `0xFE0B0400` across three phases — idle, load
(all cores pinned via `tuned-adm profile throughput-performance`), cooldown (restores
the prior tuned profile) — logging every byte of the window plus package temp to a TSV,
one row per second. Never writes to the EC.

## Usage

```
sudo ./legion-ec-capture.sh
sudo IDLE=30 LOAD=90 COOL=60 OUT=/tmp/capture.tsv ./legion-ec-capture.sh
```

`IDLE`/`LOAD`/`COOL` are phase durations in seconds (defaults 25/60/35). `OUT` defaults
to `$HOME/ec-capture.tsv`. Needs root, and a `tuned-adm` profile switcher.
