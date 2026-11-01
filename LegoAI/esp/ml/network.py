"""Крошечный фреймворк нейросетей для ESP32 (чистый Python, без numpy).

Поддерживает MLP: dense -> tanh -> ... -> dense. Inference + обучение
(backprop) прямо на плате — достаточно для политики робота 4-8-3.
Формат весов совместим с server/train_and_export.py.
"""
import math

try:
    import urandom  # MicroPython (ESP32)
except ImportError:
    import random as urandom  # CPython — для тестов и сервера


def _rand_float():
    return urandom.random()


def _rand_int(n):
    return urandom.randrange(n)


def make_weights(n_in, n_out):
    scale = math.sqrt(2.0 / n_in)
    return [[(_rand_float() * 2 - 1) * scale for _ in range(n_out)]
            for _ in range(n_in)]


class Dense:
    def __init__(self, w, b):
        self.w = w              # [n_in][n_out]
        self.b = b              # [n_out]
        self.n_in = len(w)
        self.n_out = len(b)
        self.in_acts = None
        self.pre = None         # до активации
        self.grad_w = None
        self.grad_b = None

    def forward(self, x):
        assert len(x) == self.n_in
        self.in_acts = x
        out = [self.b[j] for j in range(self.n_out)]
        for i, ai in enumerate(x):
            wi = self.w[i]
            for j in range(self.n_out):
                out[j] += ai * wi[j]
        self.pre = out
        return out[:]           # копия — наружу не отдаём внутренний список


def tanh(z):
    return math.tanh(z)


def d_tanh(out):
    return 1.0 - out * out


class Network:
    """Сеть из Dense-слоёв; скрытые слои — tanh, выход — softmax или linear."""

    def __init__(self, sizes, out_mode="softmax", lr=0.05):
        self.layers = []
        for a, b in zip(sizes, sizes[1:]):
            self.layers.append(Dense(make_weights(a, b), [0.0] * b))
        self.out_mode = out_mode
        self.lr = lr

    # ---------- inference ----------
    def forward(self, x):
        h = x
        for idx, layer in enumerate(self.layers):
            z = layer.forward(h)
            last = idx == len(self.layers) - 1
            if last and self.out_mode == "softmax":
                m = max(z)
                e = [math.exp(v - m) for v in z]
                s = sum(e)
                h = [vi / s for vi in e]
            elif last:
                h = z
            else:
                h = [tanh(v) for v in z]
        return h

    def act(self, x, explore=0.0):
        """Выбор действия (argmax вероятностей, eps-greedy)."""
        probs = self.forward(x)
        if explore > 0.0 and _rand_float() < explore:
            return _rand_int(len(probs)), probs
        best, bi = probs[0], 0
        for i, p in enumerate(probs):
            if p > best:
                best, bi = p, i
        return bi, probs

    # ---------- обучение ----------
    def train(self, x, target_idx=None, target_vec=None):
        """Один шаг backprop. target_idx — класс (cross-entropy),
        target_vec — регрессия (MSE)."""
        out = self.forward(x)
        L = len(self.layers)
        # дельта выходного слоя
        delta = out[:]
        if target_idx is not None:
            for j in range(len(delta)):
                delta[j] -= 1.0 if j == target_idx else 0.0
        else:
            for j in range(len(delta)):
                delta[j] -= target_vec[j]
        # градиенты и обратный ход
        for li in range(L - 1, -1, -1):
            layer = self.layers[li]
            n = layer.n_out
            g_w = [[0.0] * n for _ in range(layer.n_in)]
            g_b = delta[:]
            for i, ai in enumerate(layer.in_acts):
                row = g_w[i]
                for j in range(n):
                    row[j] = ai * delta[j]
            # обновляем веса (lr делится на n_in — стабильность при large lr)
            scale = self.lr / layer.n_in
            for i in range(layer.n_in):
                wi = layer.w[i]; gi = g_w[i]
                for j in range(n):
                    wi[j] -= scale * gi[j]
            for j in range(n):
                layer.b[j] -= self.lr * g_b[j]
            if li > 0:
                prev = self.layers[li - 1]
                new_delta = [0.0] * prev.n_out
                for k in range(prev.n_out):
                    s = 0.0
                    for j in range(n):
                        s += delta[j] * layer.w[k][j]
                    new_delta[k] = s * d_tanh(prev.pre[k])
                delta = new_delta
        return sum((o - t) ** 2 for o, t in
                   zip(out, self._onehot(target_idx, target_vec))) / len(out)

    def _onehot(self, ti, tv):
        n = len(self.layers[-1].b)
        if ti is not None:
            return [1.0 if i == ti else 0.0 for i in range(n)]
        return tv

    # ---------- сериализация ----------
    def to_dict(self):
        return {"arch": [len(self.layers[0].w)] +
                       [l.n_out for l in self.layers],
                "out": self.out_mode,
                "layers": [{"w": l.w, "b": l.b} for l in self.layers]}

    @classmethod
    def from_dict(cls, d):
        net = cls.__new__(cls)
        net.layers = []
        for ld in d["layers"]:
            net.layers.append(Dense(ld["w"], ld["b"]))
        net.out_mode = d.get("out", "softmax")
        net.lr = 0.05
        return net
