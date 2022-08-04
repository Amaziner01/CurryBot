@echo off
if not exist ".\env\" (
    python -m venv env && .\env\Scripts\activate && pip install -r requirements.txt
)