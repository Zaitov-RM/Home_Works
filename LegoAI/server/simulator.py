"""Симулятор «робот в лабиринте» на компьютере (CPython).

Позволяет детям учить робота Q-learning БЕЗ железа — прямо в терминале,
а заодно проверить политику перед прошивкой на ESP32.
Запуск:  python server/simulator.py            (тренировка)
         python server/simulator.py --play     (демо выученной политики)
"""
import json, random, argparse, os

ACTIONS = ("stop", "forward", "backward", "left", "right")
# геометрия: forward/left/right меняют направление; backward - назад
DIRS = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # E, S, W, N — clockwise: +1 = поворот вправо


def make_maze(size=8):
    """Случайный «комнатный» лабиринт: редкие стены-столбы, всегда проходим."""
    m = [[False for _ in range(size)] for _ in range(size)]
    for r in range(size):
        for c in range(size):
            if random.random() < 0.15 and not (r <= 1 and c <= 1) \
               and not (r >= size - 2 and c >= size - 2):
                m[r][c] = True
    goal = (size - 1, size - 1)
    m[goal[0]][goal[1]] = False
    m[0][0] = False
    return m, goal


class MazeEnv:
    def __init__(self, size=8):
        self.size = size
        self.reset()

    def reset(self):
        self.maze, self.goal = make_maze(self.size)
        self.pos = [0, 0]
        self.d = 0
        self.steps = 0
        return self.state()

    def state(self):
        """Вектор 0..1: [стена_впереди, слева, справа, впереди_слева, впереди_справа]."""
        def wall(dr, dc):
            r, c = self.pos[0] + dr, self.pos[1] + dc
            return 1.0 if (r < 0 or c < 0 or r >= self.size or
                           c >= self.size or self.maze[r][c]) else 0.0
        f = DIRS[self.d]
        left = DIRS[(self.d - 1) % 4]     # counter-clockwise от facing
        right = DIRS[(self.d + 1) % 4]
        fl = (f[0] + left[0], f[1] + left[1])   # диагональ вперёд-слева
        fr = (f[0] + right[0], f[1] + right[1]) # диагональ вперёд-справа
        return [wall(*f), wall(*left), wall(*right), wall(*fl), wall(*fr)]

    def step(self, action):
        self.steps += 1
        d = self.d
        if action == 1:
            dr, dc = DIRS[d]
            nr, nc = self.pos[0] + dr, self.pos[1] + dc
            if 0 <= nr < self.size and 0 <= nc < self.size and not self.maze[nr][nc]:
                self.pos = [nr, nc]
            else:
                return self.state(), -10.0, False   # ударился о стену
        elif action == 3:
            self.d = (d - 1) % 4                    # поворот влево
        elif action == 4:
            self.d = (d + 1) % 4                    # поворот вправо
        # action 0/2 не используются политикой (см. n_actions=3)
        if tuple(self.pos) == self.goal:
            return self.state(), 100.0, True
        if self.steps > 200:
            return self.state(), -20.0, True
        return self.state(), -1.0, False


def q_train(episodes=3000, size=8):
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "esp", "behavior"))
    from qlearning import QLearner
    env = MazeEnv(size)
    # 3 действия: 0 -> вперёд, 1 -> влево, 2 -> вправо (отображение ниже)
    MAP = {0: 1, 1: 3, 2: 4}
    q = QLearner(n_actions=3)
    wins = 0
    for ep in range(episodes):
        s = env.reset()
        done = False
        while not done:
            a = q.choose(s)
            s2, r, done = env.step(MAP[a])
            q.update(r, None if done else s2, done)
        wins += tuple(env.pos) == env.goal
        q.epsilon = max(0.05, 0.3 * (1 - ep / episodes))
        if ep % 200 == 0:
            print("ep %4d | win %3d%% | states %d" %
                  (ep, 100 * wins // (ep + 1), len(q.Q)))
    out = os.path.join(os.path.dirname(__file__), "q_maze.json")
    with open(out, "w") as f:
        json.dump({"buckets": q.buckets, "n_actions": 3, "Q": q.Q}, f)
    print("Сохранено:", out, "— скопируйте на ESP32 в /data/q.json")
    return q


def play(q, episodes=5, size=8):
    """Проверка выученной политики без исследования."""
    env = MazeEnv(size)
    MAP = {0: 1, 1: 3, 2: 4}
    wins = 0
    for _ in range(episodes):
        s = env.reset(); done = False; eps = 0
        old_eps = q.epsilon; q.epsilon = 0.0
        while not done and eps < 300:
            a = q.choose(s)
            s, _, done = env.step(MAP[a]); eps += 1
        q.epsilon = old_eps
        wins += tuple(env.pos) == env.goal
    print("play: %d/%d побед" % (wins, episodes))
    return wins


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--play", action="store_true")
    ap.add_argument("--episodes", type=int, default=3000)
    args = ap.parse_args()
    if args.play:
        q = q_train(episodes=args.episodes)
        play(q)
    else:
        q = q_train(episodes=args.episodes)
        play(q)
