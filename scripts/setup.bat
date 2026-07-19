@echo off
echo ===================================================
echo   Human Skill Digital Twin - Setup Installer
echo ===================================================
echo Checking dependencies...

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH. Please install Python 3.10+ and try again.
    exit /b %errorlevel%
)

node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not in PATH. Please install Node.js 18+ and try again.
    exit /b %errorlevel%
)

echo Creating Python Virtual Environment (venv)...
python -m venv venv

echo Activating Virtual Environment and installing pip requirements...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r backend/requirements.txt

echo Installing frontend packages...
cd frontend
call npm install
cd ..

echo ===================================================
echo   Setup completed successfully!
echo   Run "scripts\run.bat" to start the platform.
echo ===================================================
pause
