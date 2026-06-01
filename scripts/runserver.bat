@echo off
set VENV=%~dp0..\.venv\Scripts\python.exe
"%VENV%" "%~dp0..\manage.py" runserver
