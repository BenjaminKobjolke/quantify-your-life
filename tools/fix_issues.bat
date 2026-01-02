@echo off
cd ..

"D:\GIT\BenjaminKobjolke\cli-code-analyzer\venv\Scripts\python.exe" "D:\GIT\BenjaminKobjolke\cli-code-analyzer\ruff_fixer.py" --path "." --rules "code_analysis_rules.json"

cd %~dp0

pause
