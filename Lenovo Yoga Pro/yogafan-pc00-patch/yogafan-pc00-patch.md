# yogafan-pc00-patch

Patch adding Lenovo Yoga Pro 9 14IRP8 (83BU) support to the `yogafan` fan-monitor kernel
driver by Sergio Melas.

## Why this is needed

`yogafan`'s stock DMI-quirk table only knows the `PCI0/LPC0` ACPI naming most Lenovo
Yoga/Legion models use. Newer Intel platforms like the 14IRP8 expose the same `FANS`
object under `PC00/LPCB` instead — the object itself is unchanged, only the ACPI path
differs, so the driver otherwise fails to find any fan handle and reports nothing. This
patch adds a `yoga_pc00_cfg` DMI-quirk entry (matched on `DMI_PRODUCT_NAME "83BU"`) with
four candidate paths (`PC00.LPCB.EC0`/`H_EC` × `FANS`/`FA2S`) — the extra candidates are
harmless since `acpi_get_handle` simply fails and is skipped for any path that doesn't
exist — plus a `pr_info` per candidate so `dmesg` shows exactly which path matched.

## Usage

```
cp /path/to/yogafan.c yogafan-patched/yogafan_patched.c
patch yogafan-patched/yogafan_patched.c < yogafan-pc00.patch
cd yogafan-patched && make
sudo insmod yogafan_patched.ko
```

See [../yogafan-load-test.sh](../yogafan-load-test.md) for a script that loads the built
module and reports what it found, and [../legion-ec-decode.md](../legion-ec-decode.md) /
[../legion-ec-capture.md](../legion-ec-capture.md) for reading the same fan values
straight out of the EC window to cross-check the driver's output.

## Caveats

Only tested against a Yoga Pro 9 14IRP8 (DMI product name `83BU`) — other newer-Intel
Lenovo laptops hitting the same `PCI0/LPC0` failure likely need their own DMI match
added, though the `PC00/LPCB` paths may well be shared.
