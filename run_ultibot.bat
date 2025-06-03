@echo off
REM Script para lanzar UltiBot Backend y Frontend (UI) en ventanas separadas

REM Lanzar backend (FastAPI/Uvicorn)
start "UltiBot Backend" cmd /k "uvicorn src.ultibot_backend.main:app --reload"

REM Lanzar frontend (PyQt5 UI)
start "UltiBot UI" cmd /k "poetry run python src/ultibot_ui/main.py"
