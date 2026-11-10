#!/usr/bin/env python3
"""
YouTube Video Downloader
========================
Программа для скачивания видео (и аудио) с YouTube на основе yt-dlp.

Возможности:
  - скачивание видео в выбранном качестве (best, 1080p, 720p, 480p...)
  - скачивание только аудио в MP3
  - выбор папки назначения
  - пакетное скачивание нескольких ссылок / плейлистов
  - загрузка субтитров (--subs)
  - красивый прогресс-бар

Установка зависимостей:
    pip install -U yt-dlp
    (рекомендуется также установить ffmpeg для склейки видео+аудио и конвертации в mp3)

Примеры запуска:
    python youtube_downloader.py "https://www.youtube.com/watch?v=VIDEO_ID"
    python youtube_downloader.py -q 720p -o ~/Videos URL1 URL2
    python youtube_downloader.py --audio-only URL            # только аудио -> mp3
    python youtube_downloader.py --playlist URL              # весь плейлист
    python youtube_downloader.py --list-formats URL          # показать доступные форматы
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    sys.exit("Ошибка: модуль yt-dlp не найден. Установите его командой: pip install -U yt-dlp")


# ---------------------------------------------------------------------------
# Прогресс-бар
# ---------------------------------------------------------------------------

def _fmt_size(n: float) -> str:
    for unit in ("Б", "КБ", "МБ", "ГБ"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} ТБ"


def _progress_hook(d: dict, ui_callback=None) -> None:
    """Отображает прогресс загрузки отдельного потока (видео или аудио).

    Если передан ui_callback — вместо печати в терминал отправляет структурированные
    события в GUI-оболочку (см. youtube_gui.py).
    """
    if ui_callback is not None:
        info = d.get("info_dict") or {}
        vcodec = info.get("vcodec") or "none"
        payload = {
            "type": "progress",
            "status": d.get("status"),
            "label": "аудио" if vcodec == "none" else "видео",
            "format_id": info.get("format_id") or "?",
            "downloaded_bytes": d.get("downloaded_bytes") or 0,
            "total_bytes": d.get("total_bytes") or d.get("total_bytes_estimate") or 0,
            "speed": d.get("speed") or 0,
            "eta": d.get("eta"),
            "filename": d.get("filename") or "",
        }
        if d.get("status") == "finished":
            payload["type"] = "thread_finished"
        ui_callback(payload)
        return

    info = d.get("info_dict") or {}
    fid = info.get("format_id") or "?"
    vcodec = (info.get("vcodec") or "none")
    label = "аудио" if vcodec == "none" else "видео"
    prefix = f"[{label} {fid}] "

    if d["status"] == "downloading":
        downloaded = d.get("downloaded_bytes") or 0
        total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
        speed = d.get("speed") or 0
        eta = d.get("eta")

        if total:
            percent = downloaded / total * 100
            bar_len = 24
            filled = int(bar_len * percent // 100)
            bar = "#" * filled + "-" * (bar_len - filled)
            speed_str = f"{speed / 1024 / 1024:.2f} МБ/с" if speed else "--"
            eta_str = f"{eta} c" if eta is not None else "--"
            sys.stdout.write(
                f"\r{prefix}[{bar}] {percent:5.1f}% | {speed_str:>9} | ETA: {eta_str:>6} "
            )
        else:
            sys.stdout.write(f"\r{prefix}{_fmt_size(downloaded)} ...")
        sys.stdout.flush()
    elif d["status"] == "finished":
        total = d.get("total_bytes") or 0
        sys.stdout.write(
            f"\r{prefix}загружено {_fmt_size(total)}" + " " * 20 + "\n"
        )
        sys.stdout.flush()


def _postprocessor_hook(d: dict, ui_callback=None) -> None:
    pp = (d.get("postprocessor") or "").lower()
    if ui_callback is not None:
        kind = "merge" if ("mergearbvr" in pp or "ffmpegmerge" in pp) else \
               "audio" if "ffmpegextractaudio" in pp else None
        if kind:
            ui_callback({"type": "postprocess", "kind": kind,
                         "status": d.get("status"),
                         "filename": d.get("info_dict", {}).get("filepath", "")})
        return
    if d["status"] == "started":
        pp = (d.get("postprocessor") or "").lower()
        if "mergearbvr" in pp or "ffmpegmerge" in pp:
            print("\033[32m✔ Потоки загружены. Склейка видео + аудио (ffmpeg)...\033[0m")
    elif d["status"] == "finished":
        pp = (d.get("postprocessor") or "").lower()
        if "mergearbvr" in pp or "ffmpegmerge" in pp:
            print("\033[32m✔ Склейка завершена — файл готов (со звуком).\033[0m")
        elif "moviedetailsbyfilename" in pp:
            print("\033[32m✔ Готово!\033[0m")


# ---------------------------------------------------------------------------
# Основная логика
# ---------------------------------------------------------------------------

QUALITY_MAP = {
    "best": "bestvideo*+bestaudio/best",
    "2160p": "bestvideo[height<=2160]+bestaudio/best[height<=2160]",
    "1440p": "bestvideo[height<=1440]+bestaudio/best[height<=1440]",
    "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
    "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
    "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
    "360p": "bestvideo[height<=360]+bestaudio/best[height<=360]",
}


def build_ydl_opts(args: argparse.Namespace, ui_callback=None) -> dict:
    outdir = Path(args.output).expanduser()
    outdir.mkdir(parents=True, exist_ok=True)

    def _ph(d):
        _progress_hook(d, ui_callback=ui_callback)

    def _pph(d):
        _postprocessor_hook(d, ui_callback=ui_callback)

    opts: dict = {
        "outtmpl": str(outdir / "%(title)s [%(id)s].%(ext)s"),
        "progress_hooks": [_ph],
        "postprocessor_hooks": [_pph],
        "ignoreerrors": args.playlist,          # не падать на недоступных видео плейлиста
        "noplaylist": not args.playlist,        # по умолчанию брать только одно видео
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": False,
        # --- Защита от HTTP 503 со стороны YouTube -------------------------
        # Свежая версия yt-dlp решает «проблемы» (nsig/попадание на rate-limited
        # серверы) и корректно подбирает клиент. Это главное средство от 503.
        "extractor_args": {"youtube": {"player_client": ["default", "web"]}},
        # Если всё же поток вернёт 503 — yt-dlp сам переключится на другой
        # сервер/поток вместо мгновенного падения.
        "retries": 10,
        "fragment_retries": 10,
        "file_access_retries": 3,
        "sleep_interval_requests": 1,
    }

    if args.audio_only:
        if shutil.which("ffmpeg") is None:
            msg = "Для скачивания MP3 нужен ffmpeg. Установите его: winget install Gyan.FFmpeg"
            if ui_callback is not None:
                ui_callback({"type": "error", "message": msg})
                raise RuntimeError(msg)
            sys.exit(msg)
        opts["format"] = "bestaudio/best"
        opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": args.audio_bitrate,
            },
            {"key": "FFmpegMetadata"},
        ]
    else:
        has_ffmpeg = shutil.which("ffmpeg") is not None
        if not has_ffmpeg and args.quality in ("best", "2160p", "1440p", "1080p"):
            # Без ffmpeg склейка видео+аудио невозможна — иначе получится файл без звука.
            # Берём «прогрессивные» форматы (видео и аудио в одном файле), они доступны до 720p.
            print(
                "\033[33mВнимание: ffmpeg не найден. Скачиваю прогрессивный формат "
                "(до 720p, со звуком, без склейки).\n"
                "Для качества 1080p+ установите ffmpeg: winget install Gyan.FFmpeg\033[0m",
                file=sys.stderr,
            )
            opts["format"] = (
                "best[height<=720][acodec!=none][vcodec!=none]/"
                "bestvideo[height<=720]+bestaudio/best[height<=720]"
            )
        else:
            opts["format"] = QUALITY_MAP.get(args.quality, QUALITY_MAP["best"])
            opts["merge_output_format"] = "mp4"

    if args.subs:
        opts["writesubtitles"] = True
        opts["writeautomaticsub"] = True
        opts["subtitleslangs"] = [l.strip() for l in args.subs_langs.split(",")]
        opts["subtitlesformat"] = "srt/best"

    if getattr(args, "cookies", None):
        opts["cookiefile"] = str(Path(args.cookies).expanduser())
    if getattr(args, "cookies_from_browser", None):
        opts["cookiesfrombrowser"] = (args.cookies_from_browser,)

    return opts


def list_formats(url: str, opts: dict | None = None) -> None:
    """Показывает список доступных форматов для видео."""
    cfg = {"quiet": True, "no_warnings": True}
    if opts:
        cfg["cookiefile"] = opts.get("cookiefile")
        cfg["cookiesfrombrowser"] = opts.get("cookiesfrombrowser")
    with yt_dlp.YoutubeDL({k: v for k, v in cfg.items() if v}) as ydl:
        info = ydl.extract_info(url, download=False)
        print(f"\nВидео: {info.get('title')}  (длительность: {info.get('duration', 0)} c)\n")
        fmt_table = yt_dlp.format_utils.build_format_table(info["formats"])
        print(fmt_table)


def download(urls: list[str], args: argparse.Namespace) -> int:
    """CLI-точка входа: делегирует общей функции download_core."""
    n_failed = download_core(
        urls,
        output=args.output,
        quality=args.quality,
        audio_only=args.audio_only,
        audio_bitrate=args.audio_bitrate,
        playlist=args.playlist,
        subs=args.subs,
        subs_langs=args.subs_langs,
        cookies=getattr(args, "cookies", None),
        cookies_from_browser=getattr(args, "cookies_from_browser", None),
        ui_callback=None,
    )
    return 1 if n_failed else 0


def download_core(urls, *, output="./downloads", quality="best", audio_only=False,
                  audio_bitrate="192", playlist=False, subs=False, subs_langs="ru,en",
                  cookies=None, cookies_from_browser=None, ui_callback=None) -> int:
    """Общая логика скачивания — используется и CLI, и GUI-оболочкой.

    ui_callback: необязательная функция, принимающая dict-события
    (progress / thread_finished / postprocess / info / error / done).
    Возвращает число неуспешных ссылок.
    """
    args = argparse.Namespace(
        output=output, quality=quality, audio_only=audio_only,
        audio_bitrate=audio_bitrate, playlist=playlist, subs=subs,
        subs_langs=subs_langs, cookies=cookies,
        cookies_from_browser=cookies_from_browser, list_formats=False,
    )
    opts = build_ydl_opts(args, ui_callback=ui_callback)
    emit = ui_callback or (lambda e: None)
    failed: list[str] = []

    with yt_dlp.YoutubeDL(opts) as ydl:
        for i, url in enumerate(urls, 1):
            if len(urls) > 1:
                msg = f"[{i}/{len(urls)}] {url}"
                print(f"\n=== {msg} ===") if ui_callback is None else emit({"type": "info", "message": msg})
            try:
                ydl.download([url])
                emit({"type": "info", "message": f"✔ Готово: {url}"})
                if ui_callback is None:
                    print("\033[32m✔ Готово!\033[0m")
            except yt_dlp.utils.DownloadError as e:
                text = str(e)
                if ui_callback is None:
                    print(f"\033[31m✖ Ошибка при скачивании {url}:\033[0m {text}", file=sys.stderr)
                    if "503" in text:
                        print(
                            "\033[33mПодсказка: HTTP 503 — YouTube временно ограничил этот IP/поток.\n"
                            "  1) Обновите yt-dlp:  pip install -U yt-dlp\n"
                            "  2) Подождите несколько минут и повторите попытку;\n"
                            "  3) Попробуйте другое качество:  -q 720p (или -q 480p);\n"
                            "  4) Смените сеть (например, мобильный интернет/VPN);\n"
                            "  5) Если не помогает — добавьте --cookies-from-browser chrome\033[0m",
                            file=sys.stderr,
                        )
                else:
                    hint = ""
                    if "503" in text:
                        hint = ("\nПодсказка: HTTP 503 — YouTube временно ограничил выдачу. "
                                "Обновите yt-dlp (pip install -U yt-dlp), подождите несколько "
                                "минут или попробуйте качество 720p/480p.")
                    emit({"type": "error", "message": f"✖ {url}\n{text}{hint}"})
                failed.append(url)

    n_ok = len(urls) - len(failed)
    if ui_callback is None:
        if failed:
            print(f"\n\033[31mНе удалось скачать {len(failed)} из {len(urls)}:\033[0m")
            for u in failed:
                print("  -", u)
        else:
            print(f"\n\033[32mВсе загрузки завершены. Файлы сохранены в: {Path(args.output).expanduser().resolve()}\033[0m")
    else:
        emit({"type": "done", "ok": n_ok, "failed": len(failed),
              "outdir": str(Path(args.output).expanduser().resolve())})
    return len(failed)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Скачивание видео с YouTube (на базе yt-dlp)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("urls", nargs="+", help="одна или несколько ссылок на видео/плейлист")
    parser.add_argument("-o", "--output", default="./downloads",
                        help="папка для сохранения файлов")
    parser.add_argument("-q", "--quality", choices=list(QUALITY_MAP), default="best",
                        help="желаемое качество видео")
    parser.add_argument("--audio-only", action="store_true",
                        help="скачать только аудио и сохранить как MP3")
    parser.add_argument("--audio-bitrate", default="192",
                        help="битрейт MP3 в кбит/с (для --audio-only)")
    parser.add_argument("--playlist", action="store_true",
                        help="скачать весь плейлист целиком, а не только первое видео")
    parser.add_argument("--subs", action="store_true",
                        help="скачать субтитры (в т.ч. автосгенерированные)")
    parser.add_argument("--subs-langs", default="ru,en",
                        help="языки субтитров через запятую")
    parser.add_argument("--list-formats", action="store_true",
                        help="показать доступные форматы и выйти (без скачивания)")
    parser.add_argument("--cookies", metavar="FILE",
                        help="файл cookies.txt (на случай запроса YouTube 'Sign in to confirm you're not a bot')")
    parser.add_argument("--cookies-from-browser", metavar="BROWSER",
                        help="брать cookies из браузера: chrome, firefox, edge, safari, brave...")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.list_formats:
        try:
            list_formats(args.urls[0], build_ydl_opts(args))
        except yt_dlp.utils.DownloadError as e:
            print(f"\033[31m✖ Не удалось получить список форматов:\033[0m {e}", file=sys.stderr)
            return 1
        return 0

    return download(args.urls, args)


if __name__ == "__main__":
    raise SystemExit(main())
