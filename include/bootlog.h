#ifndef __BOOTLOG_H
#define __BOOTLOG_H

// Last lines of the OPL log kept in memory so the debug build can draw them on the screen (under the VRAM / FPS block).
// When the OPL stops during start-up the last lines on screen say what it was doing.

#define BOOTLOG_LINES 14
#define BOOTLOG_WIDTH 52 // characters kept per line (the rest is cut)

// Adds the text, one entry per line (empty lines are skipped). Safe to call from any thread.
void bootLogAdd(const char *text);

// Copies the line `n` (0 = oldest shown) into out; returns 0 when there is no such line yet.
int bootLogGet(int n, char *out, int outsize);

#endif
