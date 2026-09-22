@echo off
setlocal
cd /d "%~dp0"
set "PYTHONPATH=%CD%\src;%PYTHONPATH%"

if exist ".venv\Scripts\python.exe" (
    set "PYTHON=.venv\Scripts\python.exe"
) else (
    where py >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON=py -3"
    ) else (
        where python >nul 2>nul
        if errorlevel 1 (
            echo Python 3.10 or later is required.
            pause
            exit /b 1
        )
        set "PYTHON=python"
    )
)

%PYTHON% -c "import PIL, reportlab" >nul 2>nul
if errorlevel 1 (
    echo Installing required packages...
    %PYTHON% -m pip install -r requirements.txt
    if errorlevel 1 (
        echo Package installation failed.
        pause
        exit /b 1
    )
)

%PYTHON% main.py
if errorlevel 1 pause
