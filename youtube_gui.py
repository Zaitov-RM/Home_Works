#!/usr/bin/env python3
"""
YouTube Downloader — графическая оболочка (Tkinter)
===================================================
Простое окно поверх youtube_downloader.py: вставляете ссылку, выбираете
папку и качество, нажимаете «Скачать» — видите прогресс и лог.

Запуск:
    python youtube_gui.py

Зависимости: только стандартная библиотека Tkinter + yt-dlp
    pip install -U yt-dlp
Рекомендуется ffmpeg для качества 1080p+ и MP3:
    winget install Gyan.FFmpeg
"""

from __future__ import annotations

import os
import queue
import shutil
import subprocess
import sys
import threading
from pathlib import Path

# ---------------------------------------------------------------------------
# Tkinter (графическая библиотека входит в стандартный Python на Windows/macOS)
# ---------------------------------------------------------------------------
try:
    import tkinter as tk
    from tkinter import ttk
except ImportError:
    sys.exit("Tkinter не найден. Установите Python с сайта python.org "
             "(его инсталлятор включает Tcl/Tk) и повторите запуск.")

# ---------------------------------------------------------------------------
# Импортируем ядро загрузчика из соседнего файла
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    import youtube_downloader as yd
except ImportError as e:  # скорее всего, нет yt-dlp
    _IMPORT_ERROR = str(e)
    yd = None
else:
    _IMPORT_ERROR = ""


def open_in_folder(path: str | Path) -> None:
    """Открывает папку с файлом в проводнике ОС."""
    path = Path(path)
    folder = path if path.is_dir() else path.parent
    try:
        if sys.platform == "win32":
            if path.is_file():
                subprocess.Popen(["explorer", "/select,", str(path)])
            else:
                os.startfile(str(folder))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(folder)])
        else:
            subprocess.Popen(["xdg-open", str(folder)])
    except Exception:
        pass  # не критично


class App:
    QUALITIES = ["Лучшее", "2160p (4K)", "1440p", "1080p", "720p", "480p", "360p"]
    QUALITY_KEYS = ["best", "2160p", "1440p", "1080p", "720p", "480p", "360p"]

    def __init__(self, root: "tk.Tk"):
        self.root = root
        self.events: "queue.Queue[dict]" = queue.Queue()
        self.worker: threading.Thread | None = None
        self._thread_states: dict[str, dict] = {}   # format_id -> {label,total,downloaded}
        self._last_ui_update = 0.0

        root.title("YouTube Downloader")
        root.geometry("640x520")
        root.minsize(520, 420)

        pad = {"padx": 10, "pady": 5}
        main = ttk.Frame(root)
        main.pack(fill="both", expand=True)

        # --- Ссылка -------------------------------------------------------
        row1 = ttk.Frame(main)
        row1.pack(fill="x", **pad)
        ttk.Label(row1, text="Ссылка:").pack(side="left")
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(row1, textvariable=self.url_var)
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(6, 6))
        self.url_entry.bind("<Return>", lambda e: self.on_download())
        ttk.Button(row1, text="Вставить", command=self._paste).pack(side="right")

        # --- Папка сохранения ---------------------------------------------
        row2 = ttk.Frame(main)
        row2.pack(fill="x", **pad)
        ttk.Label(row2, text="Папка:").pack(side="left")
        default_out = str(Path.home() / "Downloads" / "youtube")
        self.out_var = tk.StringVar(value=default_out)
        ttk.Entry(row2, textvariable=self.out_var).pack(side="left", fill="x", expand=True, padx=(6, 6))
        ttk.Button(row2, text="Обзор…", command=self._choose_dir).pack(side="right")

        # --- Настройки ------------------------------------------------------
        row3 = ttk.Frame(main)
        row3.pack(fill="x", **pad)

        ttk.Label(row3, text="Качество:").pack(side="left")
        self.quality_var = tk.StringVar(value=self.QUALITIES[0])
        self.quality_combo = ttk.Combobox(row3, textvariable=self.quality_var,
                                          values=self.QUALITIES, state="readonly", width=12)
        self.quality_combo.pack(side="left", padx=(4, 14))

        self.audio_only_var = tk.BooleanVar()
        self.audio_chk = ttk.Checkbutton(row3, text="Только аудио (MP3)",
                                         variable=self.audio_only_var,
                                         command=self._toggle_audio)
        self.audio_chk.pack(side="left")

        self.playlist_var = tk.BooleanVar()
        ttk.Checkbutton(row3, text="Плейлист целиком",
                        variable=self.playlist_var).pack(side="left", padx=(12, 0))

        # --- Кнопки ---------------------------------------------------------
        row4 = ttk.Frame(main)
        row4.pack(fill="x", **pad)
        self.dl_btn = ttk.Button(row4, text="⬇  Скачать", command=self.on_download)
        self.dl_btn.pack(side="left")
        ttk.Button(row4, text="Открыть папку", command=lambda: open_in_folder(self.out_var.get())).pack(side="left", padx=8)
        self.status_var = tk.StringVar(value="Готов к работе")
        ttk.Label(row4, textvariable=self.status_var, anchor="e").pack(side="right", fill="x", expand=True)

        # --- Прогресс -------------------------------------------------------
        self.pbar = ttk.Progressbar(main, mode="determinate", maximum=1000)
        self.pbar.pack(fill="x", padx=10, pady=(5, 0))
        self.prog_label_var = tk.StringVar(value="")
        ttk.Label(main, textvariable=self.prog_label_var, anchor="w").pack(fill="x", padx=10)

        # --- Лог ------------------------------------------------------------
        self.log = tk.Text(main, height=10, wrap="word", state="disabled")
        self.log.pack(fill="both", expand=True, padx=10, pady=(6, 10))
        for tag, color in (("ok", "#1a7f37"), ("err", "#b91c1c"), ("info", "#374151")):
            self.log.tag_configure(tag, foreground=color)

        # Проверка зависимостей при старте
        if yd is None:
            self._log(f"✖ Не удалось загрузить модули: {_IMPORT_ERROR}\n"
                      "Установите зависимости:  pip install -U yt-dlp", "err")
            self.dl_btn.state(["disabled"])
        elif shutil.which("ffmpeg") is None:
            self._log("ℹ ffmpeg не найден: доступно видео до 720p со звуком (без склейки).\n"
                      "Для 1080p+/MP3 установите:  winget install Gyan.FFmpeg", "info")

        self.root.after(100, self._poll_events)

    # ------------------------------------------------------------------ UI
    def _paste(self):
        try:
            self.url_var.set(self.root.clipboard_get().strip().splitlines()[0])
        except Exception:
            pass

    def _choose_dir(self):
        from tkinter.filedialog import askdirectory
        d = askdirectory(initialdir=self.out_var.get() or str(Path.home()), title="Выберите папку")
        if d:
            self.out_var.set(d)

    def _toggle_audio(self):
        disabled = bool(self.audio_only_var.get())
        state = ["disabled"] if disabled else ["!disabled"]
        self.quality_combo.state(state)

    def _log(self, msg: str, tag: str = "info"):
        self.log.configure(state="normal")
        self.log.insert("end", msg.rstrip() + "\n", tag)
        self.log.see("end")
        self.log.configure(state="disabled")

    # ------------------------------------------------------------- Download
    def on_download(self):
        if self.worker and self.worker.is_alive():
            return
        urls = [u.strip() for u in self.url_var.get().replace(",", "\n").splitlines() if u.strip()]
        if not urls:
            self._log("✖ Вставьте ссылку на видео.", "err")
            return

        quality = self.QUALITY_KEYS[self.QUALITIES.index(self.quality_var.get())] \
            if self.quality_var.get() in self.QUALITIES else "best"
        params = dict(
            urls=urls,
            output=self.out_var.get() or "./downloads",
            quality=quality,
            audio_only=self.audio_only_var.get(),
            playlist=self.playlist_var.get(),
        )

        self.dl_btn.state(["disabled"])
        self.status_var.set("Скачивание…")
        self.pbar["value"] = 0
        self._thread_states.clear()
        self._log(f"▶ Начало загрузки: {', '.join(urls)}", "info")

        def run():
            try:
                yd.download_core(**params, ui_callback=self.events.put)
            except Exception as e:  # RuntimeError без ffmpeg и пр.
                self.events.put({"type": "error", "message": f"✖ {e}"})
                self.events.put({"type": "done", "ok": 0, "failed": len(urls), "outdir": ""})

        self.worker = threading.Thread(target=run, daemon=True)
        self.worker.start()

    # ------------------------------------------------------------- Events
    def _poll_events(self):
        try:
            while True:
                ev = self.events.get_nowait()
                self._handle_event(ev)
        except queue.Empty:
            pass
        self.root.after(100, self._poll_events)

    def _handle_event(self, ev: dict):
        t = ev.get("type")
        if t == "progress":
            fid = str(ev.get("format_id"))
            st = self._thread_states.setdefault(fid, {"label": "", "total": 0})
            st["label"] = ev.get("label", "")
            st["total"] = ev.get("total_bytes") or st["total"]
            st["downloaded"] = ev.get("downloaded_bytes") or 0
            st["speed"] = ev.get("speed") or 0
            st["eta"] = ev.get("eta")
            self._update_progress_bar()
        elif t == "thread_finished":
            fid = str(ev.get("format_id"))
            st = self._thread_states.setdefault(fid, {"label": "", "total": 0})
            st["downloaded"] = st["total"] = ev.get("total_bytes") or st.get("downloaded", 0)
            self._update_progress_bar()
        elif t == "postprocess":
            if ev.get("status") == "started":
                what = "склейка видео + аудио" if ev.get("kind") == "merge" else "конвертация в MP3"
                self.status_var.set(f"Обработка: {what}…")
                self.prog_label_var.set(f"⚙ {what}…")
        elif t == "info":
            msg = ev.get("message", "")
            self._log(msg, "ok" if msg.startswith("✔") else "info")
        elif t == "error":
            self._log(ev.get("message", ""), "err")
        elif t == "done":
            ok, failed = ev.get("ok", 0), ev.get("failed", 0)
            if failed == 0:
                self.status_var.set("Готово ✔")
                self.pbar["value"] = self.pbar["maximum"]
                self.prog_label_var.set("✔ Все загрузки завершены")
                outdir = ev.get("outdir", "")
                if outdir and ok:
                    self._log(f"Файлы сохранены в: {outdir}", "ok")
                    open_in_folder(outdir)
            else:
                self.status_var.set(f"Завершено с ошибками: {failed} из {ok + failed}")
            self.dl_btn.state(["!disabled"])

    def _update_progress_bar(self):
        total = sum(s.get("total", 0) for s in self._thread_states.values())
        done = sum(min(s.get("downloaded", 0), s.get("total", 0) or 1 << 62)
                   for s in self._thread_states.values())
        if total > 0:
            frac = min(done / total, 1.0)
            self.pbar["value"] = frac * 1000
            mb_done, mb_total = done / 1048576, total / 1048576
            labels = ", ".join(sorted({s["label"] for s in self._thread_states.values() if s["label"]}))
            speed = sum(s.get("speed", 0) for s in self._thread_states.values())
            eta = max((s.get("eta") or 0) for s in self._thread_states.values())
            parts = [f"{labels}: {frac*100:.1f}%  ({mb_done:.1f} / {mb_total:.1f} МБ)"]
            if speed:
                parts.append(f"{speed/1048576:.2f} МБ/с")
            if eta:
                parts.append(f"осталось ~{eta} с")
            self.prog_label_var.set("   |   ".join(parts))


def main() -> int:
    root = tk.Tk()
    try:
        ttk.Style(root).theme_use("vista")
    except Exception:
        pass
    App(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
