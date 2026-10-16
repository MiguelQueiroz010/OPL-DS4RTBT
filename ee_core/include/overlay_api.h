#ifndef _OVERLAY_API_H_
#define _OVERLAY_API_H_

// Draw the in-game overlay (stage 1: a solid red rectangle) into the frame buffer that is being displayed.
// Needs the GSM to be active for the game (it supplies the DISPFB/PMODE values). Safe to call every frame;
// it does nothing when the GS/DMA path is busy or the display registers are unknown.
void OverlayDraw(void);

#endif
