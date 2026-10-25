#include <string.h>
#include "include/bootlog.h"

// Single writer at a time is not guaranteed (EE threads), so a line may rarely be mixed up: acceptable for a debug view.
static char lines[BOOTLOG_LINES][BOOTLOG_WIDTH + 1];
static volatile unsigned int total; // lines added so far

void bootLogAdd(const char *text)
{
    const char *p = text;

    while (*p) {
        char tmp[BOOTLOG_WIDTH + 1];
        int n = 0;

        while (*p && *p != '\n') {
            if (*p == '\t')
                tmp[n < BOOTLOG_WIDTH ? n++ : n] = ' ';
            else if (*p != '\r' && n < BOOTLOG_WIDTH)
                tmp[n++] = *p;
            p++;
        }
        if (*p == '\n')
            p++;
        tmp[n] = '\0';

        if (n > 0) {
            unsigned int slot = total % BOOTLOG_LINES;

            strcpy(lines[slot], tmp);
            total++;
        }
    }
}

int bootLogGet(int n, char *out, int outsize)
{
    unsigned int t = total;
    unsigned int count = t < BOOTLOG_LINES ? t : BOOTLOG_LINES;

    if (n < 0 || (unsigned int)n >= count)
        return 0;

    strncpy(out, lines[(t - count + n) % BOOTLOG_LINES], outsize - 1);
    out[outsize - 1] = '\0';
    return 1;
}
