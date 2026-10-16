#ifndef _OVERLAY_API_H_
#define _OVERLAY_API_H_

// Draw the in-game overlay (stage 1: a solid red rectangle) into the frame buffer that is being displayed.
// Needs the GSM to be active for the game (it supplies the DISPFB/PMODE values). Safe to call every frame;
// it does nothing when the GS/DMA path is busy or the display registers are unknown.
void OverlayDraw(void);

// Result of the last OverlayDraw() call, for on-screen debugging (see padhook.c).
enum {
    OVERLAY_DRAWN = 0,
    OVERLAY_NO_DISPLAY = 1, // GSM has not seen the game enable a display circuit
    OVERLAY_BAD_FB = 2,     // unusable DISPFB (width 0 or pixel format not supported)
    OVERLAY_DMA_BUSY = 3,   // game DMA / VIF1 busy, skipped
};
extern int OverlayLastResult;

#endif
