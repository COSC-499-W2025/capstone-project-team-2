chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONNOUSERSITE=1
title Capstone2
cd /d "%~dp0"
echo Starting Capstone2...
if not exist "python\Lib\site-packages\uvicorn" (
    echo First-time setup: installing dependencies...
    echo This may take a few minutes, please wait...
    python\Scripts\pip.exe install -r src/requirements.txt --target python\Lib\site-packages
    echo Setup complete!
)
start "" http://127.0.0.1:8000
python\python.exe -m uvicorn src.API.general_API:app --host 127.0.0.1 --port 8000
echo Server stopped.
pause
taskkill /F /IM python.exe
echo Server stopped.

