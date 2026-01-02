@echo off
cd ..

"D:\GIT\BenjaminKobjolke\cli-code-analyzer\venv\Scripts\python.exe" "D:\GIT\BenjaminKobjolke\cli-code-analyzer\main.py" --language python --path "." --verbosity minimal --output "code_analysis_results" --maxamountoferrors 50 --rules "code_analysis_rules.json"

cd %~dp0

pause
