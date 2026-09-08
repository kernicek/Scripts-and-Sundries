# fan-decay-soak

Long-running soak test on a Lenovo Yoga Pro 9 14IRP8: does fan RPM fall back to the
~2100 idle floor when the machine is left alone, or does it stay pinned at ~2500 while
every sensor is cool?

## What it does

Samples the EC window at `0xFE0B0400` read-only every `INTERVAL` seconds for `DURATION`
seconds, logging alongside the coretemp package temperature and AC-online state to a
TSV. Nothing is ever written — `/dev/mem` is opened `O_RDONLY`.

## Usage

```
sudo bash fan-decay-soak.sh
sudo INTERVAL=15 DURATION=3600 bash fan-decay-soak.sh
```

`LOG` defaults to `~/fan-decay-soak.tsv` for the invoking (sudo) user. Needs root, and
Secure Boot off (kernel lockdown blocks `/dev/mem` otherwise) — the script checks this
and exits with a clear message if `/dev/mem` isn't readable.
