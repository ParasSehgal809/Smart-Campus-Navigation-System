@echo off
REM run_batch.bat - Runs Campus Batch Navigation on Windows

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=python
) else (
    where py >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        set PYTHON_CMD=py
    ) else (
        echo Error: Python 3 was not found in PATH.
        pause
        exit /b 1
    )
)

%PYTHON_CMD% batch_navigator.py --scenario all --csv batch_results.csv
pause
