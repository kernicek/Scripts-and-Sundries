#!/usr/bin/env bash
# Does the EC run a fixed fallback fan speed when the dGPU is powered down?
#
# Hypothesis: EC bytes +0xB2 and +0xB5 read 0 while the RTX 4060 is
# runtime-suspended, and the EC responds to the blind thermal zone by holding
# both fans at a constant 2500 RPM regardless of temperature. Keeping the GPU
# awake should populate those sensors; if the fans then drop, the fix for the
# noise is GPU power state, not the fan curve.
#
# Phase 1 baseline (GPU auto) -> phase 2 GPU pinned on -> phase 3 restored.
# Only write is power/control, restored on any exit. /dev/mem is read-only.
#
# Usage: sudo bash dgpu-fan-fallback-test.sh

set -uo pipefail

BASE=$((0xFE0B0400))
STEP=${STEP:-15}
PHASE=${PHASE:-180}
LOG=${LOG:-$(getent passwd "${SUDO_USER:-root}" | cut -d: -f6)/dgpu-fan-fallback-test.tsv}

[ "$(id -u)" -eq 0 ] || { echo "needs root" >&2; exit 1; }

GPU=""
for d in /sys/bus/pci/devices/*; do
	[ "$(cat "$d/vendor" 2>/dev/null)" = 0x10de ] || continue
	case "$(cat "$d/class" 2>/dev/null)" in 0x030*) GPU=$d; break;; esac
done
[ -n "$GPU" ] || { echo "no NVIDIA GPU found" >&2; exit 1; }

restore() {
	echo auto > "$GPU/power/control" 2>/dev/null
	echo "restored $GPU/power/control to auto" >&2
}
trap restore EXIT INT TERM

sample() {
	local -a b
	mapfile -t b < <(dd if=/dev/mem bs=1 skip=$BASE count=256 status=none \
		| od -An -tu1 -v | tr -s ' ' '\n' | sed '/^$/d')
	[ "${#b[@]}" -eq 256 ] || return 1
	printf '%s\t%s\t%s\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n' \
		"$(date +%H:%M:%S)" "$1" \
		"$(cat "$GPU/power/runtime_status")" \
		$(( b[6] * 100 )) $(( b[254] * 100 )) "${b[32]}" \
		"${b[176]}" "${b[177]}" "${b[178]}" "${b[179]}" \
		"${b[180]}" "${b[181]}" "${b[182]}" "${b[183]}"
}

run_phase() {
	local label=$1 end=$(( $(date +%s) + PHASE ))
	while [ "$(date +%s)" -lt "$end" ]; do
		sample "$label"
		sleep "$STEP"
	done
}

{
	printf 'time\tphase\tgpu\tfan1\tfan2\tFCMO\tB0\tB1\tB2\tB3\tB4\tB5\tB6\tB7\n'

	run_phase baseline

	echo on > "$GPU/power/control"
	run_phase gpu-on

	echo auto > "$GPU/power/control"
	run_phase restored
} | tee "$LOG"

echo
echo "log: $LOG"
