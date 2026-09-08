#!/usr/bin/env bash
# Load the path-patched yogafan and report what it found.
# Read-only driver: it only evaluates ACPI integers, never writes.
set -u
D=${D:-"$HOME/yogafan-build"}
[ "$(id -u)" -eq 0 ] || { echo "run as root"; exit 1; }

modprobe -r yogafan 2>/dev/null
rmmod yogafan_patched 2>/dev/null

dmesg -C 2>/dev/null
if ! insmod "$D/yogafan_patched.ko"; then
    echo "insmod failed"; dmesg | tail -5; exit 1
fi

echo "== probe log =="
dmesg | grep -i yogafan

echo
echo "== hwmon =="
found=0
for h in /sys/class/hwmon/hwmon*; do
    n=$(cat "$h/name" 2>/dev/null)
    [ "$n" = yogafan ] || continue
    found=1
    echo "$h ($n)"
    for f in "$h"/fan*_input; do
        [ -e "$f" ] && echo "  $(basename "$f") = $(cat "$f") RPM"
    done
done
[ "$found" -eq 0 ] && echo "no yogafan hwmon device registered"

echo
echo "== cross-check against the raw EC bytes =="
python3 - <<'PY'
import os
fd = os.open("/dev/mem", os.O_RDONLY)
b = os.pread(fd, 0x100, 0xFE0B0400)
os.close(fd)
print(f"  EC +0x06 = {b[0x06]}  -> x100 = {b[0x06]*100} RPM")
print(f"  EC +0xFE = {b[0xFE]}  -> x100 = {b[0xFE]*100} RPM")
PY
