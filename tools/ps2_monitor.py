#!/usr/bin/env python3
"""
Monitor remoto do OPL (build de debug) com diagnostico automatico do dongle / controle Bluetooth.

O que faz
  1. Escuta os logs que o OPL de debug manda pela rede (UDP, porta 18194).
  2. Mostra so as linhas que interessam (BT / PADEMU / padman). Use --all para ver tudo.
  3. Salva tudo em ps2_session_<data>_full.txt (completo) e ps2_session_<data>.txt (filtrado).
  4. Ao sair (Ctrl+C) ou com --summary, imprime e salva um RESUMO DO DIAGNOSTICO (ps2_session_<data>_resumo.txt)
     para mandar de volta: dongle, versoes, firmware Realtek, conexao do controle, relatorios HID.
  5. Opcional: abre o OPL de debug no PS2 pela rede (--ip e --elf), usando o ps2client (PS2Link).

Uso
  python ps2_monitor.py                            # so escuta e diagnostica
  python ps2_monitor.py --ip 192.168.0.50 --elf OPNPS2LD.ELF   # tambem manda o ELF para o PS2
  python ps2_monitor.py --summary ps2_session_xxx_full.txt     # diagnostico de um log ja salvo

Para o PS2 aceitar o ELF pela rede, ele precisa estar com o PS2Link rodando (uLaunchELF > PS2Link, ou o proprio
OPL de debug ja aberto). Se nao der, abra o ELF de debug do jeito de sempre: o monitor funciona do mesmo jeito.

Nada aparece? PC e PS2 na mesma rede (mesmo roteador) e libere a porta no firewall do Windows (rede privada).
"""
import argparse
import os
import re
import shutil
import socket
import subprocess
import sys
import threading
import time

PORT = 18194
INTERESTING = re.compile(r"(^|\s)(BT:|PADEMU|DS34|RTL|padman|ds34bt|bt_pademu)", re.I)


# ----------------------------------------------------------------------------------------------- diagnostico
def diagnose(lines):
    """Le as linhas do log e devolve um texto com o que da pra concluir."""
    out = []
    add = out.append

    def grab(rx, group=None, last=True):
        found = [m for m in (re.search(rx, l) for l in lines) if m]
        if not found:
            return None
        m = found[-1] if last else found[0]
        return m.group(group) if group is not None else m

    add("===== DIAGNOSTICO =====")

    usb = grab(r"USB dongle attached(?: )?:? ?([0-9A-F]{4}:[0-9A-F]{4}) rev ([0-9A-F]{4}), class ([0-9A-F/]+)")
    if usb:
        add(f"Dongle USB: {usb.group(1)} (rev {usb.group(2)}, classe {usb.group(3)})")
    else:
        add("Dongle USB: NAO apareceu nenhuma linha 'USB dongle attached' -> o PS2 nao enxergou o dongle como Bluetooth "
            "(porta, cabo/hub, dongle sem energia) ou o log da fase de menu nao chegou.")

    ver = grab(r"BT: dongle ([0-9A-F]{4}):([0-9A-F]{4}) rev ([0-9A-F]{4}) \| HCI ver ([0-9A-F]{2}) rev ([0-9A-F]{4}) \| "
               r"LMP ver ([0-9A-F]{2}) sub ([0-9A-F]{4}) \| manufacturer ([0-9A-F]{4})")
    if ver:
        vid, pid, rev, hv, hr, lv, ls, mf = ver.groups()
        add(f"Versoes lidas do chip: HCI ver {hv} rev {hr} | LMP ver {lv} sub {ls} | fabricante {mf}")
        if mf.upper() == "005D":
            add("  Fabricante 005D = Realtek.")
        if hv == "00" and lv == "00":
            add("  ATENCAO: HCI/LMP ver 00 = 'Bluetooth 1.0b'. Isso nao e um chip Bluetooth 4/5 funcionando normalmente: "
                "e o jeito de um chip Realtek que ainda NAO recebeu firmware (ou de um clone/falsificado).")
    else:
        add("Versoes do chip: nao li (o init do adaptador nao chegou na leitura de versao).")

    if grab(r"Realtek adapter, but NOT in RTL8761B ROM state"):
        m = grab(r"lmp sub ([0-9A-F]{4}), hci rev ([0-9A-F]{4})")
        add("Firmware Realtek: NAO foi carregado. O dongle e Realtek, mas nao esta no estado do RTL8761B "
            f"(esperado lmp sub 8761 / hci rev 000B; este reporta {m.group(1)} / {m.group(2)}). "
            "O firmware embutido no OPL e so do RTL8761B: este chip precisa de outro arquivo de firmware.")
    elif grab(r"Realtek RTL8761B in ROM state"):
        if grab(r"firmware downloaded"):
            add("Firmware Realtek: carregado com sucesso.")
        elif grab(r"firmware load FAILED"):
            add("Firmware Realtek: FALHOU no download (veja a linha 'fragment ... refused').")
        else:
            add("Firmware Realtek: comecou a carregar, mas o log nao mostra o fim (travou no meio?).")
    elif grab(r"is not Realtek"):
        add("Firmware: dongle nao Realtek (sem etapa de firmware). Fabricante/modelo precisam ser identificados.")

    bad = [l for l in lines if "init command" in l and "failed" in l]
    if bad:
        add(f"Init do adaptador: {len(bad)} comando(s) falharam e o adaptador foi resetado. Ultima: {bad[-1].strip()}")

    stage = grab(r"BT: init stage (\d)")
    if grab(r"BT: adapter ready"):
        add("Adaptador: PRONTO (init completo, scan de pareamento ligado).")
    elif stage is not None:
        add(f"Adaptador: NAO ficou pronto. Parou no estagio {stage} de 7 "
            "(1 reset, 2 bdaddr, 3 versao, 4 features, 5 mascara de eventos, 6 SSP, 7 scan).")
    else:
        add("Adaptador: nenhum estagio de init logado.")

    feat = grab(r"BT: features (.*)\| SSP (\d) LE (\d) RSSI-inquiry (\d)")
    if feat:
        add(f"Features: SSP={feat.group(2)} LE={feat.group(3)} inquiry-RSSI={feat.group(4)}  (bytes: {feat.group(1).strip()})")
        if feat.group(2) == "0":
            add("  O adaptador NAO anuncia Simple Pairing (SSP): pareamento sem fio de controles modernos pode falhar.")

    req = [l for l in lines if re.search(r"BT: ev 04 ", l)]
    cc = [l for l in lines if re.search(r"BT: ev 03 ", l)]
    dis = [l for l in lines if re.search(r"BT: ev 05 ", l)]
    add(f"Eventos de ligacao: {len(req)} pedido(s) de conexao, {len(cc)} conexao(oes) completa(s), {len(dis)} desconexao(oes).")
    for l in cc[-3:]:
        m = re.search(r"ev 03 len \d+: ([0-9A-F]{2})", l)
        if m and m.group(1) != "00":
            add(f"  Conexao com erro, status {m.group(1)}: {l.strip()}")
    for l in dis[-3:]:
        m = re.search(r"ev 05 len \d+: ([0-9A-F]{2}) .. .. ([0-9A-F]{2})", l)
        if m:
            add(f"  Desconexao, status {m.group(1)} motivo {m.group(2)}")

    names = [re.search(r'remote name "(.*)"', l).group(1) for l in lines if "remote name" in l]
    if names:
        add("Nome(s) do controle: " + ", ".join(sorted(set(names))))

    running = [l for l in lines if "channels open, pad running" in l]
    reports = [l for l in lines if "HID reports received" in l]
    add(f"Controle: {len(running)} vez(es) com canais L2CAP abertos / pad 'running'; {len(reports)} linha(s) de relatorios HID.")
    if reports:
        add("  Ultimo: " + reports[-1].strip())
    if req and not running:
        add("  O controle PEDIU conexao mas os canais L2CAP nunca abriram -> problema no enlace (autenticacao/chave/L2CAP), "
            "nao nos botoes. Veja as linhas 'BT: ev' e 'L2CAP signalling' em volta.")
    if running and not reports:
        add("  Canais abertos mas ZERO relatorios HID: o controle conectou e nao manda dados (modo de relatorio do clone, "
            "ou o radio nao entrega o pacote). Esse e o sintoma 'conecta mas nao mexe no menu'.")
    if running and reports:
        add("  O controle manda relatorios. Se o menu nao responde, o problema esta depois do driver (mapeamento/clone).")

    pad = [l for l in lines if "PADEMU" in l and ("->" in l or "args" in l or "pad driver" in l)]
    if pad:
        add("PADEMU (ultimas linhas): ")
        for l in pad[-4:]:
            add("  " + l.strip())

    dma = [l for l in lines if "DMA Busy" in l]
    if dma:
        add(f"padman: {len(dma)} aviso(s) 'DMA Busy' (resposta de pad fora de hora).")
    return "\n".join(out)


# ----------------------------------------------------------------------------------------------- execucao
def read_summary_file(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = [re.sub(r"^\[\s*[\d.]+\]\s*", "", l.rstrip("\n")) for l in f]
    print(diagnose(lines))


def launch_elf(ip, elf):
    exe = shutil.which("ps2client") or shutil.which("ps2client.exe")
    if not exe:
        print("[monitor] ps2client nao encontrado no PATH: abra o ELF de debug pelo uLaunchELF/FMCB como de costume.")
        return
    if not os.path.isfile(elf):
        print(f"[monitor] ELF nao encontrado: {elf}")
        return
    print(f"[monitor] mandando {elf} para {ip} (o PS2 precisa estar com o PS2Link rodando)...")
    try:
        subprocess.run([exe, "-h", ip, "reset"], timeout=20)
        time.sleep(4)
        subprocess.Popen([exe, "-h", ip, "execee", "host:" + os.path.abspath(elf)])
    except Exception as e:  # noqa: BLE001
        print(f"[monitor] nao consegui chamar o ps2client: {e}")


def main():
    ap = argparse.ArgumentParser(description="Monitor do OPL de debug + diagnostico Bluetooth")
    ap.add_argument("--port", type=int, default=PORT)
    ap.add_argument("--all", action="store_true", help="mostra todas as linhas (padrao: so BT/PADEMU/padman)")
    ap.add_argument("--ip", help="IP do PS2 (para --elf)")
    ap.add_argument("--elf", help="ELF de debug para abrir no PS2 via ps2client")
    ap.add_argument("--summary", metavar="ARQUIVO", help="so gera o diagnostico de um log ja salvo")
    ap.add_argument("--outdir", default=".")
    args = ap.parse_args()

    if args.summary:
        read_summary_file(args.summary)
        return

    stamp = time.strftime("%Y%m%d_%H%M%S")
    base = os.path.join(args.outdir, f"ps2_session_{stamp}")
    full = open(base + "_full.txt", "w", encoding="utf-8")
    filt = open(base + ".txt", "w", encoding="utf-8")
    lines = []

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", args.port))
    print(f"[monitor] ouvindo logs do PS2 na UDP {args.port}. Salvando em {base}*.txt  (Ctrl+C para sair e ver o diagnostico)")
    if args.ip and args.elf:
        threading.Thread(target=launch_elf, args=(args.ip, args.elf), daemon=True).start()

    t0 = time.time()
    buf = ""
    try:
        while True:
            data, _addr = sock.recvfrom(4096)
            buf += data.decode("latin-1", errors="replace")
            while "\n" in buf:
                line, buf = buf.split("\n", 1)
                line = line.rstrip("\r\n")
                stamped = f"[{time.time() - t0:8.3f}] {line}"
                full.write(stamped + "\n")
                full.flush()
                lines.append(line)
                if args.all or INTERESTING.search(line):
                    print(stamped)
                    filt.write(stamped + "\n")
                    filt.flush()
    except KeyboardInterrupt:
        pass
    finally:
        text = diagnose(lines)
        print("\n" + text)
        with open(base + "_resumo.txt", "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(f"\n[monitor] arquivos: {base}_resumo.txt (mande este), {base}.txt, {base}_full.txt")


if __name__ == "__main__":
    sys.exit(main())
