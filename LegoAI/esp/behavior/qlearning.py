"""Q-learning прямо на ESP32: таблица Q сохраняется во flash.

Состояние квантуется из вектора датчиков (0..1), действия целочисленные.
Награда — от кнопки «похвала/ошибка» ребёнка или от правила среды.
"""
import json


class QLearner:
    def __init__(self, n_states_dim=4, n_actions=3, buckets=4,
                 alpha=0.3, gamma=0.9, epsilon=0.3):
        self.Q = {}                       # "s0,s1,..." -> [q,...]
        self.buckets = buckets
        self.n_actions = n_actions
        self.alpha, self.gamma = alpha, gamma
        self.epsilon = epsilon
        self.last = None                  # (state_key, action)

    def _key(self, state):
        return ",".join(str(min(self.buckets - 1, int(v * self.buckets)))
                        for v in state)

    def _row(self, key):
        if key not in self.Q:
            self.Q[key] = [0.0] * self.n_actions
        return self.Q[key]

    def choose(self, state):
        import math
        try:
            from urandom import random as rnd
        except ImportError:
            from random import random as rnd
        key = self._key(state)
        row = self._row(key)
        if rnd() < self.epsilon:
            a = int(rnd() * self.n_actions)
        else:
            a = row.index(max(row))
        self.last = (key, a)
        return a

    def update(self, reward, next_state=None, done=False):
        if self.last is None:
            return
        key, a = self.last
        row = self._row(key)
        if done or next_state is None:
            target = reward
        else:
            nrow = self._row(self._key(next_state))
            target = reward + self.gamma * max(nrow)
        row[a] += self.alpha * (target - row[a])
        self.last = None if done else self.last
        if done:
            self.last = None

    # --- сохранение во flash ---
    def save(self, path="/data/q.json"):
        with open(path, "w") as f:
            json.dump({"buckets": self.buckets,
                       "n_actions": self.n_actions,
                       "Q": self.Q}, f)

    def load(self, path="/data/q.json"):
        try:
            with open(path) as f:
                d = json.load(f)
            self.Q = d["Q"]
            self.buckets = d.get("buckets", self.buckets)
            self.n_actions = d.get("n_actions", self.n_actions)
            return True
        except (OSError, ValueError):
            return False

    def stats(self):
        return {"states": len(self.Q),
                "best": {k: max(v) for k, v in list(self.Q.items())[:5]}}
