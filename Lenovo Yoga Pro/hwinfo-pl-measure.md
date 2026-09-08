# hwinfo-pl-measure

Reads Intel PL1/PL2 power limits (and package power/temp/throttle state) from
[HWiNFO](https://www.hwinfo.com/)'s shared-memory interface on a Lenovo Yoga Pro 9
14IRP8, for comparing thermal-mode/power-mode combinations.

## Setup

HWiNFO64 must be running with Settings → "Shared Memory Support" ticked (the free
version disables it again after 12h, so re-tick it if readings stop).

## Usage

```
.\hwinfo-pl-measure.ps1 -Label 'batterysaving-AC-idle'
.\hwinfo-pl-measure.ps1 -Label 'batterysaving-AC-load' -Load -Seconds 90
```

- `-Label` — tag for this sample set, written into the CSV.
- `-Load` — spin up one CPU-bound PowerShell process per logical core (`-Threads` to
  override the count) for `-Seconds` seconds while sampling, to see limits under load.
  Without `-Load` it takes a single idle snapshot.
- `-IntervalMs` — sample interval while under load (default 2500ms).

Set the Lenovo thermal mode with Fn+Q *before* each run — the Windows power-mode slider
does not change the power limits on this chassis. Appends every run to
`pl-samples.csv` next to the script.
