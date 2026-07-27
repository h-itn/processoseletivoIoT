import time
from machine import Pin, I2C

PIN_BTN = 4
PIN_SDA = 21
PIN_SCL = 22
MPU6050_ADDR = 0x68

LIMITE_TEMPO_X = 5000
LIMITE_VARIACAO_Y = 3.0

class MPU6050:
    def __init__(self, i2c, addr=MPU6050_ADDR):
        self.i2c = i2c
        self.addr = addr
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
            return 20.0

btn_porta = Pin(PIN_BTN, Pin.IN, Pin.PULL_DOWN)
i2c = I2C(0, scl=Pin(PIN_SCL), sda=Pin(PIN_SDA), freq=400000)
mpu = MPU6050(i2c)

print("Sistema de Monitoramento Inicializado")

temp_referencia = mpu.read_temperature()
tempo_abertura_inicio = None

alerta_porta_ativo = False
alerta_termico_ativo = False

while True:
    tempo_atual = time.ticks_ms()
    estado_porta = btn_porta.value()
    temp_atual = mpu.read_temperature()

    if estado_porta == 0:
        if tempo_abertura_inicio is None:
            tempo_abertura_inicio = tempo_atual

        if not alerta_porta_ativo and time.ticks_diff(tempo_atual, tempo_abertura_inicio) >= LIMITE_TEMPO_X:
            print("ALERTA: Porta aberta por muito tempo!")
            alerta_porta_ativo = True
    else:
        tempo_abertura_inicio = None
        alerta_porta_ativo = False
        if not alerta_termico_ativo:
            temp_referencia = temp_atual

    delta_t = temp_atual - temp_referencia

    if delta_t >= LIMITE_VARIACAO_Y:
        if not alerta_termico_ativo:
            print("ALERTA: Degradacao termica detectada!")
            alerta_termico_ativo = True
    else:
        alerta_termico_ativo = False

    if (alerta_porta_ativo or alerta_termico_ativo) and (estado_porta == 1 and delta_t < LIMITE_VARIACAO_Y):
        print("Status: Sistema Normalizado.")
        alerta_porta_ativo = False
        alerta_termico_ativo = False

    time.sleep_ms(10)
    