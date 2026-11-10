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

def _progress_hook(d: dict) -> None:
    """Отображает прогресс загрузки в консоли."""
    if d["status"] == "downloading":
        downloaded = d.get("downloaded_bytes") or 0
        total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
        speed = d.get("speed") or 0
        eta = d.get("eta")

        if total:
            percent = downloaded / total * 100
            bar_len = 30
            filled = int(bar_len * percent // 100)
            bar = "#" * filled + "-" * (bar_len - filled)
            speed_str = f"{speed / 1024 / 1024:.2f} МБ/с" if speed else "--"
            eta_str = f"{eta} c" if eta is not None else "--"
            sys.stdout.write(
                f"\r[{bar}] {percent:5.1f}% | {speed_str:>10} | ETA: {eta_str:>6} "
            )
            sys.stdout.flush()
    elif d["status"] == "finished":
        sys.stdout.write("\n\033[32m✔ Загрузка завершена.\033[0m Обработка...\n")


def _postprocessor_hook(d: dict) -> None:
    if d["status"] == "finished":
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


def build_ydl_opts(args: argparse.Namespace) -> dict:
    outdir = Path(args.output).expanduser()
    outdir.mkdir(parents=True, exist_ok=True)

    opts: dict = {
        "outtmpl": str(outdir / "%(title)s [%(id)s].%(ext)s"),
        "progress_hooks": [_progress_hook],
        "postprocessor_hooks": [_postprocessor_hook],
        "ignoreerrors": args.playlist,          # не падать на недоступных видео плейлиста
        "noplaylist": not args.playlist,        # по умолчанию брать только одно видео
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": False,
    }

    if args.audio_only:
        if shutil.which("ffmpeg") is None:
            sys.exit("Для --audio-only нужен ffmpeg. Установите его и повторите попытку.")
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
    opts = build_ydl_opts(args)
    failed: list[str] = []

    with yt_dlp.YoutubeDL(opts) as ydl:
        for i, url in enumerate(urls, 1):
            if len(urls) > 1:
                print(f"\n=== [{i}/{len(urls)}] {url} ===")
            try:
                ydl.download([url])
            except yt_dlp.utils.DownloadError as e:
                print(f"\033[31m✖ Ошибка при скачивании {url}:\033[0m {e}", file=sys.stderr)
                failed.append(url)

    if failed:
        print(f"\n\033[31mНе удалось скачать {len(failed)} из {len(urls)}:\033[0m")
        for u in failed:
            print("  -", u)
        return 1
    print(f"\n\033[32mВсе загрузки завершены. Файлы сохранены в: {Path(args.output).expanduser().resolve()}\033[0m")
    return 0


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

    if shutil.which("ffmpeg") is None and not args.audio_only and args.quality != "best":
        print("Внимание: ffmpeg не найден — объединение видео и аудио может не сработать.",
              file=sys.stderr)

    if args.list_formats:
        list_formats(args.urls[0], build_ydl_opts(args))
        return 0

    return download(args.urls, args)


if __name__ == "__main__":
    raise SystemExit(main())
