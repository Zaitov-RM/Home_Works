"""LegoAI OS — ядро: конечный автомат циклов робота + диспетчер поведений.

Состояния ОС: IDLE -> RUN(behavior) -> TEACH(imitation/RL) -> SAVE.
main.py создаёт RobotOS и вызывает os.loop_period_ms().
"""
import json, time, os, sys

sys.path.append("/usr/lib/micropython")
for p in ("drivers", "behavior", "ml", "storage"):
    if os.path.isdir("/" + p):
        sys.path.append("/" + p)

ACTIONS = ("stop", "forward", "backward", "left", "right")


class DatasetRecorder:
    """Собирает (state -> action) при обучении демонстрацией."""

    PATH = "/data/ds.json"

    def __init__(self):
        self.rows = []

    def add(self, state, action):
        self.rows.append({"s": state, "a": action})
        if len(self.rows) % 20 == 0:
            self.save()

    def save(self):
        _mkdir("/data")
        with open(self.PATH, "w") as f:
            json.dump(self.rows, f)

    def load(self):
        try:
            with open(self.PATH) as f:
                self.rows = json.load(f)
            return True
        except (OSError, ValueError):
            return False

    def clear(self):
        self.rows = []
        try:
            os.remove(self.PATH)
        except OSError:
            pass


def _mkdir(p):
    try:
        os.mkdir(p)
    except OSError:
        pass


class RobotOS:
    def __init__(self, suite, drive, praise=None, error_btn=None):
        self.suite = suite          # drivers.sensors.SensorSuite
        self.drive = drive          # drivers.motors.DifferentialDrive
        self.praise = praise
        self.error_btn = error_btn
        self.behavior = None        # объект с step(state)->action
        self.mode = "idle"          # idle | run | teach_rl | teach_imitate
        self.recorder = DatasetRecorder()
        self.q = None               # QLearner в режиме teach_rl
        self.period_ms = 150
        self.log = []
        self.human_action = None    # ставится веб-интерфейсом в teach_imitate

    # ---------- API из веба ----------
    def set_behavior(self, b):
        self.behavior = b
        self.mode = "run"

    def start_rl(self, qlearner):
        self.q = qlearner
        self.mode = "teach_rl"

    def start_teaching(self):
        self.mode = "teach_imitate"

    def stop(self):
        self.mode = "idle"
        self.drive.stop()

    # ---------- главный цикл ----------
    def apply_action(self, a):
        if a == 0: self.drive.stop()
        elif a == 1: self.drive.forward(50)
        elif a == 2: self.drive.backward(40)
        elif a == 3: self.drive.turn_left(45)
        elif a == 4: self.drive.turn_right(45)

    def loop_once(self):
        state = self.suite.state()
        if self.mode == "idle" or not state:
            return

        if self.mode == "run":
            self.apply_action(self.behavior.step(state))

        elif self.mode == "teach_imitate":
            # робот едет «как его ведут» кнопками ребёнка из веба
            if self.human_action is not None:
                self.apply_action(self.human_action)
                if hasattr(self.behavior, "imitate"):
                    self.behavior.imitate(self.human_action)
                self.recorder.add(state, self.human_action)
                self.human_action = None

        elif self.mode == "teach_rl":
            a = self.q.choose(state)
            self.apply_action(a)
            reward = 0.0
            done = False
            if self.praise and self.praise.pressed():
                reward, done = 10.0, True
            if self.error_btn and self.error_btn.pressed():
                reward, done = -10.0, True
            nxt = self.suite.state()
            self.q.update(reward, nxt if not done else None, done)

        self._log(state)

    def _log(self, state):
        self.log.append((time.ticks_ms(), state))
        if len(self.log) > 50:
            self.log.pop(0)

    def telemetry(self):
        st = self.suite.state()
        return {"mode": self.mode, "state": st,
                "actions": ACTIONS,
                "dataset": len(self.recorder.rows),
                "q_states": len(self.q.Q) if self.q else 0}
