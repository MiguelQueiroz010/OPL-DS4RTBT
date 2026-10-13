## OPL com Bluetooth (DS4 clone / DualSense) via dongle USB

Fork do Open PS2 Loader com suporte a controles sem fio Bluetooth no PADEMU, usando um dongle Bluetooth USB no PS2.

### Novidades
- Suporte a **DualShock 4 original e clones ("Wireless Controller")** e **DualSense** pelo PADEMU, no menu e dentro do jogo.
- **Dongles Realtek RTL8761B(U)**: o firmware é carregado automaticamente ao iniciar (menu e jogo).
- **Pareamento sem fio** pela tela PADEMU > Wireless Pairing (busca, lista de dispositivos, chaves guardadas na configuração).
- **Vibração no jogo** funcionando em DS4/clones (relatório de saída com CRC32, handshake do relatório 0x05, buffers L2CAP sem corrida).
- Motor grande da vibração com faixa ampliada (96–255), porque os clones quase não respondem a valores baixos.
- **Controller Test** no menu: teste de LED, vibração e botões.

### Como usar
1. Copie `OPL-DualSense-BT-*.ELF` para o PS2 e execute.
2. Espete o dongle Bluetooth numa porta USB do PS2.
3. Em **Configurações > PADEMU**, escolha o modo **DS3/DS4/DS5 BT** e use **Wireless Pairing > Search** com o controle em modo de pareamento (PS + Share).
4. Ative o PADEMU no jogo e jogue.

### Limitações conhecidas
- A cor do LED de alguns clones ainda não muda (em investigação).
- Sem teste em todos os modelos de dongle: relate o VID/PID do seu em uma issue.

### Créditos
Baseado no Open PS2 Loader e no PADEMU. Dongle Realtek: firmware do projeto linux-firmware.
