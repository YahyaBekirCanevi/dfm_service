@echo off
setlocal enabledelayedexpansion
echo Setting up DFM Engine Environment...

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing API dependencies...
pip install fastapi uvicorn python-multipart pydantic requests jinja2

echo.
echo Checking for pythonocc-core...
python -c "import OCC" 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] pythonocc-core is not installed.
    echo This package is usually installed via Conda:
    echo     conda install -c conda-forge pythonocc-core
    echo.
    echo You can also try: pip install pythonocc-core
    echo (Note: pip installation often fails on Windows due to complex dependencies)
) else (
    echo [OK] pythonocc-core is already installed.
)

echo.
echo Build process finished.
echo If any errors occurred above, please resolve them before running run.bat.
pause
