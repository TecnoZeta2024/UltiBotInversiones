@echo off
python -m uvicorn ultibot_backend.main:app --reload
timeout /t 10
python -m uvicorn ultibot_ui.main:app --reload
