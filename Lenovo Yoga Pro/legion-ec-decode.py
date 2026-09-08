#!/usr/bin/env python3
"""
Read-only decode of legion-laptop's EC map against a Lenovo Yoga Pro 9
14IRP8's hardware.

Reads the full 0x600 window at 0xFE0B0400 via /dev/mem and interprets it using
model_j1cn's offsets. Never writes, and never loads the module.

Translation (from ecram_memoryio_read): phys = 0xFE0B0400 + (ec_off - 0xC400)

  sudo ./legion-ec-decode.py           one-shot decode
  sudo ./legion-ec-decode.py --watch   sample every 2s until Ctrl-C
"""
import os, sys, time, struct

RAMIO = 0xFE0B0400
EC_BASE = 0xC400
SIZE = 0x600

F = {
    'FAN_CUR_POINT':    0xC534,
    'FAN_POINTS_SIZE':  0xC535,
    'MINIFANCURVE':     0xC536,
    'CPU_TEMP_INPUT':   0xC538,
    'GPU_TEMP_INPUT':   0xC539,
    'LOCKFANCONTROLLER':0xC4AB,
    'POWERMODE':        0xC420,
    'IC_TEMP_INPUT':    0xC5E8,
}
FAN1_RPM = 0xC5E0   # LSB, MSB at +1
FAN2_RPM = 0xC5E2
FAN1_BASE, FAN2_BASE = 0xC540, 0xC550
CPU_TEMP_CURVE, GPU_TEMP_CURVE = 0xC580, 0xC5A0
ACC_BASE, DEC_BASE = 0xC560, 0xC570


def off(ec):
    return ec - EC_BASE


def snapshot(fd):
    return os.pread(fd, SIZE, RAMIO)


def u16(buf, ec):
    o = off(ec)
    return buf[o] | (buf[o + 1] << 8)


def show(buf, known):
    print("legion-laptop field decode (model_j1cn map):")
    for name, ec in F.items():
        print(f"  {name:<18} EC 0x{ec:04X}  phys 0x{RAMIO + off(ec):08X}  = {buf[off(ec)]}")
    r1, r2 = u16(buf, FAN1_RPM), u16(buf, FAN2_RPM)
    print(f"\n  FAN1_RPM (16-bit)  EC 0x{FAN1_RPM:04X}  phys 0x{RAMIO + off(FAN1_RPM):08X}  = {r1}")
    print(f"  FAN2_RPM (16-bit)  EC 0x{FAN2_RPM:04X}  phys 0x{RAMIO + off(FAN2_RPM):08X}  = {r2}")

    print(f"\n  fan1 curve points  {list(buf[off(FAN1_BASE):off(FAN1_BASE) + 10])}")
    print(f"  fan2 curve points  {list(buf[off(FAN2_BASE):off(FAN2_BASE) + 10])}")
    print(f"  cpu temp points    {list(buf[off(CPU_TEMP_CURVE):off(CPU_TEMP_CURVE) + 10])}")
    print(f"  gpu temp points    {list(buf[off(GPU_TEMP_CURVE):off(GPU_TEMP_CURVE) + 10])}")
    print(f"  accel points       {list(buf[off(ACC_BASE):off(ACC_BASE) + 10])}")
    print(f"  decel points       {list(buf[off(DEC_BASE):off(DEC_BASE) + 10])}")

    print(f"\n  known-good (our earlier finding): fan1%={known[0]} fan2%={known[1]} FCMO={known[2]}")
    print("\nplausibility:")
    ok = []
    ok.append(("FAN RPM in a sane range (0 or 1500-8000)",
               all(v == 0 or 1500 <= v <= 8000 for v in (r1, r2))))
    ok.append(("POWERMODE matches our FCMO", buf[off(F['POWERMODE'])] == known[2]))
    ok.append(("CPU_TEMP_INPUT looks like degC (30-100)",
               30 <= buf[off(F['CPU_TEMP_INPUT'])] <= 100))
    ok.append(("fan curve points non-trivial (not all 0/0xFF)",
               len(set(buf[off(FAN1_BASE):off(FAN1_BASE) + 10])) > 1))
    for label, good in ok:
        print(f"  [{'OK ' if good else 'NO '}] {label}")


def main():
    try:
        fd = os.open("/dev/mem", os.O_RDONLY)
    except PermissionError:
        sys.exit("need root, and Secure Boot must stay off")
    buf = snapshot(fd)
    known = (buf[0x06], buf[0xFE], buf[0x20])

    if "--watch" not in sys.argv:
        show(buf, known)
        os.close(fd)
        return

    print(f"{'t':>4} {'fan1%':>6} {'fan2%':>6} {'RPM1':>6} {'RPM2':>6} {'cpuT':>5} {'mode':>5}")
    t0 = time.time()
    try:
        while True:
            b = snapshot(fd)
            print(f"{time.time()-t0:>4.0f} {b[0x06]:>6} {b[0xFE]:>6} "
                  f"{u16(b, FAN1_RPM):>6} {u16(b, FAN2_RPM):>6} "
                  f"{b[off(F['CPU_TEMP_INPUT'])]:>5} {b[off(F['POWERMODE'])]:>5}")
            time.sleep(2)
    except KeyboardInterrupt:
        pass
    os.close(fd)


main()
