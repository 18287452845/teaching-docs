@echo off
setlocal
cd /d "%~dp0"
node .\scripts\run-sync.mjs >nul 2>&1
git diff --quiet
if %errorlevel% equ 0 (
    exit /b
)
for /f "delims=" %%i in ('git branch --show-current') do set BRANCH=%%i
if "%BRANCH%"=="" set BRANCH=main
git add -A
git commit -m "update: auto sync %date:~0,10,1% %time:~0,8,1%" --quiet
git push origin %BRANCH% --quiet
