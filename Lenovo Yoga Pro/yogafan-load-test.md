# yogafan-load-test

Loads a locally-patched build of the `yogafan` kernel module and reports what it found,
for testing a device-path patch against a Lenovo Yoga Pro 9 14IRP8 (`yogafan` targets a
different ACPI device path by default; the patched build here is named
`yogafan_patched.ko` to distinguish it from the stock module).

## What it does

Unloads any existing `yogafan`/`yogafan_patched` module, clears `dmesg`, `insmod`s
`yogafan_patched.ko` from the build directory, then prints the module's probe log, any
`yogafan` hwmon device it registered (with fan RPM readings), and a cross-check of the
same values read directly from the raw EC bytes at `0xFE0B0400` via `/dev/mem`. Purely a
read-only driver — it only evaluates ACPI integers, never writes.

## Usage

```
sudo D=/path/to/yogafan-build ./yogafan-load-test.sh
```

`D` defaults to `$HOME/yogafan-build` and must contain the built `yogafan_patched.ko`.
Needs root.
