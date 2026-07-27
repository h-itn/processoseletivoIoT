# Relatório do Desafio Técnico – Sistema de Monitoramento de Temperatura e Abertura de Porta

## Identificação do Candidato

- **Nome completo:** Hailton Gabriel de Souza Conceição
- **GitHub:** https://github.com/

---

## Visão Geral da Solução

O projeto consiste em um sistema embarcado desenvolvido para controle de qualidade e auditoria em ambientes refrigerados, estufas e painéis elétricos. A solução monitora em tempo real duas condições críticas de risco: o tempo contínuo de abertura de uma porta ou tampa e variações térmicas abruptas baseadas no gradiente de temperatura ($\Delta T$). 

O sistema emite alertas via comunicação Serial assim que qualquer uma das anomalias é identificada e registra a normalização das condições operacionais quando o ambiente é restaurado aos parâmetros de segurança.

---

## Arquitetura do Sistema Embarcado

A solução foi desenvolvida em MicroPython com uma arquitetura orientada ao loop de execução contínuo e não-bloqueante, estruturada da seguinte forma:

- **Inicialização:** Configuração do pino do sensor de porta, inicialização do barramento I2C para comunicação com o sensor MPU6050 e emissão do log de inicialização na comunicação Serial.
- **Leitura Contínua e Temporização:** No laço principal, o estado do sensor de porta e a temperatura atual são verificados constantemente. A medição do tempo de abertura é feita calculando a diferença de tempo através do método `time.ticks_diff()`, evitando o congelamento da execução por atrasos bloqueantes (`time.sleep`).
- **Máquina de Estados de Alarme:** 
  - Caso a porta permaneça aberta por tempo igual ou superior a 5000ms, o estado de alerta de porta é acionado.
  - Caso o gradiente de temperatura ($\Delta T = T_{atual} - T_{referencia}$) atinja ou ultrapasse $3.0^\circ\text{C}$, o estado de alerta térmico é ativado.
- **Normalização:** Quando a porta é fechada e a variação térmica retorna ao limite aceitável, o sistema redefini seus parâmetros, imprime a mensagem de normalização e estabelece a nova temperatura de referência.

---

## Componentes Utilizados na Simulação

- **Microcontrolador ESP32 DevKit C v4 (`board-esp32-devkit-c-v4`):** Unidade central de processamento e controle do firmware.
- **IMU MPU6050 (`imu1`):** Sensor conectado via I2C aos pinos GPIO 21 (SDA) e GPIO 22 (SCL), responsável pela leitura e cálculo da temperatura ambiente.
- **Pushbutton (`btn1`):** Botão conectado ao pino GPIO 4 configurado com Pull-Down interno, atuando como chave fim de curso para simular a abertura (nível lógico 0) e fechamento (nível lógico 1) da porta.

---

## Decisões Técnicas Relevantes

- **Uso de Funções Não-Bloqueantes:** A utilização de `time.ticks_ms()` e `time.ticks_diff()` garante alta responsividade do firmware, permitindo que a automação de testes do Wokwi CI leia com precisão os eventos sem perda de janelas de tempo.
- **Encapsulamento do Driver I2C:** A comunicação com o MPU6050 foi isolada em uma classe dedicada para tratar erros de leitura e conversão de dados do registrador, garantindo maior legibilidade do código-fonte e robustez contra falhas de comunicação.
- **Controle de Borda e Flags de Estado:** As mensagens de alerta são disparadas apenas nas transições de estado através de variáveis booleanas de controle (`alerta_porta_ativo` e `alerta_termico_ativo`), evitando poluição no terminal Serial e garantindo a correspondência exata de strings esperada no pipeline de testes automatizados.
- **Uso de Constantes Descritivas:** Todos os pinos, limites de temporização e gradientes de temperatura foram definidos via constantes em caixa alta, eliminando o uso de números mágicos espalhados pelo código.

---

## Resultados Obtidos

- Execução completa e correta das simulações no Wokwi.
- Disparo do alarme de tempo de exposição da porta após a contagem contínua de 5000ms.
- Detecção imediata de elevação térmica abrupta no MPU6050 ao atingir o delta de $3.0^\circ\text{C}$.
- Restauração automática para o estado normalizado assim que as condições de contorno retornam ao padrão seguro.
- Passagem bem-sucedida nos testes de validação do pipeline automatizado (GitHub Actions).

---

## Comentários Adicionais

- **Aprendizados:** O projeto permitiu consolidar práticas avançadas de programação não-bloqueante para sistemas embarcados em MicroPython, bem como a estruturação de fluxos de validação de hardware via Integração Contínua (CI) com Wokwi CLI.
- **Melhorias Futuras:** Em um cenário de produção física, a solução poderia incluir um atuador sonoro (Buzzer) e integração via protocolo MQTT para envio de dados de telemetria a um painel de monitoramento em nuvem.