#ifndef _PADSETUP_H_
#define _PADSETUP_H_

/*
 * "Controller Setup" (PADEMU): button remapping, PS button and touchpad behaviour.
 * Shared by the OPL GUI (EE), ee_core (which hands the blob to the IOP) and the in-game
 * pad emulator (pademu IRX). The blob is a fixed-size packed structure; the OPL config
 * stores it as a hex string (conf_opl.cfg, CONFIG_ITEM_PADEMU_SETUP).
 */

#define PADSETUP_ARG_LEN 28
#define PADSETUP_HEX_LEN (PADSETUP_ARG_LEN * 2)
#define PADSETUP_MAGIC0  'C'
#define PADSETUP_MAGIC1  'S'
#define PADSETUP_VERSION 1

// touch_mode
enum {
    PADSETUP_TOUCH_SELSTART = 0, // original behaviour: click on the left half = Select, right half = Start
    PADSETUP_TOUCH_BUTTON = 1,   // click = touch_click button, no touch position handling
    PADSETUP_TOUCH_RSTICK_DRAG = 2,
    PADSETUP_TOUCH_LSTICK_DRAG = 3,
    PADSETUP_TOUCH_RSTICK_MOUSE = 4,
    PADSETUP_TOUCH_LSTICK_MOUSE = 5,
    PADSETUP_TOUCH_MODE_COUNT = 6,
};

// ps_hold (long press of the PS button, emulates the OPL in-game reset combos)
enum {
    PADSETUP_PSHOLD_NONE = 0,
    PADSETUP_PSHOLD_EXIT = 1,       // L1+L2+R1+R2+Start+Select: back to the OPL menu
    PADSETUP_PSHOLD_POWEROFF = 2,   // L1+L2+R1+R2+L3+R3: power off
    PADSETUP_PSHOLD_SCREENSHOT = 3, // L1+L2+R1+R2+Up: in-game screenshot (GSM/IGS)
    PADSETUP_PSHOLD_OVERLAY = 4,    // L1+L2+R1+R2+Down: in-game overlay (needs GSM + IGS build)
    PADSETUP_PSHOLD_COUNT = 5,
};

// Button targets: 0 = no change/none, 1..16 = DS2 button bit number + 1 (select, l3, r3, start, up, right, down,
// left, l2, r2, l1, r1, triangle, circle, cross, square). For remap[] a value of 0xFF disables the button.
#define PADSETUP_TARGET_DISABLED 0xFF

typedef struct
{
    unsigned char magic[2];
    unsigned char version;
    unsigned char touch_mode;
    unsigned char touch_sens;    // 1..8
    unsigned char touch_click;   // button pressed by the touchpad click (modes other than SELSTART)
    unsigned char ps_tap;        // button pulsed by a short press of the PS button
    unsigned char ps_hold;       // PADSETUP_PSHOLD_*
    unsigned char ps_hold_time;  // 0 = 1s, 1 = 2s, 2 = 3s
    unsigned char reserved0;
    unsigned char remap[16];     // per DS2 button: 0 = unchanged, 0xFF = disabled, else target + 1
    unsigned char reserved1[2];
} __attribute__((packed)) padsetup_t;

_Static_assert(sizeof(padsetup_t) == PADSETUP_ARG_LEN, "padsetup_t size");

static inline void padsetup_default(padsetup_t *s)
{
    unsigned char *p = (unsigned char *)s;
    int i;

    for (i = 0; i < PADSETUP_ARG_LEN; i++)
        p[i] = 0;
    s->magic[0] = PADSETUP_MAGIC0;
    s->magic[1] = PADSETUP_MAGIC1;
    s->version = PADSETUP_VERSION;
    s->touch_sens = 4;
    s->ps_hold = PADSETUP_PSHOLD_EXIT; // basic IGR: hold PS to go back to the OPL menu
    s->ps_hold_time = 1;               // 2 seconds
}

static inline int padsetup_valid(const padsetup_t *s)
{
    return s->magic[0] == PADSETUP_MAGIC0 && s->magic[1] == PADSETUP_MAGIC1 && s->version == PADSETUP_VERSION;
}

static inline int padsetup_is_default(const padsetup_t *s)
{
    padsetup_t d;
    const unsigned char *a = (const unsigned char *)s, *b = (const unsigned char *)&d;
    int i;

    padsetup_default(&d);
    for (i = 0; i < PADSETUP_ARG_LEN; i++)
        if (a[i] != b[i])
            return 0;
    return 1;
}

static inline void padsetup_to_hex(const padsetup_t *s, char *out)
{
    static const char hex[] = "0123456789ABCDEF";
    const unsigned char *p = (const unsigned char *)s;
    int i;

    for (i = 0; i < PADSETUP_ARG_LEN; i++) {
        out[2 * i] = hex[p[i] >> 4];
        out[2 * i + 1] = hex[p[i] & 15];
    }
    out[PADSETUP_HEX_LEN] = '\0';
}

// Returns 1 and fills *s when str holds a valid blob; otherwise *s is the default setup and 0 is returned.
static inline int padsetup_from_hex(const char *str, padsetup_t *s)
{
    unsigned char *p = (unsigned char *)s;
    int i, hi, lo;

    padsetup_default(s);
    for (i = 0; i < PADSETUP_ARG_LEN; i++) {
        char a = str[2 * i], b;
        if (a == '\0')
            goto bad;
        b = str[2 * i + 1];
        hi = (a >= '0' && a <= '9') ? a - '0' : (a >= 'A' && a <= 'F') ? a - 'A' + 10 : (a >= 'a' && a <= 'f') ? a - 'a' + 10 : -1;
        lo = (b >= '0' && b <= '9') ? b - '0' : (b >= 'A' && b <= 'F') ? b - 'A' + 10 : (b >= 'a' && b <= 'f') ? b - 'a' + 10 : -1;
        if (hi < 0 || lo < 0)
            goto bad;
        p[i] = (unsigned char)((hi << 4) | lo);
    }
    if (!padsetup_valid(s))
        goto bad;
    if (s->touch_sens < 1 || s->touch_sens > 8)
        s->touch_sens = 4;
    return 1;
bad:
    padsetup_default(s);
    return 0;
}

#endif
