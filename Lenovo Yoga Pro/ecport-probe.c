/*
 * Passive I/O port probe: are 0x5C0/0x5C4 decoded on a Lenovo Yoga Pro 9 14IRP8 at all?
 *
 * Reads only. No outb anywhere in this program, so nothing is sent to the EC.
 * Compares the candidate mailbox ports against the known-good ACPI EC status
 * port (0x66) and against ports that should be undecoded, to establish what
 * "nothing there" looks like on this machine.
 *
 *   gcc -O2 -o ecport-probe ecport-probe.c
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
#include <sys/io.h>

static void sample(const char *label, unsigned short port)
{
    unsigned char v[5];
    for (int i = 0; i < 5; i++) { v[i] = inb(port); usleep(200); }
    printf("  0x%03X %-22s %02X %02X %02X %02X %02X",
           port, label, v[0], v[1], v[2], v[3], v[4]);
    int all_ff = 1, same = 1;
    for (int i = 0; i < 5; i++) if (v[i] != 0xFF) all_ff = 0;
    for (int i = 1; i < 5; i++) if (v[i] != v[0]) same = 0;
    if (all_ff)     printf("   <- 0xFF, port not decoded\n");
    else if (same)  printf("   <- stable, decoded\n");
    else            printf("   <- varying, decoded and live\n");
}

int main(void)
{
    if (geteuid() != 0) { fprintf(stderr, "run as root\n"); return 1; }

    /* Grab the low ports (ACPI EC reference) and the 0x5Cx candidates. */
    if (ioperm(0x60, 8, 1) || ioperm(0x5C0, 16, 1) || ioperm(0x5D0, 8, 1)) {
        fprintf(stderr, "ioperm: %s\n", strerror(errno));
        return 1;
    }

    printf("reference points:\n");
    sample("ACPI EC status (known)", 0x66);
    sample("undecoded control", 0x5D4);

    printf("\ncandidate mailbox:\n");
    sample("mailbox data?", 0x5C0);
    sample("mailbox status?", 0x5C4);

    printf("\nneighbourhood scan:\n");
    for (unsigned short p = 0x5C1; p <= 0x5C7; p++) {
        if (p == 0x5C4) continue;
        char lbl[32];
        snprintf(lbl, sizeof lbl, "+%u", p - 0x5C0);
        sample(lbl, p);
    }

    ioperm(0x60, 8, 0); ioperm(0x5C0, 16, 0); ioperm(0x5D0, 8, 0);
    return 0;
}
