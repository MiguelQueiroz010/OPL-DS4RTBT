#!/usr/bin/env python3
"""
Identifica no PC o dongle Bluetooth USB e o controle (DS4 / clone / DualSense / DS3).
Sem instalar nada alem do Python 3. Roda no Windows, Linux e macOS.

Uso:   python bt_identify.py
Saida: texto na tela + bt_identify_report.txt  (mande o arquivo)

Ligue o dongle e o controle no PC antes (o controle pode estar por cabo USB ou pareado por Bluetooth).
Quanto mais nomes aparecerem (VID:PID e nome), melhor.
"""
import json
import os
import platform
import re
import subprocess
import sys

# Dongles que o fork conhece. O resto aparece como "desconhecido" (nao e prova de que nao funciona).
KNOWN_DONGLES = {
    "0BDA:8771": "Realtek RTL8761B(U/V) - firmware embutido no OPL (carrega sozinho).",
    "0A12:0001": "CSR8510 (classico) - nao precisa de firmware; confira se nao e clone falso.",
}
SONY_CONTROLLERS = {
    "054C:0268": "DualShock 3",
    "054C:05C4": "DualShock 4 v1 (CUH-ZCT1)",
    "054C:09CC": "DualShock 4 v2 (CUH-ZCT2)",
    "054C:0CE6": "DualSense",
    "054C:0DF2": "DualSense Edge",
}


def decode(raw):
    """Saida de programas do Windows nem sempre e UTF-8 (cp850/cp1252): tenta algumas e nunca falha."""
    for enc in ("utf-8", "cp1252", "cp850"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def run(cmd, timeout=25):
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=timeout, shell=isinstance(cmd, str))
        return decode(r.stdout or b"") + decode(r.stderr or b"")
    except Exception as e:  # noqa: BLE001
        return f"(falhou: {e})"


def fmt(vid, pid):
    return f"{vid.upper().zfill(4)}:{pid.upper().zfill(4)}"


# ------------------------------------------------------------------------------------------------ Windows
def windows():
    ps = ("[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Get-PnpDevice -PresentOnly | Select-Object InstanceId,FriendlyName,Class,Manufacturer,Status | "
          "ConvertTo-Json -Compress")
    raw = run(["powershell", "-NoProfile", "-Command", ps], timeout=60)
    try:
        devs = json.loads(raw)
        if isinstance(devs, dict):
            devs = [devs]
    except Exception:  # noqa: BLE001
        return [], [], "Nao consegui listar os dispositivos pelo PowerShell:\n" + raw[:500]
    dongles, pads = [], []
    for d in devs:
        iid = d.get("InstanceId") or ""
        name = d.get("FriendlyName") or ""
        cls = d.get("Class") or ""
        m = re.search(r"USB\\VID_([0-9A-F]{4})&PID_([0-9A-F]{4})", iid, re.I)
        if m and (cls == "Bluetooth" or "bluetooth" in name.lower() or "wireless" in name.lower() and "adapter" in name.lower()):
            dongles.append({"id": fmt(*m.groups()), "name": name, "maker": d.get("Manufacturer"), "instance": iid})
        # controles: USB (VID_054C&PID_xxxx) ou HID por Bluetooth (VID&0002054C_PID&09CC)
        m2 = re.search(r"VID_([0-9A-F]{4})&PID_([0-9A-F]{4})", iid, re.I) if iid.upper().startswith(("HID\\", "USB\\")) else None
        m3 = re.search(r"VID&0002([0-9A-F]{4})_PID&([0-9A-F]{4})", iid, re.I)
        mm = m3 or m2
        if mm and (cls in ("HIDClass", "XboxComposite", "") or "controller" in name.lower() or "game" in name.lower()):
            if "controller" in name.lower() or "game" in name.lower() or mm.group(1).upper() == "054C":
                pads.append({"id": fmt(*mm.groups()), "name": name, "via": "Bluetooth" if m3 else "USB", "instance": iid})
    return dongles, pads, ""


# ------------------------------------------------------------------------------------------------ Linux
def linux():
    dongles, pads, extra = [], [], []
    base = "/sys/bus/usb/devices"
    if os.path.isdir(base):
        for dev in sorted(os.listdir(base)):
            p = os.path.join(base, dev)

            def rd(n, p=p):
                try:
                    return open(os.path.join(p, n)).read().strip()
                except Exception:  # noqa: BLE001
                    return ""
            vid, pid = rd("idVendor"), rd("idProduct")
            if not vid:
                continue
            cls = rd("bDeviceClass")
            is_bt = cls == "e0"
            try:
                for sub in os.listdir(p):
                    if sub.startswith(dev + ":") and open(os.path.join(p, sub, "bInterfaceClass")).read().strip() == "e0":
                        is_bt = True
            except Exception:  # noqa: BLE001
                pass
            if is_bt:
                dongles.append({"id": fmt(vid, pid), "name": rd("product"), "maker": rd("manufacturer"), "instance": dev})
            if vid.lower() == "054c" or "controller" in rd("product").lower():
                pads.append({"id": fmt(vid, pid), "name": rd("product"), "via": "USB", "instance": dev})
    inp = run("cat /proc/bus/input/devices 2>/dev/null")
    for blk in inp.split("\n\n"):
        n = re.search(r'Name="(.*)"', blk)
        i = re.search(r"Bus=(\w+) Vendor=(\w+) Product=(\w+)", blk)
        if n and i and ("controller" in n.group(1).lower() or i.group(2).upper() == "054C"):
            pads.append({"id": fmt(i.group(2), i.group(3)), "name": n.group(1), "via": "Bluetooth" if i.group(1) == "0005" else "USB",
                         "instance": "/proc/bus/input"})
    for tool in ("hciconfig -a", "btmgmt info"):
        out = run(tool + " 2>/dev/null")
        if out.strip() and "falhou" not in out:
            extra.append(f"$ {tool}\n{out.strip()}")
    return dongles, pads, "\n\n".join(extra)


# ------------------------------------------------------------------------------------------------ macOS
def macos():
    dongles, pads = [], []
    out = run("system_profiler SPUSBDataType -json", timeout=60)
    try:
        data = json.loads(out)

        def walk(items):
            for it in items:
                vid = (it.get("vendor_id") or "").replace("0x", "").split(" ")[0]
                pid = (it.get("product_id") or "").replace("0x", "")
                name = it.get("_name", "")
                if vid and pid:
                    if "bluetooth" in name.lower():
                        dongles.append({"id": fmt(vid, pid), "name": name, "maker": it.get("manufacturer"), "instance": ""})
                    if "controller" in name.lower() or vid.upper().endswith("54C"):
                        pads.append({"id": fmt(vid[-4:], pid), "name": name, "via": "USB", "instance": ""})
                walk(it.get("_items", []))
        walk(data.get("SPUSBDataType", []))
    except Exception:  # noqa: BLE001
        pass
    return dongles, pads, run("system_profiler SPBluetoothDataType", timeout=60)[:3000]


def main():
    for stream in (sys.stdout, sys.stderr):  # nomes com acento nao podem derrubar o script no console do Windows
        try:
            stream.reconfigure(errors="replace")
        except Exception:  # noqa: BLE001
            pass
    osn = platform.system()
    if osn == "Windows":
        dongles, pads, extra = windows()
    elif osn == "Darwin":
        dongles, pads, extra = macos()
    else:
        dongles, pads, extra = linux()

    L = [f"Sistema: {platform.platform()}", ""]
    L.append("== DONGLE(S) BLUETOOTH USB ==")
    if not dongles:
        L.append("Nenhum dongle Bluetooth USB encontrado (ligado? driver instalado? no Windows, abra o Gerenciador de Dispositivos).")
    for d in dongles:
        info = KNOWN_DONGLES.get(d["id"].upper())
        L.append(f"- {d['id']}  {d['name']}  [{d.get('maker') or 'fabricante ?'}]")
        if info:
            L.append(f"    Conhecido: {info}")
        elif d["id"].upper().startswith("0BDA:"):
            L.append("    Realtek, mas ESTE modelo nao esta na lista do fork. O firmware embutido no OPL e so do RTL8761B (0BDA:8771); "
                     "outros Realtek precisam de outro arquivo de firmware. Mande esta linha.")
        else:
            L.append("    Desconhecido para o fork (nao prova que nao funciona). Mande esta linha.")
    L.append("")
    L.append("== CONTROLE(S) ==")
    if not pads:
        L.append("Nenhum controle encontrado (ligue por cabo USB ou pareie por Bluetooth antes de rodar).")
    seen = set()
    for p in pads:
        key = (p["id"], p["via"], p["name"])
        if key in seen:
            continue
        seen.add(key)
        known = SONY_CONTROLLERS.get(p["id"].upper())
        L.append(f"- {p['id']}  {p['name']}  (via {p['via']})")
        if known:
            L.append(f"    VID:PID de um controle Sony de verdade: {known}.")
        elif p["id"].upper().startswith("054C:"):
            L.append("    VID da Sony com PID diferente dos conhecidos: pode ser clone ou modelo novo.")
        else:
            L.append("    VID diferente da Sony: provavelmente CLONE (a maioria usa o nome 'Wireless Controller').")
    if extra:
        L += ["", "== INFO EXTRA ==", extra]
    text = "\n".join(L)
    print(text)
    with open("bt_identify_report.txt", "w", encoding="utf-8") as f:
        f.write(text + "\n")
    print("\nSalvei bt_identify_report.txt: mande esse arquivo.")


if __name__ == "__main__":
    sys.exit(main())
