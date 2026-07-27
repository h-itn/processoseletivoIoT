import time
import sys
from machine import Pin, SoftI2C

# 1. Print IMEDIATO para o CI registrar antes de qualquer processamento
print("Sistema de Monitoramento Inicializado")
sys.stdout.flush() # Empurra a mensagem para o console à força

# 2. Configurações de Pinos e Constantes
PIN_BTN = 4
PIN_SDA = 21
PIN_SCL = 22
MPU6050_ADDR = 0x68

LIMITE_TEMPO_X = 4000
LIMITE_VARIACAO_Y = 2.5

# 3. I2C via Software (Prevenção absoluta contra travamentos do Wokwi)
try:
    i2c = SoftI2C(scl=Pin(PIN_SCL), sda=Pin(PIN_SDA), freq=100000, timeout=50000)
    i2c.writeto_mem(MPU6050_ADDR, 0x6B, b'\x00') # Acorda o sensor
except Exception:
    pass

def ler_temperatura():
    try:
        data = i2c.readfrom_mem(MPU6050_ADDR, 0x41, 2)
        raw_temp = (data[0] << 8) | data[1]
        if raw_temp & 0x8000:
            raw_temp -= 65536
        return (raw_temp / 340.0) + 36.53
    except Exception:
        return None

# 4. Inicialização
btn_porta = Pin(PIN_BTN, Pin.IN, Pin.PULL_DOWN)

# Tenta ler a temperatura inicial com segurança
temp_referencia = 24.0
for _ in range(5):
    t = ler_temperatura()
    if t is not None:
        temp_referencia = t
        break
    time.sleep_ms(50)

tempo_abertura_inicio = None
alerta_porta_ativo = False
alerta_termico_ativo = False
esteve_em_alerta = False

# 5. Loop Principal (Sem classes complexas para otimizar memória)
while True:
    try:
        tempo_atual = time.ticks_ms()
        estado_porta = btn_porta.value()
        
        # Leitura de temperatura à prova de falhas
        temp_lida = ler_temperatura()
        temp_atual = temp_lida if temp_lida is not None else temp_referencia

        # Atualiza referência apenas num ambiente seguro que está esfriando
        if not alerta_termico_ativo and not esteve_em_alerta and temp_atual < temp_referencia:
            temp_referencia = temp_atual

        # --- Lógica de Porta Aberta ---
        if estado_porta == 0: # 0 = Aberto
            if tempo_abertura_inicio is None:
                tempo_abertura_inicio = tempo_atual
            
            # Checa o estouro do cronômetro
            elif not alerta_porta_ativo and time.ticks_diff(tempo_atual, tempo_abertura_inicio) >= LIMITE_TEMPO_X:
                print("ALERTA: Porta aberta por muito tempo!")
                sys.stdout.flush()
                alerta_porta_ativo = True
                esteve_em_alerta = True
        else:
            tempo_abertura_inicio = None
            alerta_porta_ativo = False

        # --- Lógica de Alarme Térmico ---
        delta_t = temp_atual - temp_referencia
        if delta_t >= LIMITE_VARIACAO_Y:
            if not alerta_termico_ativo:
                print("ALERTA: Degradacao termica detectada!")
                sys.stdout.flush()
                alerta_termico_ativo = True
                esteve_em_alerta = True
        else:
            alerta_termico_ativo = False

        # --- Lógica de Normalização ---
        if esteve_em_alerta and estado_porta == 1 and delta_t < LIMITE_VARIACAO_Y:
            print("Status: Sistema Normalizado.")
            sys.stdout.flush()
            esteve_em_alerta = False
            alerta_porta_ativo = False
            alerta_termico_ativo = False
            temp_referencia = temp_atual

    except Exception:
        pass

    # Delay de 50ms (dá respiro ao processador do Wokwi)
    time.sleep_ms(50)