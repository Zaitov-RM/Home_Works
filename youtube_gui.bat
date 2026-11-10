@echo off
rem Двойной клик по этому файлу запустит графическую оболочку YouTube Downloader
where pythonw >nul 2>nul
if %errorlevel%==0 (
    start "" pythonw "%~dp0youtube_gui.py"
) else (
    python "%~dp0youtube_gui.py"
)
