@echo off
echo Starting DFM Engine v1...

if not exist "venv" (
    echo Error: Virtual environment not found. Please run build.bat first.
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate

echo Starting FastAPI server...
python -m app.main

pause
