# Motion Pad (experimental): phone as a steering wheel over Bluetooth

Status: **prototype, untested on hardware.** Build with `MOTIONPAD=1` (off by default).

## Idea
The phone is *not* a full controller. It only provides the wheel:

| Phone sensor | PS2 output |
|---|---|
| Roll (tilt left/right) | Left stick X (D-pad left/right in digital mode) |
| Pitch forward | Cross = accelerate (pressure follows the tilt) |
| Pitch back | Square = brake / reverse |
| Two on-screen buttons | Triangle, Circle |

The values are merged into the report of the **first real pad** in `ds34bt_get_data()`, so a normal
PADEMU controller (DS4/DualSense/DS3) keeps providing every other button. If the phone stops sending for
~2 s, the wheel is released and the real pad is untouched.

## How it works
- Android registers as a Bluetooth HID device (`BluetoothHidDevice`, API 28+) with a tiny custom descriptor.
- Like a DualShock 3, the phone opens the L2CAP control (PSM 0x11) and interrupt (PSM 0x13) channels itself.
- On the PS2 the connection request is tagged by its Class of Device (major class 2 = Phone) and the pad
  becomes type `WHEEL`. No HID descriptor is parsed and nothing is sent to the phone (no DS3 enable command).
- Input report (interrupt channel): `A1 01 | steer | throttle | brake | buttons`
  - `steer`: `0x80` = centre, `0x00` full left, `0xFF` full right
  - `throttle`, `brake`: `0..255`
  - `buttons`: bit0 Triangle, bit1 Circle

Code: `modules/pademu/ds34bt.c` (`wheel_read_report`, `wheel_overlay`, guarded by `MOTIONPAD`).
Android sample: `tools/motionpad-android/MotionPadService.kt`.

## Differences from MotionPad-PS2 (koleskyline777-git)
That project is USB tethering + a custom ELF whose source is not public, and it needs a physical pad in port 1.
This prototype shares only the idea (phone motion = wheel). No code from it is used.

## Known risks / not done
1. **Pairing.** The in-game driver only page-scans; it does not run inquiry or answer SSP IO-capability
   requests. The phone must already be bonded with the dongle (link key present in the pad keys). Pairing
   from the OPL menu driver (`modules/ds34bt/iop`) still has to be added.
2. It uses one pad slot (enable 2 BT pads in Controller Setup); the wheel's own port reports a neutral pad.
3. Android may refuse a "Phone" HID profile on some vendors' Bluetooth stacks.
4. Latency and filtering (dead zone, smoothing) need tuning on real hardware; throttle on pitch alone is awkward,
   so a hold-to-accelerate on-screen button is a sensible alternative.
5. IOP RAM: kept behind a flag because `bt_pademu.irx` is size sensitive.

## Build
`make MOTIONPAD=1` (add `DEBUG=1` for the BT log). The GitHub Action can pass the same variable.
