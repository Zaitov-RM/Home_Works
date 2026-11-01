"""Драйверы моторов для LEGO-совместимых драйверов (DRV8833 / L298N / LEGO PF).

Безопасность для детей: PWM ограничен MAX_DUTY (70%).
MicroPython-совместимый код (machine.PWM).
"""
from machine import Pin, PWM

MAX_DUTY = 70  # процентов; физический предел скорости


class Motor:
    """Один DC-мотор на двух пинах IN1/IN2 драйвера."""

    def __init__(self, in1_pin, in2_pin, freq=20000):
        self.in1 = PWM(Pin(in1_pin))
        self.in2 = PWM(Pin(in2_pin))
        for p in (self.in1, self.in2):
            p.freq(freq)
            p.duty(0)

    def _set(self, duty_pct):
        duty_pct = max(-MAX_DUTY, min(MAX_DUTY, duty_pct))
        d = int(abs(duty_pct) * 1023 / 100)
        if duty_pct > 0:
            self.in1.duty(d); self.in2.duty(0)
        elif duty_pct < 0:
            self.in1.duty(0); self.in2.duty(d)
        else:
            self.brake()

    def run(self, speed):     # -100..100
        self._set(speed)

    def stop(self):           # свободный выбег
        self.in1.duty(0); self.in2.duty(0)

    def brake(self):          # активное торможение
        self.in1.duty(1023); self.in2.duty(1023)


class DifferentialDrive:
    """Двухмоторная «тележка» (танковый привод)."""

    def __init__(self, left: Motor, right: Motor):
        self.left, self.right = left, right

    def drive(self, linear, turn):
        """linear, turn в диапазоне -100..100."""
        self.left.run(max(-100, min(100, linear + turn)))
        self.right.run(max(-100, min(100, linear - turn)))

    def forward(self, s=50):  self.drive(s, 0)
    def backward(self, s=50): self.drive(-s, 0)
    def turn_left(self, s=40):  self.drive(0, s)
    def turn_right(self, s=40): self.drive(0, -s)
    def stop(self):
        self.left.brake(); self.right.brake()


class Servo:
    """Сервопривод (LEGO/WG9000), угол 0..180, ограничение скорости.»"""

    def __init__(self, pin, freq=50, min_us=500, max_us=2500):
        self.pwm = PWM(Pin(pin))
        self.pwm.freq(freq)
        self.min_us, self.max_us = min_us, max_us
        self.angle = 90

    def set_angle(self, angle):
        angle = max(0, min(180, angle))
        us = self.min_us + (self.max_us - self.min_us) * angle // 180
        self.pwm.duty(int(us * 4095 / 20000))  # duty при freq=50 -> период 20ms
        self.angle = angle

    def detach(self):
        self.pwm.duty(0)
