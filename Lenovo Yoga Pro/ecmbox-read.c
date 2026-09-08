/*
 * Read-only EC mailbox probe for a Lenovo Yoga Pro 9 14IRP8, Gen 8.
 *
 * Issues ONLY the query subcommand (0x63) from EsenbUS/yoga-pro-9i-gen9-fan-control,
 * then cross-checks the answer against the known-good fan bytes in the
 * memory-mapped EC window at 0xFE0B0400 (+0x06 fan1, +0xFE fan2).
 *
 * The set subcommands (0x61/0x62) are deliberately NOT implemented, so this
 * binary cannot change fan speed even if invoked wrongly.
 *
 * Requires Secure Boot off (lockdown blocks ioperm and /dev/mem).
 *   gcc -O2 -o ecmbox-read ecmbox-read.c
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/io.h>

#define PORT_DATA 0x5C0
#define PORT_CMD  0x5C4

#define CMD_FAN         0xEF
#define SUBCMD_QUERY    0x63
#define QUERY_READ_FAN1 0x01
#define QUERY_READ_FAN2 0x02

#define EC_PHYS   0xFE0B0400UL
#define OFF_FAN1  0x06
#define OFF_FAN2  0xFE

#define MAX_SPINS 20000   /* ~200 ms at 10 us */

static int spin_ibe(void)   /* input buffer empty: bit 1 clear */
{
    for (int i = 0; i < MAX_SPINS; i++) {
        if ((inb(PORT_CMD) & 0x02) == 0) return 0;
        usleep(10);
    }
    return -1;
}

static int spin_obf(void)   /* output buffer full: bit 0 set */
{
    for (int i = 0; i < MAX_SPINS; i++) {
        if ((inb(PORT_CMD) & 0x01) == 1) return 0;
        usleep(10);
    }
    return -1;
}

static int spin_obe(void)   /* output buffer empty, draining stale bytes */
{
    for (int i = 0; i < MAX_SPINS; i++) {
        if ((inb(PORT_CMD) & 0x01) == 0) return 0;
        (void)inb(PORT_DATA);
        usleep(10);
    }
    return -1;
}

/* One mailbox transaction. Returns result byte, or -1 on timeout. */
static int mbey(unsigned char cmd, unsigned char subcmd, unsigned char arg)
{
    if (spin_ibe()) return -1;
    if (spin_obe()) return -1;
    outb(cmd, PORT_CMD);
    if (spin_ibe()) return -1;
    outb(subcmd, PORT_DATA);
    if (spin_ibe()) return -1;
    outb(arg, PORT_DATA);
    if (spin_ibe()) return -1;
    if (spin_obf()) return -1;
    return inb(PORT_DATA);
}

static int ec_window_byte(int fd, unsigned long off, unsigned char *out)
{
    return pread(fd, out, 1, (off_t)(EC_PHYS + off)) == 1 ? 0 : -1;
}

int main(void)
{
    if (geteuid() != 0) { fprintf(stderr, "run as root\n"); return 1; }

    int memfd = open("/dev/mem", O_RDONLY);
    if (memfd < 0) {
        fprintf(stderr, "open /dev/mem: %s%s\n", strerror(errno),
                errno == EPERM ? " (Secure Boot lockdown still active?)" : "");
        return 1;
    }

    unsigned char m1 = 0, m2 = 0;
    if (ec_window_byte(memfd, OFF_FAN1, &m1) || ec_window_byte(memfd, OFF_FAN2, &m2)) {
        fprintf(stderr, "EC window read failed: %s\n", strerror(errno));
        close(memfd);
        return 1;
    }
    printf("EC window  0xFE0B0400: fan1(+0x06)=%u  fan2(+0xFE)=%u\n", m1, m2);

    if (ioperm(PORT_DATA, 8, 1)) {
        fprintf(stderr, "ioperm(0x%X): %s%s\n", PORT_DATA, strerror(errno),
                errno == EPERM ? " (Secure Boot lockdown still active?)" : "");
        close(memfd);
        return 1;
    }

    int f1 = mbey(CMD_FAN, SUBCMD_QUERY, QUERY_READ_FAN1);
    int f2 = mbey(CMD_FAN, SUBCMD_QUERY, QUERY_READ_FAN2);
    ioperm(PORT_DATA, 8, 0);

    printf("EC mailbox 0x5C0/0x5C4: ");
    if (f1 < 0 || f2 < 0) printf("TIMEOUT (fan1=%d fan2=%d) -> protocol does not answer on Gen 8\n", f1, f2);
    else                  printf("fan1=%u  fan2=%u\n", (unsigned)f1, (unsigned)f2);

    /* Re-read the window afterwards: confirms the probe changed nothing. */
    unsigned char a1 = 0, a2 = 0;
    ec_window_byte(memfd, OFF_FAN1, &a1);
    ec_window_byte(memfd, OFF_FAN2, &a2);
    printf("EC window after       : fan1=%u  fan2=%u%s\n", a1, a2,
           (a1 == m1 && a2 == m2) ? "  (unchanged)" : "  (CHANGED)");

    if (f1 >= 0 && f2 >= 0) {
        int d1 = abs(f1 - (int)m1), d2 = abs(f2 - (int)m2);
        printf("\nverdict: ");
        if (d1 <= 3 && d2 <= 3)
            printf("MATCH (delta %d/%d) -> Gen 9 mailbox protocol is valid on Gen 8\n", d1, d2);
        else if ((f1 == 0 && f2 == 0) || f1 == 0xFF || f2 == 0xFF)
            printf("answered but with a null/0xFF value -> command likely unsupported, do NOT write\n");
        else
            printf("MISMATCH (mailbox %d/%d vs window %u/%u) -> different semantics, do NOT write\n",
                   f1, f2, m1, m2);
    }

    close(memfd);
    return 0;
}
