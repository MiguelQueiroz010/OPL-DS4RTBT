# OPL-DS4RTBT

**English** | [Português (Brasil)](README.pt-BR.md)

A fork of [Open PS2 Loader](https://github.com/ps2homebrew/Open-PS2-Loader) with **Bluetooth controller support** in PADEMU. Play your PS2 wirelessly with a **DualShock 4 (original or clone), DualSense or DS3** through a USB Bluetooth dongle.

## Features

- Wireless pads in the OPL menu and in-game: buttons, sticks, rumble and lightbar.
- Wireless pairing from the menu: `Bluetooth Pads → Search`, pick the pad, done. No cable, no PC.
- Up to 4 Bluetooth pads at once, all of them can navigate the menu. Battery indicator per pad.
- Realtek dongles (RTL8761B/BU): firmware loaded automatically.
- `Controller Setup`: lightbar colour per slot and button remapping.
- Rumble that works on DS4 clones, and a `Controller Test` screen.
- Multitap emulation.

## Quick start

1. Download the `.ELF` from [Releases](../../releases) and launch it like any OPL. You need a **USB Bluetooth dongle** plugged into the PS2.
2. `Start → Controller Settings → Configure PADEMU` (or per game: select it, press `Triangle`). Set `Pad Emulator` to **On**, `Pad Emulator Mode` to **DS3/DS4/DS5 BT**, enable `Emulation` for the port, then `Save Changes`.
3. Pair once: `Bluetooth Pads → Search`, then put the pad in pairing mode (**PS + Share** on DS4, **PS + Create** on DualSense). The DS3 has no pairing mode, pair it with a USB cable (`Pair`).
4. Launch the game and press **PS** on the pad once the game is on screen (launching a game resets USB, so the pad reconnects).

<img src="docs/img/pademu-settings.jpg" alt="Pad Emulator Settings" width="480"> <img src="docs/img/wireless-pairing.jpg" alt="Wireless Pairing" width="480">

## Compatibility

- **Tested:** PS2 Slim SCPH-90001, Realtek dongle `0BDA:8771`, DualSense (wireless and USB pairing, menu and in-game).
- **Should work:** any PS2 that runs OPL, DualShock 4 (original and "Wireless Controller" clones), DualSense, DS3, Realtek RTL8761B/BU and most Bluetooth 2.1+ dongles that don't need firmware from the OS.
- **Probably not:** dongles that need other firmware, BLE-only dongles, some DS4 clones (old PIN pairing only).
- **Limits:** pads 3 and 4 only drive the OPL menu; Kingdom Hearts II over SMB with PADEMU has little IOP memory (USB/HDD ISO frees it).

Tell us how it went on your setup in an [issue](../../issues) (PS2 model, dongle, controller, what worked). Logs help a lot: run `python tools/ps2_log.py` on your PC and use a debug build.

## Building

With [ps2dev](https://github.com/ps2dev/ps2dev) set up (`PS2DEV` and `PS2SDK` exported):

```sh
make download_lng
make                          # release
make DEBUG=1 INGAME_DEBUG=1   # debug build with network logs
```

After changing shared headers (such as `ee_core/include/coreconfig.h`), do a `make clean` and remove `ee_core/obj` once. Upstream docs: [README-OPL.md](README-OPL.md).

## Credits

- **Miguel Queiroz** ([@MiguelQueiroz010](https://github.com/MiguelQueiroz010)): maintainer of this fork.
- **Rodrigo Galvan** ([rodrigoGalvanDev](https://github.com/rodrigoGalvanDev/OPL-DualSense-BT)): original OPL-DualSense-BT project (DualSense over Bluetooth, SDP, wireless pairing).
- The [Open PS2 Loader](https://github.com/ps2homebrew/Open-PS2-Loader) team and everyone behind PADEMU.
- Bluetooth driver based on [Arduino-PSRemote](https://github.com/IonAgorria/Arduino-PSRemote) and [USB Host Shield 2.0](https://github.com/felis/USB_Host_Shield_2.0). Realtek firmware from [linux-firmware](https://git.kernel.org/pub/scm/linux/kernel/git/firmware/linux-firmware.git).

License: [Academic Free License v3.0](LICENSE).
