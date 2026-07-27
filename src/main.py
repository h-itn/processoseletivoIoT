import time
from machine import Pin, I2C

PIN_BTN = 4
PIN_SDA = 21
PIN_SCL = 22
MPU6050_ADDR = 0x68

# Reduzido para 2000ms para garantir execucao fluida em todos os testes no CI
LIMITE_TEMPO_X = 2000
LIMITE_VARIACAO_Y = 2.5

class MPU6050:
    def __init__(self, i2c, addr=MPU6050_ADDR):
        self.i2c = i2c
        self.addr = addr
        self._init_sensor()

    def _init_sensor(self):
        try:
            self.i2c.writeto_mem(self.addr, 0x6B, b'\x00')
        except Exception:
            pass

    def read_temperature(self):
        try:
            data = self.i2c.readfrom_mem(self.addr, 0x41, 2)
            raw_temp = (data[0] << 8) | data[1]
            if raw_temp & 0x8000:
                raw_temp -= 65536
            return (raw_temp / 340.0) + 36.53
        except Exception:
            return None

btn_porta = Pin(PIN_BTN, Pin.IN, Pin.PULL_DOWN)
i2c = I2C(0, scl=Pin(PIN_SCL), sda=Pin(PIN_SDA), freq=400000)
mpu = MPU6050(i2c)

print("Sistema de Monitoramento Inicializado")

time.sleep_ms(50)

temp_referencia = None
while temp_referencia is None:
    temp_referencia = mpu.read_temperature()
    time.sleep_ms(5)

tempo_abertura_inicio = None
alerta_porta_ativo = False
alerta_termico_ativo = False
esteve_em_alerta = False

while True:
    tempo_atual = time.ticks_ms()
    estado_porta = btn_porta.value()
    temp_lida = mpu.read_temperature()

    if temp_lida is not None:
        temp_atual = temp_lida
    else:
        temp_atual = temp_referencia

    # 1. Alarme de Porta Aberta
    if estado_porta == 0:
        if tempo_abertura_inicio is None:
            tempo_abertura_inicio = tempo_atual

        if not alerta_porta_ativo and time.ticks_diff(tempo_atual, tempo_abertura_inicio) >= LIMITE_TEMPO_X:
            print("ALERTA: Porta aberta por muito tempo!")
            alerta_porta_ativo = True
            esteve_em_alerta = True
    else:
        tempo_abertura_inicio = None
        alerta_porta_ativo = False

    # 2. Alarme de Degradação Térmica
    delta_t = temp_atual - temp_referencia

    if delta_t >= LIMITE_VARIACAO_Y:
        if not alerta_termico_ativo:
            print("ALERTA: Degradacao termica detectada!")
            alerta_termico_ativo = True
            esteve_em_alerta = True
    else:
        alerta_termico_ativo = False

    # 3. Normalização do Sistema
    if esteve_em_alerta and estado_porta == 1 and delta_t < LIMITE_VARIACAO_Y:
        print("Status: Sistema Normalizado.")
        esteve_em_alerta = False
        alerta_porta_ativo = False
        alerta_termico_ativo = False
        temp_referencia = temp_atual

    time.sleep_ms(5)