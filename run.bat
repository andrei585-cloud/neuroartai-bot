@echo off
REM NeuroArtAI Bot Startup Script for Windows

echo.
echo ========================================
echo   NeuroArtAI Bot - Starting...
echo ========================================
echo.

REM Check if .env exists
if not exist .env (
    echo ERROR: .env file not found!
    echo Please create .env file with:
    echo   TELEGRAM_TOKEN=your_token
    echo   HF_API_TOKEN=your_token
    pause
    exit /b 1
)

REM Check if requirements are installed
python -m pip show python-telegram-bot >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing dependencies...
    python -m pip install -r requirements.txt
)

REM Run the bot
echo Starting bot...
python bot.py

pause

