"""Wi-Fi + HTTP API LegoAI OS (MicroPython, socket).

Эндпоинты:
  GET  /            — страница управления (встроенный HTML/JS)
  GET  /api/telemetry — JSON телеметрии
  POST /api/mode    — {"mode": "run|teach_imitate|teach_rl|idle"}
  POST /api/action  — {"a": 0..4}  джойстик ребёнка в режиме обучения
  POST /api/rules   — {"rules": [[sensor,'<'|'>',thr,action],...]}
  POST /api/train   — {"what":"nn"} обучение НС на собранном датасете
  POST /api/save /api/load — модель/датасет во flash
  GET  /api/dataset — выгрузка датасета на компьютер
"""
import network, socket, json, time

try:
    import esp
except ImportError:
    esp = None

HTML = """<!doctype html><html><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>LegoAI</title><style>
body{font-family:sans-serif;background:#111;color:#eee;text-align:center}
button{font-size:24px;margin:6px;padding:14px 22px;border-radius:12px;border:0}
.joy button{background:#2a6df4;color:#fff}.act{background:#f4a827}
#t{background:#222;padding:10px;border-radius:8px;font-family:monospace}
</style></head><body>
<h2>🤖 LegoAI</h2><div id=t>…</div><p>
<button class=act onclick=mode('run')>▶ Запуск</button>
<button class=act onclick=mode('teach_imitate')>🎓 Учу руками</button>
<button class=act onclick=mode('teach_rl')>🍭 RL+похвала</button>
<button class=act onclick=mode('idle')>⏹ Стоп</button></p>
<div class=joy>
<button onclick=act(1)>⬆</button><br>
<button onclick=act(3)>⬅</button>
<button onclick=act(0)>⏹</button>
<button onclick=act(4)>➡</button><br>
<button onclick=act(2)>⬇</button></div><p>
<button onclick=post('/api/train','{}')>🧠 Обучить нейросеть</button>
<button onclick=post('/api/save','{}')>💾 Сохранить</button></p>
<script>
async function post(u,b){await fetch(u,{method:'POST',body:b})}
function mode(m){post('/api/mode',JSON.stringify({mode:m}))}
function act(a){post('/api/action',JSON.stringify({a:a}))}
setInterval(async()=>{try{const r=await fetch('/api/telemetry');
const d=await r.json();document.getElementById('t').innerText=
'режим: '+d.mode+'\\nдатчики: ['+d.state.join(', ')+']\\nпримеров: '+d.dataset+
'\\nQ-состояний: '+d.q_states}catch(e){}},700)
</script></body></html>"""


class WebServer:
    def __init__(self, robot_os, ssid=None, password="legoai4kids"):
        self.os = robot_os
        self.ssid = ssid
        self.password = password
        self.sock = None

    # ---------- Wi-Fi ----------
    def wifi_start(self):
        if self.ssid:  # режим клиента домашней сети
            sta = network.StationIF()
            sta.active(True)
            sta.connect(self.ssid, self.password)
            for _ in range(40):
                if sta.isconnected():
                    break
                time.sleep_ms(500)
            ip = sta.ifconfig()[0]
        else:          # точка доступа LegoAI-XXXX
            ap = network.SoftAP()
            chip = "".join("%02x" % b for b in esp.mac_address()[-3:]) \
                if esp else "0000"
            ap.active(True)
            try:
                ap.config(ssid="LegoAI-" + chip, key=self.password)
            except (TypeError, AttributeError):
                pass  # старые прошивки: ssid задаётся при active(True)
            ap.ifconfig(("192.168.4.1", "255.255.255.0",
                         "192.168.4.1", "8.8.8.8"))
            ip = "192.168.4.1"
        print("LegoAI OS ready: http://%s" % ip)
        return ip

    # ---------- HTTP ----------
    def start(self, port=80):
        self.sock = socket.socket()
        self.sock.bind(socket.getaddrinfo("0.0.0.0", port)[0][-1])
        self.sock.listen(2)
        self.sock.settimeout(0.05)

    def poll(self):
        """Неблокирующий: вызывать каждый цикл ОС."""
        if not self.sock:
            return
        try:
            client, _ = self.sock.accept()
        except OSError:
            return
        try:
            self._handle(client)
        finally:
            client.close()

    def _read_request(self, c):
        data = b""
        c.settimeout(1.0)
        header_end = None
        while len(data) < 4096:
            try:
                chunk = c.recv(512)
            except OSError:
                break
            if not chunk:
                break
            data += chunk
            if b"\r\n\r\n" in data:
                header_end = data.find(b"\r\n\r\n") + 4
                need = int(self._content_length(data[:header_end])) \
                    if "Content-Length" in str(data[:header_end]) else 0
                if len(data) >= header_end + need:
                    break
        if header_end is None:
            return None, None, None
        head = data[:header_end].decode(errors="ignore")
        body = data[header_end:].decode(errors="ignore")
        first = head.split("\r\n")[0].split(" ")
        return first[0], first[1], body

    @staticmethod
    def _content_length(head):
        for line in head.split("\r\n"):
            if line.lower().startswith("content-length"):
                return int(line.split(":")[1])
        return 0

    def _send(self, c, code, ctype, body):
        resp = ("HTTP/1.1 %s OK\r\nContent-Type: %s\r\n"
                "Connection: close\r\n\r\n%s") % (code, ctype, body)
        c.send(resp.encode())

    def _handle(self, c):
        method, path, body = self._read_request(c)
        if method is None:
            return
        o = self.os
        try:
            if path == "/":
                self._send(c, 200, "text/html; charset=utf-8", HTML)
            elif path == "/api/telemetry":
                self._send(c, 200, "application/json", json.dumps(o.telemetry()))
            elif path == "/api/dataset":
                self._send(c, 200, "application/json", json.dumps(o.recorder.rows))
            elif method == "POST":
                req = json.loads(body or "{}")
                if path == "/api/mode":
                    m = req.get("mode")
                    if m == "idle": o.stop()
                    elif m == "teach_imitate": o.start_teaching()
                    elif m == "teach_rl":
                        from qlearning import QLearner
                        q = o.q or QLearner(n_actions=5)
                        q.load()
                        o.start_rl(q)
                    elif m == "run":
                        if o.behavior: o.mode = "run"
                elif path == "/api/action":
                    o.human_action = int(req.get("a", 0))
                elif path == "/api/rules":
                    from behaviors import RuleBehavior
                    rb = RuleBehavior()
                    for r in req.get("rules", []):
                        rb.add_rule(int(r[0]), r[1], float(r[2]), int(r[3]))
                    o.set_behavior(rb)
                elif path == "/api/train":
                    self._train_nn()
                elif path == "/api/save":
                    if o.behavior and hasattr(o.behavior, "save"):
                        o.behavior.save()
                    if o.q: o.q.save()
                    o.recorder.save()
                elif path == "/api/load":
                    from behaviors import NNPolicyBehavior
                    o.set_behavior(NNPolicyBehavior.__new__(NNPolicyBehavior))
                    o.behavior.net = None
                    o.behavior.load()
                    if o.q: o.q.load()
                    o.recorder.load()
                self._send(c, 200, "application/json", '{"ok":true}')
            else:
                self._send(c, 404, "text/plain", "not found")
        except Exception as e:
            self._send(c, 200, "application/json",
                       json.dumps({"ok": False, "err": str(e)}))

    def _train_nn(self):
        """Обучить НС-политику на записанном датасете (on-device)."""
        from network import Network
        from behaviors import NNPolicyBehavior
        rows = self.os.recorder.rows
        if not rows:
            return
        n_in = len(rows[0]["s"])
        net = Network([n_in, 8, 5])
        pol = NNPolicyBehavior(net, explore=0.05)
        for _ in range(30):
            err = 0.0
            for r in rows:
                err += net.train(r["s"], target_idx=r["a"])
        self.os.set_behavior(pol)
        self.os.behavior.save()
