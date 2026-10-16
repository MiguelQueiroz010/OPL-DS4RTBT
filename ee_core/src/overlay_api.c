/*
 * In-game overlay, stage 1.
 *
 * Draws a filled rectangle into the frame buffer that is currently displayed, using GS drawing context 2
 * (most games only use context 1) and the same VIF1 DIRECT path the IGS screenshot code uses.
 * The display registers come from the GSM shadow copy (GSMSourceGSRegs), so this only works when the GSM is
 * active for the game. It is called from the IGR polling thread, which runs at low priority (when the game is idle).
 *
 * Touched GS state: FRAME_2, ZBUF_2, XYOFFSET_2, SCISSOR_2, TEST_2, FBA_2, PRIM, RGBAQ and the vertex queue.
 */

#include "include/igs_api.h"
#include "include/overlay_api.h"

// GS general registers (A+D addresses)
#define OV_PRIM       0x00
#define OV_RGBAQ      0x01
#define OV_XYZ2       0x05
#define OV_XYOFFSET_2 0x19
#define OV_SCISSOR_2  0x41
#define OV_TEST_2     0x48
#define OV_FBA_2      0x4B
#define OV_FRAME_2    0x4D
#define OV_ZBUF_2     0x4F

#define OV_NREGS 10 // A+D writes below
#define OV_QWC   (1 + 1 + OV_NREGS + 1) // VIF codes, GIF tag, A+D pairs, VIF codes (re-enable PATH3)

#define OV_WAIT_LOOPS 20000

static u32 ov_packet[OV_QWC * 4] __attribute__((aligned(16)));

int OverlayLastResult = OVERLAY_NO_DISPLAY;

static u64 ov_xy(u32 x, u32 y)
{
    return (u64)((x << 4) & 0xFFFF) | ((u64)((y << 4) & 0xFFFF) << 16);
}

void OverlayDraw(void)
{
    u64 pmode, dispfb;
    u32 fbp, fbw, psm, i;
    u32 *p;
    u64 *q;

    pmode = GSMSourceGSRegs.pmode;
    dispfb = GET_PMODE_EN2(pmode) ? GSMSourceGSRegs.dispfb2 : GSMSourceGSRegs.dispfb1;

    if (!GET_PMODE_EN1(pmode) && !GET_PMODE_EN2(pmode))
    {
        OverlayLastResult = OVERLAY_NO_DISPLAY;
        return; // display registers unknown (GSM has not seen the game set them yet)
    }

    fbp = GET_DISPFB_FBP(dispfb);
    fbw = GET_DISPFB_FBW(dispfb);
    psm = GET_DISPFB_PSM(dispfb);
    if (fbw == 0 || (psm != GS_PSM_CT32 && psm != GS_PSM_CT24 && psm != GS_PSM_CT16 && psm != GS_PSM_CT16S)) {
        OverlayLastResult = OVERLAY_BAD_FB;
        return;
    }

    // Do not wait for the game: if its DMA to VIF1/GIF is in progress, try again on the next frame.
    for (i = 0; (*GS_D1_CHCR & 0x0100) && i < OV_WAIT_LOOPS; i++)
        ;
    if (*GS_D1_CHCR & 0x0100) {
        OverlayLastResult = OVERLAY_DMA_BUSY;
        return;
    }
    for (i = 0; (*GS_VIF1_STAT & 0x1f000000) && i < OV_WAIT_LOOPS; i++)
        ;
    if (*GS_VIF1_STAT & 0x1f000000) {
        OverlayLastResult = OVERLAY_DMA_BUSY;
        return;
    }

    p = (u32 *)UNCACHED_SEG(ov_packet);

    // VIF1 codes: stop PATH3, wait for it to drain, then DIRECT the following qwords to the GIF
    p[0] = GS_VIF1_NOP;
    p[1] = GS_VIF1_MSKPATH3(0x8000);
    p[2] = GS_VIF1_FLUSHA;
    p[3] = GS_VIF1_DIRECT(1 + OV_NREGS);

    q = (u64 *)(p + 4);
    q[0] = GS_GIFTAG(OV_NREGS, 1, 0, 0, 0, 1); // PACKED, REGS = A+D
    q[1] = GS_GIF_AD;
#define OV_AD(n, reg, val) \
    do {                   \
        q[2 + 2 * (n)] = (val); \
        q[3 + 2 * (n)] = (reg); \
    } while (0)
    OV_AD(0, OV_FRAME_2, (u64)fbp | ((u64)fbw << 16) | ((u64)psm << 24));
    OV_AD(1, OV_ZBUF_2, (u64)1 << 32);                                    // ZMSK: never write Z
    OV_AD(2, OV_XYOFFSET_2, 0);
    OV_AD(3, OV_SCISSOR_2, ((u64)2047 << 16) | ((u64)2047 << 48));        // 0..2047 x 0..2047
    OV_AD(4, OV_TEST_2, ((u64)1 << 16) | ((u64)1 << 17));                 // ZTE on, ZTST = ALWAYS: no test
    OV_AD(5, OV_FBA_2, 0);
    OV_AD(6, OV_PRIM, 6 | (1 << 9));                                      // SPRITE, context 2, no texture/blend
    OV_AD(7, OV_RGBAQ, 0xFFULL | (0x80ULL << 24) | ((u64)0x3F800000 << 32)); // red, A=0x80, Q=1.0
    OV_AD(8, OV_XYZ2, ov_xy(32, 32));
    OV_AD(9, OV_XYZ2, ov_xy(96, 80));                                     // kicks the sprite
#undef OV_AD

    // VIF1 codes: let PATH3 run again
    p += 4 + 4 * (1 + OV_NREGS);
    p[0] = GS_VIF1_NOP;
    p[1] = GS_VIF1_NOP;
    p[2] = GS_VIF1_NOP;
    p[3] = GS_VIF1_MSKPATH3(0);

    asm volatile("sync.l");

    *GS_D1_QWC = OV_QWC;
    *GS_D1_MADR = (u32)ov_packet;
    *GS_D1_CHCR = 0x101;
    asm volatile("sync.l");
    OverlayLastResult = OVERLAY_DRAWN;
}
