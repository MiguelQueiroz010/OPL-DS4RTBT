# Debug Bluetooth remoto (dongle / controle)

Branch `debug-dongle`: o OPL de debug manda para a rede linhas curtas `BT:` / `PADEMU BT:` sobre o dongle e o controle.

## 1. Pegar o ELF de debug
GitHub > Actions > **Debug-BT** > ultimo run > artifact `OPL-BT-INGAMEDEBUG` (um `.ELF`).
Rodando manualmente ("Run workflow") dá para marcar `verbose` e ter também as linhas detalhadas de HCI/L2CAP.

## 2. No PC que fica na mesma rede do PS2 (o do seu amigo, acessado por Radmin)
```
python tools/ps2_monitor.py
```
- Ele escuta os logs (UDP 18194), mostra só o que importa (`--all` mostra tudo) e salva `ps2_session_*.txt`.
- Ao dar `Ctrl+C` ele imprime e salva o **resumo do diagnóstico** (`ps2_session_*_resumo.txt`): **mande esse arquivo**.
- Para o monitor também abrir o ELF no PS2 (precisa do `ps2client` no PATH e do PS2Link rodando no PS2):
  `python tools/ps2_monitor.py --ip IP_DO_PS2 --elf OPL-BT-INGAMEDEBUG-xxxx.ELF`
  Se não tiver PS2Link, abra o ELF como sempre (uLaunchELF/FMCB): o monitor funciona do mesmo jeito.
- Libere a porta no firewall do Windows (rede privada) na primeira vez.

## 3. Roteiro de teste
1. Abra o monitor, depois o OPL de debug, com o dongle ligado desde antes.
2. Em `Configurar PADEMU > Bluetooth Pads` abra **Adapter Information** (foto da tela ajuda).
3. Faça o pareamento / ligue o controle (PS) e tente mexer no menu por ~30 s.
4. `Ctrl+C` no monitor e mande `_resumo.txt` (e o `_full.txt` se pedirem).

## 4. Identificar os aparelhos no PC
Com o dongle e o controle ligados no PC:
```
python tools/bt_identify.py
```
Manda o `bt_identify_report.txt` (VID:PID e nome do dongle e do controle).

## O que as linhas significam
- `BT: dongle VID:PID ... | HCI ver .. | LMP ver .. | manufacturer ..`: o que o chip diz que é. `ver 00` = "Bluetooth 1.0b" = chip sem firmware (ou clone).
- `BT: Realtek adapter, but NOT in RTL8761B ROM state ... firmware NOT loaded`: Realtek de outro modelo, o firmware embutido é só do RTL8761B.
- `BT: adapter ready`: o init terminou. Se não aparecer, a linha `init stage N` mostra onde parou.
- `BT: ev XX ...`: eventos HCI (04 pedido de conexão, 03 conexão completa, 05 desconexão, 07 nome do controle).
- `BT: pad N channels open, pad running` e `HID reports received`: o controle abriu os canais e está mandando dados.
