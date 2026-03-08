@echo off
echo Starting Auto Cut Picture...

REM Start backend
echo Starting backend...
cd backend
if not exist venv python -m venv venv
call venv\Scripts\activate
pip install -r requirements.txt -q
start /b uvicorn app.main:app --reload --port 8000
cd ..

REM Start frontend
echo Starting frontend...
cd frontend
if not exist node_modules npm install
start /b npm run dev
cd ..

echo Backend running at http://localhost:8000
echo Frontend running at http://localhost:3000
echo Press Ctrl+C to stop services

REM Wait for user to exit
pause
