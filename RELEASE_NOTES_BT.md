## OPL com Bluetooth (DS4 clone / DualSense) via dongle USB

Fork do Open PS2 Loader com suporte a controles sem fio Bluetooth no PADEMU, usando um dongle Bluetooth USB no PS2.

### Novidades
- Suporte a **DualShock 4 original e clones ("Wireless Controller")** e **DualSense** pelo PADEMU, no menu e dentro do jogo.
- **Dongles Realtek RTL8761B(U)**: o firmware é carregado automaticamente ao iniciar (menu e jogo).
- **Pareamento sem fio** pela tela PADEMU > Wireless Pairing (busca, lista de dispositivos, chaves guardadas na configuração).
- **Vibração no jogo** funcionando em DS4/clones (relatório de saída com CRC32, handshake do relatório 0x05, buffers L2CAP sem corrida).
- Motor grande da vibração com faixa ampliada (96–255), porque os clones quase não respondem a valores baixos.
- **Controller Test** no menu: teste de LED, vibração e botões.

### Correção: Kingdom Hearts II (SLPM-66675) com PADEMU + SMB
Com o PADEMU ligado e a ISO no SMB, o KH2 não iniciava o som: o jogo pede 233.432 bytes **contínuos** da RAM da IOP para o buffer de efeitos sonoros e a alocação falhava (`SE(fffffffc)`). O PADEMU, o USBD e a pilha de rede deixavam o total livre e o maior bloco contínuo abaixo disso. O que mudou:
- **Pilha de rede in-game (SMSTCPIP) sem remontagem/fragmentação IP.** Os buffers estáticos de remontagem (5,8 KB) e fragmentação (1,5 KB) ficavam residentes sem serem usados (TCP sobre MTU 1500 não fragmenta).
- **Pool do USBD menor** para o PADEMU (endpoints 10, TDs 12, isoTDs 2, requisições 8), já que só um dongle Bluetooth é usado.
- **Builds de debug** passam a usar o mesmo lwIP enxuto do release (com UDP para o log), para o log refletir a memória real. Antes eles usavam o lwIP completo, e por isso os ajustes de memória nunca apareciam nos testes.
- Mantidos `CDVDMAN_FS_SECTORS = 8` e a janela TCP de 10240 / 8 buffers: reduzi esses valores numa tentativa e o SMB caiu de ~9 ms para ~318 ms por leitura de 16 KB (~50 KB/s), e leituras de 3 setores travavam o FMV.
- Resultado medido no build de debug: o KH2 passa a alocar o buffer de efeitos (`SE(038fd8/038fd8:100%)`) com ~30 KB de sobra, e o SMB volta a ~8 ms por leitura.

### Como usar
1. Copie `OPL-DualSense-BT-*.ELF` para o PS2 e execute.
2. Espete o dongle Bluetooth numa porta USB do PS2.
3. Em **Configurações > PADEMU**, escolha o modo **DS3/DS4/DS5 BT** e use **Wireless Pairing > Search** com o controle em modo de pareamento (PS + Share).
4. Ative o PADEMU no jogo e jogue.

### Limitações conhecidas
- **Este é um release candidato:** a correção do KH2 foi validada num build de debug. Houve uma trava aos ~22 s do primeiro FMV nesse build de debug, ainda sob investigação (suspeita: log por UDP em alta taxa); o build de release ainda não foi testado nesse ponto.
- O KH2 em SMB com PADEMU tem pouca folga de memória. Rodar a ISO por USB ou HDD libera a pilha de rede inteira da IOP.
- A cor do LED de alguns clones ainda não muda (em investigação).
- Sem teste em todos os modelos de dongle: relate o VID/PID do seu em uma issue.

### Créditos
Baseado no Open PS2 Loader e no PADEMU. Dongle Realtek: firmware do projeto linux-firmware.
