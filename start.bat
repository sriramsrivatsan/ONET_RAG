@echo off
REM Labor Market RAG - Quick Start Script for Windows

echo 🚀 Labor Market RAG - Quick Start
echo ==================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.10 or higher.
    pause
    exit /b 1
)

echo ✅ Python found
python --version
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv\" (
    echo 📦 Creating virtual environment...
    python -m venv venv
    echo ✅ Virtual environment created
) else (
    echo ✅ Virtual environment already exists
)

echo.

REM Activate virtual environment
echo 🔌 Activating virtual environment...
call venv\Scripts\activate.bat

echo.

REM Install dependencies
echo 📥 Installing dependencies...
pip install -r requirements.txt

echo.

REM Check for OpenAI API key
if "%OPENAI_API_KEY%"=="" (
    echo ⚠️  OpenAI API key not found in environment
    echo.
    echo Please set your API key:
    echo   set OPENAI_API_KEY=your-key-here
    echo.
    echo Or create .streamlit\secrets.toml with:
    echo   OPENAI_API_KEY = "your-key-here"
    echo.
) else (
    echo ✅ OpenAI API key found
)

echo.
echo 🎯 Starting application...
echo.
echo Access the application at: http://localhost:8501
echo.
echo Press Ctrl+C to stop the application
echo.

REM Run Streamlit app
streamlit run app\main.py

pause
