"""Датчики: HC-SR04 (дальность), TCRT5000 (линия), датчик препятствия, кнопка-«похвала».

Все значения нормализуются в 0..1 — так их удобно подавать в нейросеть.
"""
from machine import Pin, ADC, time_pulse_us


class Ultrasonic:
    """HC-SR04: расстояние в см, нормированное к RANGE."""

    RANGE_CM = 200.0

    def __init__(self, trig, echo):
        self.trig = Pin(trig, Pin.OUT)
        self.echo = Pin(echo, Pin.IN)
        self.trig.value(0)

    def distance_cm(self):
        self.trig.value(1)
        self.trig.value(0)
        us = time_pulse_us(self.echo, 1, 30000)
        if us < 0:
            return self.RANGE_CM  # таймаут = «очень далеко»
        return us / 58.0

    def read_norm(self):
        """1.0 = объект вплотную, 0.0 = пусто впереди."""
        d = self.distance_cm()
        return max(0.0, min(1.0, 1.0 - d / self.RANGE_CM))


class LineSensor:
    """N датчиков линии (TCRT5000) на ADC. Возвращает вектор 0..1."""

    def __init__(self, pins):
        self.adcs = [ADC(Pin(p)) for p in pins]

    def read_norm(self):
        out = []
        for a in self.adcs:
            v = a.read_u16() / 65535.0
            out.append(round(v, 3))
        return out


class ObstacleSide:
    """Цифровой ИК-датчик препятствия слева/справа (1 = есть стена)."""

    def __init__(self, pin):
        self.pin = Pin(pin, Pin.IN)

    def read_norm(self):
        return 1.0 if self.pin.value() == 0 else 0.0


class PraiseButton:
    """Кнопка, которой ребёнок «хвалит» робота при обучении с подкреплением."""

    def __init__(self, pin):
        self.pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        self._last = 1

    def pressed(self):
        v = self.pin.value()
        edge = (self._last == 1 and v == 0)
        self._last = v
        return edge


class SensorSuite:
    """Собирает все подключённые датчики в единый вектор состояния."""

    def __init__(self, ultrasonic=None, line=None, left=None, right=None):
        self.ultrasonic = ultrasonic
        self.line = line
        self.left = left
        self.right = right

    def state(self):
        s = []
        if self.ultrasonic: s.append(round(self.ultrasonic.read_norm(), 3))
        if self.line:       s += self.line.read_norm()
        if self.left:       s.append(self.left.read_norm())
        if self.right:      s.append(self.right.read_norm())
        return s

    @property
    def n(self):
        return len(self.state())
