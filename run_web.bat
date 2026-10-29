@echo off
REM run_web.bat - Starts Smart Campus Navigation Web Server on Windows

echo Starting Campus Navigation Web Server...

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=python
) else (
    where py >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        set PYTHON_CMD=py
    ) else (
        echo Error: Python 3 was not found in PATH. Please install Python.
        pause
        exit /b 1
    )
)

start "" http://localhost:8000
%PYTHON_CMD% server.py 8000
pause
