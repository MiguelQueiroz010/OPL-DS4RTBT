# OPL-DS4RTBT

[English](README.md) | **Português (Brasil)**

Fork do [Open PS2 Loader](https://github.com/ps2homebrew/Open-PS2-Loader) com **suporte a controles Bluetooth** no PADEMU. Jogue no PS2 sem fio com **DualShock 4 (original ou clone), DualSense ou DS3** usando um dongle Bluetooth USB.

## Recursos

- Controles sem fio no menu do OPL e dentro do jogo: botões, analógicos, vibração e lightbar.
- Pareamento sem fio pelo menu: `Bluetooth Pads → Search`, escolha o controle e pronto. Sem cabo, sem PC.
- Até 4 controles Bluetooth ao mesmo tempo, todos navegam no menu. Indicador de bateria por controle.
- Dongles Realtek (RTL8761B/BU): firmware carregado automaticamente.
- `Controller Setup`: cor da lightbar por slot e remapeamento de botões.
- Vibração que funciona em clones de DS4 e tela `Controller Test`.
- Emulação de multitap (experimental, ainda não validada em hardware).

## Início rápido

1. Baixe o `.ELF` em [Releases](../../releases) e execute como qualquer OPL. Você precisa de um **dongle Bluetooth USB** ligado ao PS2.
2. `Start → Controller Settings → Configure PADEMU` (ou por jogo: selecione, aperte `Triangle`). Coloque `Pad Emulator` em **On**, `Pad Emulator Mode` em **DS3/DS4/DS5 BT**, ative `Emulation` na porta e use `Save Changes`.
3. Pareie uma vez: `Bluetooth Pads → Search` e coloque o controle em modo de pareamento (**PS + Share** no DS4, **PS + Create** no DualSense). O DS3 não tem modo de pareamento, pareie por cabo USB (`Pair`).
4. Abra o jogo e aperte **PS** no controle quando a tela do jogo aparecer (abrir um jogo reinicia o USB, então o controle reconecta).

<img src="docs/img/pademu-settings.jpg" alt="Pad Emulator Settings" width="480"> <img src="docs/img/wireless-pairing.jpg" alt="Wireless Pairing" width="480">

## Compatibilidade

- **Testado:** PS2 Slim SCPH-90001, dongle Realtek `0BDA:8771`, DualSense (pareamento sem fio e USB, menu e jogo).
- **Deve funcionar:** qualquer PS2 que rode OPL, DualShock 4 (original e clones "Wireless Controller"), DualSense, DS3, Realtek RTL8761B/BU e a maioria dos dongles Bluetooth 2.1+ que não precisam de firmware do sistema.
- **Provavelmente não:** dongles que precisam de outro firmware, dongles só BLE, alguns clones de DS4 (só pareiam por PIN antigo).
- **Limites:** controles 3 e 4 só controlam o menu do OPL; Kingdom Hearts II via SMB com PADEMU tem pouca memória IOP (ISO em USB/HDD libera).

Conte como foi no seu setup em uma [issue](../../issues) (modelo do PS2, dongle, controle, o que funcionou). Logs ajudam muito: rode `python tools/ps2_log.py` no PC e use um build debug.

## Compilando

Com o [ps2dev](https://github.com/ps2dev/ps2dev) configurado (`PS2DEV` e `PS2SDK` exportados):

```sh
make download_lng
make                          # release
make DEBUG=1 INGAME_DEBUG=1   # debug com logs pela rede
```

Depois de mudar headers compartilhados (como `ee_core/include/coreconfig.h`), faça `make clean` e apague `ee_core/obj` uma vez. Documentação original: [README-OPL.md](README-OPL.md).

## Créditos

- **Miguel Queiroz** ([@MiguelQueiroz010](https://github.com/MiguelQueiroz010)): mantenedor deste fork.
- **Rodrigo Galvan** ([rodrigoGalvanDev](https://github.com/rodrigoGalvanDev/OPL-DualSense-BT)): projeto original OPL-DualSense-BT (DualSense por Bluetooth, SDP, pareamento sem fio).
- A equipe do [Open PS2 Loader](https://github.com/ps2homebrew/Open-PS2-Loader) e todos por trás do PADEMU.
- Driver Bluetooth baseado em [Arduino-PSRemote](https://github.com/IonAgorria/Arduino-PSRemote) e [USB Host Shield 2.0](https://github.com/felis/USB_Host_Shield_2.0). Firmware Realtek do [linux-firmware](https://git.kernel.org/pub/scm/linux/kernel/git/firmware/linux-firmware.git).

Licença: [Academic Free License v3.0](LICENSE).
