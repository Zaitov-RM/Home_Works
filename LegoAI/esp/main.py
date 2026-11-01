"""Точка входа LegoAI OS на ESP32.

Копируется на плату как /main.py (или boot.py -> import main).
Настройки железа — в CONFIG ниже; правьте под свой конструктор.
"""
import sys, os, time

BASE = os.path.dirname(os.path.abspath(__file__)) \
    if hasattr(os.path, "abspath") else "/"
for p in ("drivers", "behavior", "ml", "storage", "web"):
    d = BASE.rstrip("/") + "/" + p
    if os.path.isdir(d):
        sys.path.append(d)

from motors import Motor, DifferentialDrive, Servo          # noqa: E402
from sensors import (Ultrasonic, LineSensor, ObstacleSide,  # noqa: E402
                     PraiseButton, SensorSuite)             # noqa: E402
from os_core import RobotOS                                  # noqa: E402
from behaviors import RuleBehavior, NNPolicyBehavior         # noqa: E402
from server import WebServer                                 # noqa: E402

# ---------------------- КОНФИГУРАЦИЯ ЖЕЛЕЗА ----------------------
CONFIG = {
    "wifi_ssid": None,            # None = режим точки доступа LegoAI-XXXX
    "wifi_pass": "legoai4kids",
    "left_motor": (25, 26),       # DRV8833 IN1, IN2
    "right_motor": (27, 14),      # внимание: если включите servo, освободите пин
    "servo": None,                # например 13
    "ultrasonic": (4, 5),         # trig, echo
    "line_pins": [34, 35, 36],    # TCRT5000 x3 (ADC, только input-пины)
    "obstacle_left": 18,
    "obstacle_right": 19,
    "praise_btn": 35,
    "error_btn": 39,
}


def build_robot(cfg):
    lm = Motor(*cfg["left_motor"])
    rm = Motor(*cfg["right_motor"])
    drive = DifferentialDrive(lm, rm)
    line = LineSensor(cfg["line_pins"]) if len(cfg["line_pins"]) >= 2 else None
    suite = SensorSuite(
        ultrasonic=Ultrasonic(*cfg["ultrasonic"]) if cfg["ultrasonic"] else None,
        line=line,
        left=ObstacleSide(cfg["obstacle_left"]) if cfg.get("obstacle_left") is not None else None,
        right=ObstacleSide(cfg["obstacle_right"]) if cfg.get("obstacle_right") is not None else None,
    )
    praise = PraiseButton(cfg["praise_btn"]) if cfg.get("praise_btn") is not None else None
    err = PraiseButton(cfg["error_btn"]) if cfg.get("error_btn") is not None else None
    return RobotOS(suite, drive, praise=praise, error_btn=err)


def default_reflex(robot):
    """Урок 1: рефлекс избегания столкновений (датчик 0 = ультразвук)."""
    rb = RuleBehavior(default=1)
    rb.add_rule(0, ">", 0.85, 2)   # вплотную -> назад
    rb.add_rule(0, ">", 0.6, 4)    # близко -> вправо (объезд)
    if len(CONFIG["line_pins"]) >= 2:
        # индекс 1 = центр линии; при съезде рулим к центру
        rb.add_rule(1, "<", 0.3, 3)
    robot.set_behavior(rb)
    return rb


def main():
    robot = build_robot(CONFIG)
    web = WebServer(robot, ssid=CONFIG["wifi_ssid"], password=CONFIG["wifi_pass"])
    web.wifi_start()
    web.start(port=80)

    # попробуем восстановить выученную политику, иначе — рефлекс урока 1
    pol = NNPolicyBehavior.__new__(NNPolicyBehavior)
    pol.explore = 0.1
    pol.last = None
    if pol.load("/data/policy.json"):
        robot.set_behavior(pol)
        print("LegoAI: загружена нейросеть-политика")
    else:
        default_reflex(robot)
        print("LegoAI: включён базовый рефлекс (Урок 1)")

    tick = time.ticks_ms
    while True:
        t0 = tick()
        web.poll()
        robot.loop_once()
        dt = time.ticks_diff(tick(), t0)
        time.sleep_ms(max(5, robot.period_ms - dt))


if __name__ == "__main__":
    main()
