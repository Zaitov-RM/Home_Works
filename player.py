#!/usr/bin/env python3
"""Самый простой терминальный проигрыватель музыки.

Использование:
    python3 player.py [папка_с_музыкой]

Управление:
    Enter  - играть / пауза (продолжить)
    n      - следующий трек
    p      - предыдущий трек
    q      - выход
"""

import os
import sys
import time
import shutil
import signal
import termios
import tty
from subprocess import Popen, DEVNULL

EXTENSIONS = (".mp3", ".ogg", ".wav", ".flac", ".m4a", ".aac", ".opus", ".wma")


def find_player():
    """Ищем доступный консольный плеер (ffplay из ffmpeg или mpg123)."""
    for name in ("ffplay", "mpg123"):
        path = shutil.which(name)
        if path:
            return path
    sys.exit("Не найден плеер. Установите ffmpeg или mpg123.")


def read_key():
    """Читает одну нажатую клавишу без Enter (сигнал 't' - трек закончился)."""
    if not sys.stdin.isatty():  # запуск не из терминала (pipe) - просто ждём
        time.sleep(0.2)
        return "t"
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


class Player:
    def __init__(self, playlist, player_bin):
        self.playlist = playlist
        self.player_bin = player_bin
        self.index = 0
        self.proc = None
        self.paused = False

    @property
    def track(self):
        return self.playlist[self.index]

    def play(self):
        self.stop()
        if os.path.basename(self.player_bin) == "ffplay":
            cmd = [self.player_bin, "-nodisp", "-autoexit", "-loglevel", "quiet", self.track]
        else:  # mpg123 умеет только mp3
            cmd = [self.player_bin, "-q", self.track]
        self.proc = Popen(cmd, stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL)
        self.paused = False

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=2)
            except Exception:
                self.proc.kill()
        self.proc = None

    def pause(self):
        """Приостановка/продолжение через сигналы SIGSTOP/SIGCONT."""
        if not self.proc or self.proc.poll() is not None:
            return
        sig = signal.SIGCONT if self.paused else signal.SIGSTOP
        os.kill(self.proc.pid, sig)
        self.paused = not self.paused

    def next(self):
        self.index = (self.index + 1) % len(self.playlist)
        self.play()

    def prev(self):
        self.index = (self.index - 1) % len(self.playlist)
        self.play()

    def running(self):
        return self.proc is not None and self.proc.poll() is None


def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else "."
    if os.path.isfile(folder):
        playlist = [folder]
    else:
        playlist = sorted(
            os.path.join(root, f)
            for root, _, files in os.walk(folder)
            for f in files
            if f.lower().endswith(EXTENSIONS)
        )
    if not playlist:
        sys.exit(f"В папке '{folder}' не найдено аудиофайлов.")

    player_bin = find_player()
    pl = Player(playlist, player_bin)
    pl.play()

    print(f"Плеер: {os.path.basename(player_bin)} | Треков: {len(playlist)}")
    print("Enter - играть/пауза, n - следующий, p - предыдущий, q - выход\n")

    try:
        while True:
            if not pl.running() and not pl.paused:
                pl.next()  # трек закончился -> играем следующий
            print(f"\r▶ {pl.track}{'   ' if not pl.paused else ' [II]'}", end=" ", flush=True)
            key = read_key()
            if key in ("q", "\x03"):  # q или Ctrl+C
                break
            elif key in ("\r", "\n", " "):
                if pl.running():
                    pl.pause()
                else:
                    pl.play()
            elif key == "n":
                pl.next()
            elif key == "p":
                pl.prev()
            # key == "t" - трек ещё играет, просто обновили строку статуса
            time.sleep(0.05)
    finally:
        pl.stop()
        print("\nПока!")


if __name__ == "__main__":
    main()
