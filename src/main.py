import time
import sys
from machine import Pin, I2C

# 1. Atraso Crítico: Segura a execução por 1 segundo inteiro para o CI plugar o monitor serial
time.sleep(1)
print("Sistema de Monitoramento Inicializado")
sys.stdout.flush()

# 2. Configurações
PIN_BTN = 4
PIN_SDA = 21
PIN_SCL = 22
MPU6050_ADDR = 0x68

LIMITE_TEMPO_X = 4000
LIMITE_VARIACAO_Y = 2.5

# 3. I2C via Hardware (Mais rápido e não trava no simulador)
i2c = I2C(0, scl=Pin(PIN_SCL), sda=Pin(PIN_SDA), freq=100000)

try:
    i2c.writeto_mem(MPU6050_ADDR, 0x6B, b'\x00')
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

btn_porta = Pin(PIN_BTN, Pin.IN, Pin.PULL_DOWN)

# 4. Calibração Inicial
temp_referencia = None
for _ in range(10):
    t = ler_temperatura()
    if t is not None:
        temp_referencia = t
        break
    time.sleep_ms(20)

if temp_referencia is None:
    temp_referencia = 24.0

tempo_abertura_inicio = None
alerta_porta_ativo = False
alerta_termico_ativo = False
esteve_em_alerta = False

# 5. Loop Principal
while True:
    try:
        tempo_atual = time.ticks_ms()
        estado_porta = btn_porta.value()
        
        temp_lida = ler_temperatura()
        if temp_lida is not None:
            temp_atual = temp_lida
            if not alerta_termico_ativo and not esteve_em_alerta and temp_atual < temp_referencia:
                temp_referencia = temp_atual
        else:
            temp_atual = temp_referencia

        # --- Porta ---
        if estado_porta == 0: 
            if tempo_abertura_inicio is None:
                tempo_abertura_inicio = tempo_atual
            elif not alerta_porta_ativo and time.ticks_diff(tempo_atual, tempo_abertura_inicio) >= LIMITE_TEMPO_X:
                print("ALERTA: Porta aberta por muito tempo!")
                sys.stdout.flush()
                alerta_porta_ativo = True
                esteve_em_alerta = True
        else:
            tempo_abertura_inicio = None
            alerta_porta_ativo = False

        # --- Térmico ---
        delta_t = temp_atual - temp_referencia
        if delta_t >= LIMITE_VARIACAO_Y:
            if not alerta_termico_ativo:
                print("ALERTA: Degradacao termica detectada!")
                sys.stdout.flush()
                alerta_termico_ativo = True
                esteve_em_alerta = True
        else:
            alerta_termico_ativo = False

        # --- Normalização ---
        if esteve_em_alerta and estado_porta == 1 and delta_t < LIMITE_VARIACAO_Y:
            print("Status: Sistema Normalizado.")
            sys.stdout.flush()
            esteve_em_alerta = False
            alerta_porta_ativo = False
            alerta_termico_ativo = False
            temp_referencia = temp_atual

    except Exception:
        pass

    time.sleep_ms(20)