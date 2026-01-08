@echo off
cd ..

uv run pytest tests/ -v

cd %~dp0

pause
