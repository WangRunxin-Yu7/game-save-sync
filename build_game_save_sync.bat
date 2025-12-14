@echo off
setlocal
if not exist "output" mkdir "output"
pyinstaller -F -w -n game_save_sync --clean --distpath "output" "src\main.py"
exit /b %errorlevel%
