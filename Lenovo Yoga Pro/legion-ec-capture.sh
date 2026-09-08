#!/usr/bin/env bash
# Read-only EC RAM capture for a Lenovo Yoga Pro 9 14IRP8.
# Samples the DSDT-declared ERAX window at 0xFE0B0400 across idle -> load -> cooldown
# so we can spot which byte tracks fan speed. Never writes to the EC.
set -u

BASE=$((0xFE0B0400))
LEN=255
OUT=${OUT:-"$HOME/ec-capture.tsv"}
IDLE=${IDLE:-25}
LOAD=${LOAD:-60}
COOL=${COOL:-35}

[ "$(id -u)" -eq 0 ] || { echo "run as root" >&2; exit 1; }

read_win() {
  dd if=/dev/mem bs="$LEN" count=1 iflag=skip_bytes skip="$BASE" status=none |
    od -An -tu1 -v | tr -s ' ' '\n' | grep -v '^$' | paste -sd'\t'
}

probe=$(read_win)
[ -n "$probe" ] || { echo "read failed at $(printf 0x%X $BASE)" >&2; exit 1; }
echo "EC window readable, $(echo "$probe" | tr '\t' '\n' | wc -l) bytes"

PREV_PROFILE=$(tuned-adm active 2>/dev/null | sed 's/.*: //')
restore() {
  kill $(jobs -p) 2>/dev/null
  [ -n "${PREV_PROFILE:-}" ] && tuned-adm profile "$PREV_PROFILE" >/dev/null 2>&1
  echo "restored profile: ${PREV_PROFILE:-unknown}"
}
trap restore EXIT INT TERM

pkgtemp() {
  for h in /sys/class/hwmon/hwmon*; do
    [ "$(cat "$h/name" 2>/dev/null)" = coretemp ] || continue
    echo $(( $(cat "$h/temp1_input" 2>/dev/null || echo 0) / 1000 )); return
  done
  echo 0
}

{
  printf 'phase\tt\tpkgtemp'
  for i in $(seq 0 $((LEN - 1))); do printf '\tb%02X' "$i"; done
  printf '\n'
} > "$OUT"

sample() {
  printf '%s\t%s\t%s\t%s\n' "$1" "$SECONDS" "$(pkgtemp)" "$(read_win)" >> "$OUT"
}

echo "phase 1/3: idle ${IDLE}s"
for _ in $(seq "$IDLE"); do sample idle; sleep 1; done

echo "phase 2/3: load ${LOAD}s (performance profile, all cores)"
tuned-adm profile throughput-performance >/dev/null 2>&1
sleep 3
for _ in $(seq "$(nproc)"); do ( while :; do :; done ) & done
for _ in $(seq "$LOAD"); do sample load; sleep 1; done
kill $(jobs -p) 2>/dev/null

echo "phase 3/3: cooldown ${COOL}s"
tuned-adm profile "$PREV_PROFILE" >/dev/null 2>&1
for _ in $(seq "$COOL"); do sample cool; sleep 1; done

echo "wrote $OUT"
