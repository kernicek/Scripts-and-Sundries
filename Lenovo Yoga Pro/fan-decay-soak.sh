#!/usr/bin/env bash
# Fan-decay soak: does fan RPM fall back to the 2100 idle floor when the
# machine is left alone, or does it stay pinned at ~2500 while every sensor is
# cool? Samples the EC window read-only and logs alongside coretemp package.
#
# Read-only: /dev/mem is opened O_RDONLY by dd, nothing is ever written.
# Needs Secure Boot off (lockdown blocks /dev/mem otherwise).
#
# Usage: sudo bash fan-decay-soak.sh
#        sudo INTERVAL=15 DURATION=3600 bash fan-decay-soak.sh

set -uo pipefail

BASE=$((0xFE0B0400))
INTERVAL=${INTERVAL:-30}
DURATION=${DURATION:-1200}
LOG=${LOG:-$(getent passwd "${SUDO_USER:-root}" | cut -d: -f6)/fan-decay-soak.tsv}

if [ "$(id -u)" -ne 0 ]; then
	echo "needs root for /dev/mem" >&2
	exit 1
fi

if [ ! -r /dev/mem ]; then
	echo "/dev/mem unreadable: Secure Boot / lockdown still on?" >&2
	exit 1
fi

pkg_temp() {
	local d f label
	for d in /sys/class/hwmon/hwmon*; do
		[ "$(cat "$d/name" 2>/dev/null)" = coretemp ] || continue
		for f in "$d"/temp*_label; do
			label=$(cat "$f")
			if [ "$label" = "Package id 0" ]; then
				echo $(( $(cat "${f%_label}_input") / 1000 ))
				return
			fi
		done
	done
	echo -1
}

sample() {
	local -a b
	mapfile -t b < <(dd if=/dev/mem bs=1 skip=$BASE count=256 status=none \
		| od -An -tu1 -v | tr -s ' ' '\n' | sed '/^$/d')
	[ "${#b[@]}" -eq 256 ] || { echo "short read (${#b[@]} bytes)" >&2; return 1; }
	printf '%s\t%s\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n' \
		"$(date +%H:%M:%S)" \
		"$(cat /sys/class/power_supply/ADP0/online 2>/dev/null)" \
		$(( b[6] * 100 )) $(( b[254] * 100 )) \
		"${b[32]}" "$(pkg_temp)" \
		"${b[176]}" "${b[177]}" "${b[178]}" "${b[179]}" \
		"${b[180]}" "${b[181]}" "${b[182]}" "${b[183]}"
}

{
	printf 'time\tac\tfan1\tfan2\tFCMO\tpkg\tB0\tB1\tB2\tB3\tB4\tB5\tB6\tB7\n'
	end=$(( $(date +%s) + DURATION ))
	while [ "$(date +%s)" -lt "$end" ]; do
		sample
		sleep "$INTERVAL"
	done
} | tee "$LOG"

echo
echo "log: $LOG"
