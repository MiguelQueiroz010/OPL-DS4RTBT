# OPL-DS4RTBT

A fork of [Open PS2 Loader](https://github.com/ps2homebrew/Open-PS2-Loader) with **Bluetooth controller support** in PADEMU: play your PS2 wirelessly with a **DualShock 4 (original or clone), DualSense or DS3**, through a USB Bluetooth dongle. No cable from the couch to the console.

## What's new

- **Wireless pads in the OPL menu and in-game:** DualShock 4 (original and "Wireless Controller" clones), DualSense and DS3. Buttons, sticks, rumble and lightbar.
- **Realtek dongles (RTL8761B/BU):** the firmware is loaded automatically at startup, in the menu and in-game.
- **Wireless pairing from the OPL menu:** `Bluetooth Pads → Search`, pick the pad from the list, done. The same screen shows the connected pads (type and battery) with a `Disconnect` button each. No cable, no PC.
- **Up to 4 Bluetooth pads at once.** All of them can navigate the OPL menu.
- **Battery indicator in the menu:** one card per connected pad (slot, type, 5-segment battery, percentage, charging bolt, low battery alert).
- **Lightbar colour per slot** in `Controller Setup` (Default, Red, Green, Blue, Yellow, Cyan, Magenta, White, Orange or Off), applied in the menu and in-game.
- **Rumble that works on DS4 clones**, with a wider range for the big motor (clones barely react to low values).
- **Controller Test** screen: LED, rumble and button test.
- **Kingdom Hearts II (SLPM-66675) with PADEMU + SMB** has sound again: less IOP memory used by the network stack and by USBD.
- Everything that already worked in stock OPL (DS3, DS4 and USB pairing) keeps working.

## Getting started

Grab the `.ELF` from the [Releases](../../releases) page and launch it however you usually launch OPL (FreeMcBoot, uLaunchELF, a modchip, whatever). It's a regular OPL, so your games and settings work as usual.

You need a **USB Bluetooth dongle** plugged into the PS2 (see [Compatibility](#compatibility)).

### 1. Turn on the pad emulator

- **For all games:** `Start → Controller Settings → Configure PADEMU`
- **For a single game:** select the game, press `Triangle`, then go to `Configure PADEMU`

Then set:
- `Pad Emulator` → **On**
- `Pad Emulator Mode` → **DS3/DS4/DS5 BT**
- `Settings For Port` → pick the port (1P, 2P...) and turn on `Emulation` (and `Vibration` if you want rumble)

<img src="docs/img/pademu-settings.jpg" alt="Pad Emulator Settings with the DS3/DS4/DS5 BT mode" width="640">

Don't forget `Save Changes`. If you skip it, the game launches without the emulator and you'll swear the pad is broken.

### 2. Pair the pad (only once)

**Wireless (recommended):**
1. In the same PADEMU screen, go to `Bluetooth Pads → Search`.
2. Put the pad in pairing mode: **PS + Share** on the DualShock 4, **PS + Create** on the DualSense (hold until the light blinks fast).
3. Your pad shows up in the list. Select it and wait for `Paired and saved`.

**Note:** wireless pairing works with the DualShock 4 and the DualSense. The DS3 has no pairing mode, so it still needs the cable method below.

<img src="docs/img/wireless-pairing.jpg" alt="Wireless Pairing screen finding a controller" width="640">

**With a cable:**
1. Plug the pad into the PS2 with a USB cable (dongle in the other port).
2. Press `Pair`, unplug the cable and press PS.

The pairing is saved, so you don't have to do it again. Next time just press PS.

### 3. Pick the colours (optional)

`Controller Setup` has a lightbar colour for each of the 4 slots. The colour is applied when the pad connects, and the same colour is used in-game.

### 4. Play

Launch the game and press **PS** on the pad once the game is on screen. Launching a game resets the PS2's USB side, so the pad always disconnects for a second and needs that PS press to come back. Reconnecting takes a fraction of a second.

## Compatibility

### Tested

| What | Model |
|---|---|
| Console | PS2 Slim SCPH-90001 (Matrix modchip) |
| Dongle | Realtek, USB ID `0BDA:8771` |
| Controller | DualSense (wireless pairing, USB pairing, menu and in-game) |
| Mixed | DualSense on 1P via Bluetooth + wired DualShock 2 on 2P |

That setup is from the project this fork started from. DS4 clones and Realtek dongles are what this fork is developed and tested with. Everything else below comes from how the code works, so reports from other setups are very welcome (see [Report your setup](#report-your-setup)).

### Should work

- **Any PS2 that runs OPL** (fat or slim). There's nothing model-specific in here.
- **Dongles:** Realtek RTL8761B/BU (firmware loaded automatically) and most USB Bluetooth adapters that don't need firmware loaded by the OS. CSR8510-based ones are the classic pick for PADEMU. The wireless search needs **Bluetooth 2.1 or newer**. USB pairing works with older dongles too.
- **DualShock 4 original** (CUH-ZCT1 and ZCT2) and **DS4 clones** that show up as "Wireless Controller".
- **DualSense and DualSense Edge:** same reports, recognized by name.
- **DS3**, as in stock OPL.

### Probably won't work / unknown

- **Dongles that need firmware uploaded** other than the Realtek RTL8761B/BU (some Intel and Broadcom ones), and **BLE-only dongles**.
- **Cheap clone CSR dongles:** a coin toss.
- **Some DS4 clones:** depends on the clone. Some only do old PIN pairing (the wireless search doesn't handle that yet), and on some the lightbar colour doesn't change yet.

### Limitations

- **4 pads** at once. Pads 3 and 4 have no physical PS2 port behind them, so they only drive the OPL menu; in-game the pads follow the ports you enabled in PADEMU.
- Up to **4 pads** paired with the wireless search are remembered. Pairing a 5th forgets the oldest one.
- Some games just don't like PADEMU (games with their own pad drivers, or that use USB for something else). That's the same as stock OPL.
- **Kingdom Hearts II over SMB with PADEMU** has very little IOP memory to spare. Running the ISO from USB or HDD frees the whole network stack.
- On a fat PS2 with HDD + VMC + cheats all on, some games may run out of IOP memory. That's also a stock OPL thing.

### Report your setup

Open an [issue](../../issues) with:
- PS2 model (e.g. SCPH-90001)
- Dongle (brand, and the USB ID if you can get it: `xxxx:xxxx`)
- Controller (DualShock 4 original/clone, DualSense, DS3...)
- What worked: USB pairing / wireless search / menu / in-game / lightbar / rumble

If something's broken, a log helps a ton (see the next section).

## Debug build and logs

A debug build sends logs over the network:

1. Connect the PS2 to your router with an Ethernet cable and set its IP in OPL's network settings.
2. On your PC (same network), run `python tools/ps2_log.py`. It listens on UDP port 18194 and saves everything to `ps2_log.txt`.
3. Launch the debug ELF (see [Building](#building)), reproduce the problem and attach `ps2_log.txt` to your issue.

## Building

Same as regular OPL: you need [ps2dev/ps2sdk](https://github.com/ps2dev/ps2dev) set up (`PS2DEV` and `PS2SDK` exported), then:

```sh
make download_lng
make            # release
make DEBUG=1 INGAME_DEBUG=1   # debug build with network logs
```

See [README-OPL.md](README-OPL.md) for the full upstream docs (game formats, devices, settings and so on).

### Where the changes live

- `modules/ds34bt/iop/ds34bt.c`: Bluetooth driver for the OPL menu (DS4 / DualSense, SDP, wireless search and pairing, battery)
- `modules/ds34bt/ee/libds34bt.c`: EE side of the driver (RPC, pad info and battery)
- `modules/pademu/ds34bt.c`: in-game Bluetooth driver
- `modules/*/rtl8761b_fw.h`: Realtek RTL8761B firmware (generated with `tools/gen_rtl_fw.py`)
- `modules/ds34usb/iop/ds34usb.c`: USB pairing
- `include/btkeys.h`: per-pad link keys for wireless pairing
- `include/padsetup.h`: Controller Setup blob (remapping, lightbar colour per slot)
- `src/gui.c`: Bluetooth pads indicator (battery cards)
- `src/guigame.c`, `src/dialogs.c`: `Pad Emulator Settings`, `Bluetooth Pads`, `Controller Setup` and `Controller Test` screens

## Credits

- **Miguel Queiroz** ([@MiguelQueiroz010](https://github.com/MiguelQueiroz010)): maintainer of this fork. DualShock 4 and clone support, Realtek dongle firmware loading, rumble on clones, Controller Test, multi-pad menu, battery indicator, lightbar colours and the Kingdom Hearts II memory fix.
- **[rodrigoGalvanDev](https://github.com/rodrigoGalvanDev/OPL-DualSense-BT)**: the original OPL-DualSense-BT project this fork is based on (DualSense over Bluetooth, SDP server and wireless pairing).
- The [Open PS2 Loader](https://github.com/ps2homebrew/Open-PS2-Loader) team and everyone behind PADEMU. Most of this is their work.
- The Bluetooth driver is based on [Arduino-PSRemote](https://github.com/IonAgorria/Arduino-PSRemote) and the [USB Host Shield 2.0](https://github.com/felis/USB_Host_Shield_2.0) library, same as upstream.
- Realtek firmware: from the [linux-firmware](https://git.kernel.org/pub/scm/linux/kernel/git/firmware/linux-firmware.git) project.

## License

Same as OPL: [Academic Free License v3.0](LICENSE).
