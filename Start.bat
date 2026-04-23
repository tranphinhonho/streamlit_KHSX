@echo off
title B7KHSX - Production Planning System
echo ========================================
echo   B7KHSX - He Thong Ke Hoach San Xuat
echo ========================================
echo.

cd /d "%~dp0"

echo Dang kich hoat moi truong ao...
call .\venv\Scripts\activate

echo Dang khoi dong Streamlit...
echo URL: http://localhost:8501
echo.

python -m streamlit run main.py --server.port 8501

pause
