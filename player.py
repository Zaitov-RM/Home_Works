#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Самый простой терминальный проигрыватель музыки.
Работает на Windows, Linux и macOS.

Использование (Windows):
    python player.py C:\\Users\\Graviton\\Music

Управление:
    Enter  - следующий трек / начать воспроизведение
    q      - выход (или Ctrl+C)

Воспроизведение в Windows делегируется PowerShell (MediaPlayer),
в Linux/macOS - ffplay или mpg123.
"""

import os
import sys
import time
import shutil
import subprocess

AUDIO_EXTS = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".opus", ".wma"}


def find_tracks(path):
    """Собирает список аудиофайлов из файла или папки."""
    if os.path.isfile(path):
        return [path]
    tracks = []
    for root, _dirs, files in os.walk(path):
        for f in sorted(files):
            if os.path.splitext(f)[1].lower() in AUDIO_EXTS:
                tracks.append(os.path.join(root, f))
    return tracks


def play_windows(track):
    """Проигрывает трек через PowerShell (System.Windows.Media)."""
    ps = (
        "Add-Type -AssemblyName presentationCore; "
        "$p = New-Object System.Windows.Media.MediaPlayer; "
        "$p.Open([uri]'{}'); $p.Play(); "
        "while ($p.NaturalDuration.HasTimeSpan -and "
        "$p.Position -lt $p.NaturalDuration.TimeSpan) {{ Start-Sleep -m 200 }}".format(
            track.replace("'", "''")
        )
    )
    proc = subprocess.Popen(
        ["powershell", "-NoProfile", "-Command", ps],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        while proc.poll() is None:
            time.sleep(0.2)
    except KeyboardInterrupt:
        proc.terminate()
        raise
    return proc.returncode or 0


def play_unix(track, players):
    """Проигрывает трек через консольный плеер (ffplay/mpg123/afplay)."""
    name, args = players
    cmd = [name] + args + [track]
    proc = subprocess.Popen(cmd)
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        raise
    return proc.returncode or 0


def find_unix_players():
    candidates = [
        ("ffplay", ["-nodisp", "-autoexit", "-loglevel", "quiet"]),
        ("mpg123", ["-q"]),
        ("afplay", []),       # macOS
    ]
    for name, args in candidates:
        if shutil.which(name):
            return (name, args)
    return None


def main():
    if len(sys.argv) > 1:
        src = sys.argv[1]
    else:
        src = os.getcwd()

    tracks = find_tracks(src)
    if not tracks:
        print("Не нашёл аудиофайлов в:", src)
        print("Поддерживаемые форматы:", ", ".join(sorted(AUDIO_EXTS)))
        return 1

    is_windows = os.name == "nt"
    players = None
    if not is_windows:
        players = find_unix_players()
        if not players:
            print("Не найден плеер. Установите ffmpeg или mpg123:")
            print("  Debian/Ubuntu: sudo apt install ffmpeg")
            return 1

    print("Найдено треков: {}".format(len(tracks)))
    print("Enter - следующий трек, q - выход\n")

    try:
        for i, track in enumerate(tracks, 1):
            print("[{}/{}] {}".format(i, len(tracks), os.path.basename(track)))
            if is_windows:
                play_windows(track)
            else:
                play_unix(track, players)
    except KeyboardInterrupt:
        pass

    print("\nГотово.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
