@echo off
setlocal
if not exist "output" mkdir "output"
pyinstaller -F -w -n game_save_sync --clean --distpath "output" "src\main.py"
if not exist "output\config.ini" (
    if exist "data\config.ini" (
        copy "data\config.ini" "output\config.ini"
        echo Config file copied to output folder.
    ) else (
        echo Warning: data\config.ini not found, skipping copy.
    )
) else (
    echo Config file already exists in output folder, skipping copy.
)
exit /b %errorlevel%
