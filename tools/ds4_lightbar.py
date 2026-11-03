#!/usr/bin/env python3
"""
DS4 / clone lightbar colour tool (Windows, Linux, macOS).

Sets the lightbar colour of DualShock 4 controllers (and clones) connected by Bluetooth or USB.
It builds the same output report the OPL Bluetooth driver uses (report 0x11 + CRC32 over Bluetooth,
report 0x05 over USB), so a clone that works in OPL works here.

    pip install hidapi pyusb libusb-package     (the last two only for controllers using a libusb driver)
    python ds4_lightbar.py                  graphical interface (needs tkinter, included with Python on Windows)
    python ds4_lightbar.py --list           list the controllers found
    python ds4_lightbar.py --set 255 0 128  set every controller to this colour and exit
    ... --mode "BT 0x11 (no CRC)"           force one report format (Auto tries them all)
    python ds4_lightbar.py --set 0 0 255 --keep   ... and keep re-sending it (Ctrl+C to stop)

DS4Windows (and Steam) open the controller exclusively and keep the lightbar to themselves. Close them, or
add python to the HidHide whitelist, otherwise this tool cannot open the controller.
"""
import json
import os
import sys
import time
import zlib

try:
    import hid
except ImportError:
    sys.exit("hidapi is missing. Install it with:  pip install hidapi")

try:  # optional: controllers bound to a libusb/WinUSB driver (DS4Windows' "Wireless Controller" driver) are not HID devices
    import usb.core
    import usb.util
    try:
        import libusb_package
        _backend = None
        try:
            import usb.backend.libusb1 as _lb
            _backend = _lb.get_backend(find_library=libusb_package.find_library)
        except Exception:  # noqa: BLE001
            _backend = None
    except ImportError:
        _backend = None
except ImportError:
    usb = None
    _backend = None

SONY = 0x054C
KNOWN_PIDS = {0x05C4, 0x09CC, 0x0BA0}  # DS4 v1, DS4 v2, USB wireless adapter
BUS_USB, BUS_BT = 1, 2  # hidapi bus_type values
CFG = os.path.join(os.path.expanduser("~"), ".ds4_lightbar.json")

PRESETS = {
    "Red": (255, 0, 0), "Green": (0, 255, 0), "Blue": (0, 0, 255), "Yellow": (255, 200, 0),
    "Cyan": (0, 255, 255), "Magenta": (255, 0, 255), "White": (255, 255, 255), "Orange": (255, 90, 0),
    "Violet": (140, 0, 255), "Off": (0, 0, 0),
}


def report_bt(r, g, b, small=0, big=0, crc=True):
    """Bluetooth output report 0x11, 78 bytes: same layout as modules/pademu/ds34bt.c (hid_LEDRumbleCommand)."""
    buf = bytearray(78)
    buf[0] = 0x11
    buf[1] = 0xC4 if crc else 0x84  # HID report (+ CRC32 present), 4 ms poll interval
    buf[3] = 0xFF  # every valid flag: some clones only apply the colour when all are set
    buf[6], buf[7] = small, big
    buf[8], buf[9], buf[10] = r, g, b
    if crc:
        c = zlib.crc32(b"\xA2" + bytes(buf[:74])) & 0xFFFFFFFF
        buf[74:78] = c.to_bytes(4, "little")
    return bytes(buf)


def report_usb(r, g, b, small=0, big=0):
    """USB output report 0x05, 32 bytes."""
    buf = bytearray(32)
    buf[0] = 0x05
    buf[1] = 0xFF
    buf[4], buf[5] = small, big
    buf[6], buf[7], buf[8] = r, g, b
    return bytes(buf)


def find_pads():
    """Every HID gamepad that looks like a DS4: Sony IDs, or a gamepad (usage page 1, usage 5) with a DS4-like name."""
    pads, seen = [], set()
    for d in hid.enumerate():
        path = d["path"]
        if path in seen:
            continue
        name = (d.get("product_string") or "")
        is_pad = d.get("usage_page") == 1 and d.get("usage") == 5
        sony = d["vendor_id"] == SONY and d["product_id"] in KNOWN_PIDS
        if sony or (is_pad and ("wireless controller" in name.lower() or "ds4" in name.lower())):
            seen.add(path)
            pads.append(d)
    if usb is not None:  # USB devices without a HID driver
        try:
            for u in usb.core.find(find_all=True, backend=_backend) or []:
                try:
                    name = usb.util.get_string(u, u.iProduct) if u.iProduct else ""
                except Exception:  # noqa: BLE001
                    name = ""
                if (u.idVendor == SONY and u.idProduct in KNOWN_PIDS) or "wireless controller" in (name or "").lower():
                    pads.append({"path": "usb:%d:%d" % (u.bus, u.address), "vendor_id": u.idVendor,
                                 "product_id": u.idProduct, "product_string": name or "Wireless Controller",
                                 "bus_type": BUS_USB, "libusb": u})
        except Exception:  # noqa: BLE001
            pass
    return pads


def bus_of(d):
    bus = d.get("bus_type")
    if bus in (BUS_USB, BUS_BT):
        return bus
    p = str(d["path"]).lower()  # older hidapi: guess from the Windows device path
    return BUS_BT if ("bthenum" in p or "00001124" in p or "&0005" in p) else BUS_USB


def label(d):
    kind = "Bluetooth" if bus_of(d) == BUS_BT else ("USB (libusb)" if d.get("libusb") else "USB")
    return "%s  [%s]  %04X:%04X" % (d.get("product_string") or "Controller", kind, d["vendor_id"], d["product_id"])


def send_libusb(u, rgb):
    """USB output report 0x05 on the interrupt OUT endpoint, for a controller using a libusb driver."""
    try:
        try:
            u.set_configuration()
        except Exception:  # noqa: BLE001
            pass
        usb.util.claim_interface(u, 0)
        try:
            n = u.write(0x03, report_usb(*rgb)[0:32], timeout=1000)
            return "libusb 0x05: ok (%d bytes)" % n
        finally:
            usb.util.release_interface(u, 0)
    except Exception as e:  # noqa: BLE001
        return "libusb error: %s" % e


MODES = ["Auto", "BT 0x11 (CRC)", "BT 0x11 (no CRC)", "USB 0x05"]


def variants(d, rgb, mode):
    bt = bus_of(d) == BUS_BT
    table = {
        "BT 0x11 (CRC)": lambda: report_bt(*rgb),
        "BT 0x11 (no CRC)": lambda: report_bt(*rgb, crc=False),
        "USB 0x05": lambda: report_usb(*rgb),
    }
    if mode != "Auto":
        return [(mode, table[mode])]
    order = ["BT 0x11 (CRC)", "BT 0x11 (no CRC)", "USB 0x05"] if bt else ["USB 0x05", "BT 0x11 (CRC)"]
    return [(n, table[n]) for n in order]


def send(d, rgb, mode="Auto"):
    """Sends the colour. Returns a short text with the result of every report tried ('' is never returned)."""
    if d.get("libusb") is not None:
        return send_libusb(d["libusb"], rgb)
    try:
        dev = hid.device()
        dev.open_path(d["path"])
    except Exception as e:  # noqa: BLE001
        return "cannot open (is DS4Windows / Steam running?): %s" % e
    out = []
    try:
        try:  # a Bluetooth DS4 only switches to its full mode after the calibration feature report is read
            dev.get_feature_report(0x02, 64)
        except Exception:  # noqa: BLE001
            pass
        for name, mk in variants(d, rgb, mode):
            try:
                n = dev.write(mk())
                out.append("%s: %s" % (name, "ok (%d bytes)" % n if n >= 0 else "FAILED " + str(dev.error())))
            except Exception as e:  # noqa: BLE001
                out.append("%s: error %s" % (name, e))
            time.sleep(0.05)
        return " | ".join(out)
    finally:
        dev.close()


def load_cfg():
    try:
        with open(CFG, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:  # noqa: BLE001
        return {}


def save_cfg(cfg):
    try:
        with open(CFG, "w", encoding="utf-8") as f:
            json.dump(cfg, f)
    except OSError:
        pass


def cli(argv):
    if "--list" in argv:
        pads = find_pads()
        for i, d in enumerate(pads):
            print(i, label(d))
        if not pads:
            print("No controller found.")
        return 0
    i = argv.index("--set")
    rgb = tuple(max(0, min(255, int(x))) for x in argv[i + 1:i + 4])
    if len(rgb) != 3:
        sys.exit("usage: --set R G B")
    mode = argv[argv.index("--mode") + 1] if "--mode" in argv else "Auto"
    while True:
        pads = find_pads()
        if not pads:
            print("No controller found.")
        for d in pads:
            print(label(d), "->", send(d, rgb, mode))
        if "--keep" not in argv:
            return 0
        time.sleep(2)


def gui():
    import tkinter as tk
    from tkinter import colorchooser, ttk

    cfg = load_cfg()
    root = tk.Tk()
    root.title("DS4 Lightbar")
    root.geometry("520x430")

    pads = []
    colours = {}  # path -> (r, g, b)
    status = tk.StringVar(value="")

    lst = tk.Listbox(root, height=5, exportselection=False)
    lst.pack(fill="x", padx=10, pady=(10, 4))

    modevar = tk.StringVar(value=cfg.get("mode", "Auto"))
    mrow = tk.Frame(root)
    mrow.pack(fill="x", padx=10)
    tk.Label(mrow, text="Report:").pack(side="left")
    ttk.Combobox(mrow, textvariable=modevar, values=MODES, state="readonly", width=18).pack(side="left", padx=6)

    swatch = tk.Label(root, text="  ", bg="#8c00ff", height=2)
    swatch.pack(fill="x", padx=10, pady=4)

    def key(d):
        return "%04X:%04X:%s" % (d["vendor_id"], d["product_id"], d["path"])

    def selected():
        s = lst.curselection()
        return pads[s[0]] if s else None

    def show(rgb):
        swatch.config(bg="#%02x%02x%02x" % rgb)
        for n, v in zip("RGB", rgb):
            sliders[n].set(v)

    def apply(rgb, d=None):
        d = d or selected()
        if not d:
            status.set("Select a controller first.")
            return
        colours[key(d)] = rgb
        cfg[label(d)] = list(rgb)
        cfg["mode"] = modevar.get()
        save_cfg(cfg)
        status.set("%s\n%s" % (label(d), send(d, rgb, modevar.get())))
        show(rgb)

    def refresh():
        nonlocal pads
        pads = find_pads()
        lst.delete(0, "end")
        for d in pads:
            lst.insert("end", label(d))
        if pads:
            lst.selection_set(0)
            saved = cfg.get(label(pads[0]))
            if saved:
                show(tuple(saved))
        status.set("%d controller(s) found." % len(pads) if pads else "No controller found. Connect one and press Refresh.")

    def on_slider(_=None):
        rgb = tuple(int(sliders[n].get()) for n in "RGB")
        swatch.config(bg="#%02x%02x%02x" % rgb)
        if live.get():
            apply(rgb)

    sliders = {}
    for n in "RGB":
        s = tk.Scale(root, from_=0, to=255, orient="horizontal", label=n, command=on_slider)
        s.pack(fill="x", padx=10)
        sliders[n] = s

    live = tk.BooleanVar(value=True)
    ttk.Checkbutton(root, text="Apply while moving the sliders", variable=live).pack(anchor="w", padx=10)

    row = tk.Frame(root)
    row.pack(fill="x", padx=10, pady=4)
    for name, rgb in PRESETS.items():
        tk.Button(row, text=name, command=lambda c=rgb: apply(c), bg="#%02x%02x%02x" % rgb,
                  fg="white" if sum(rgb) < 380 else "black", width=6).pack(side="left", padx=1)

    def pick():
        c = colorchooser.askcolor(color=swatch.cget("bg"))[0]
        if c:
            apply(tuple(int(x) for x in c))

    btns = tk.Frame(root)
    btns.pack(fill="x", padx=10, pady=4)
    ttk.Button(btns, text="Pick colour...", command=pick).pack(side="left")
    ttk.Button(btns, text="Apply", command=lambda: apply(tuple(int(sliders[n].get()) for n in "RGB"))).pack(side="left", padx=6)
    ttk.Button(btns, text="Refresh", command=refresh).pack(side="left")

    tk.Label(root, textvariable=status, anchor="w", wraplength=500, justify="left").pack(fill="x", padx=10, pady=4)

    def keepalive():  # re-send the chosen colours: some pads fall back to their default colour after a while
        for d in pads:
            rgb = colours.get(key(d))
            if rgb:
                send(d, rgb, modevar.get())
        root.after(3000, keepalive)

    lst.bind("<<ListboxSelect>>", lambda _e: (lambda d: d and cfg.get(label(d)) and show(tuple(cfg[label(d)])))(selected()))
    refresh()
    root.after(3000, keepalive)
    root.mainloop()


if __name__ == "__main__":
    if "--set" in sys.argv or "--list" in sys.argv:
        sys.exit(cli(sys.argv))
    gui()
