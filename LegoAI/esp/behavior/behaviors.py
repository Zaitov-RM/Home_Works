"""Конструктор поведений: правила, конечный автомат (FSM), политика на нейросети.

Каждое поведение — объект с методом step(state) -> action_idx, и опц.
полем reward_fn для обучения. Действия робота нумеруются:
0 = стоп, 1 = вперёд, 2 = назад, 3 = влево, 4 = вправо.
"""


class RuleBehavior:
    """Набор правил «если датчик X < a → действие Y» (для уроков 1-2)."""

    def __init__(self, rules=None, default=1):
        # rules: список (sensor_idx, '<'/'>', порог, action)
        self.rules = rules or []
        self.default = default

    def add_rule(self, sensor_idx, cmp, threshold, action):
        self.rules.append((sensor_idx, cmp, threshold, action))

    def step(self, state):
        for idx, cmp, thr, act in self.rules:
            v = state[idx] if idx < len(state) else 0.0
            if cmp == "<" and v < thr: return act
            if cmp == ">" and v > thr: return act
        return self.default


class FSMBehavior:
    """Простой конечный автомат: состояния + переходы с условиями."""

    def __init__(self, states, initial):
        # states: {name: {"action": int,
        #                 "transitions": [(sensor_idx, '<'/'==', val, next_state)]}}
        self.states = states
        self.state = initial

    def step(self, s):
        cfg = self.states[self.state]
        for idx, cmp, val, nxt in cfg.get("transitions", []):
            v = s[idx] if idx < len(s) else 0.0
            if cmp == "<" and v < val: self.state = nxt; break
            if cmp == ">" and v > val: self.state = nxt; break
            if cmp == "==" and abs(v - val) < 1e-6: self.state = nxt; break
        return cfg["action"]


class NNPolicyBehavior:
    """Политика на нейросети (ml/network.py). Режимы: exploit/explore/teach."""

    ACTIONS = ("stop", "forward", "backward", "left", "right")

    def __init__(self, net, explore=0.15):
        self.net = net
        self.explore = explore
        self.last = None   # (state, action) для обучения демонстрацией

    def step(self, state):
        a, probs = self.net.act(state, explore=self.explore)
        self.last = (state[:], a)
        return a

    def imitate(self, human_action):
        """Обучение демонстрацией: ребёнок рулит, сеть запоминает."""
        if self.last:
            s, _ = self.last
            self.net.train(s, target_idx=human_action)

    def save(self, path="/data/policy.json"):
        import json, os
        try:
            os.mkdir("/data")
        except OSError:
            pass
        with open(path, "w") as f:
            json.dump(self.net.to_dict(), f)

    def load(self, path="/data/policy.json"):
        import json, sys, os
        # ml/ может не быть в sys.path на ESP32 — добавляем рядом лежащий
        try:
            from network import Network
        except ImportError:
            sys.path.append(os.path.dirname(os.path.dirname(__file__)) + "/ml")
            from network import Network
        try:
            with open(path) as f:
                self.net = Network.from_dict(json.load(f))
            return True
        except (OSError, ValueError, KeyError):
            return False
