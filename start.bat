@echo off
setlocal

cd /d "%~dp0"
set "PROJECT_ROOT=%CD%"
set "VENV_PYTHON=%PROJECT_ROOT%\Scripts\python.exe"
set "FRONTEND_DIR=%PROJECT_ROOT%\frontend"
set "CONFIG_URL=http://127.0.0.1:5000/UI"

if not exist "%VENV_PYTHON%" goto run_setup
if not exist "%FRONTEND_DIR%\node_modules" goto run_setup
call :find_npm
if not defined NPM_EXE goto run_setup
goto launch

:run_setup
echo GryphDeck has not been fully set up yet. Running setup.bat...
call "%PROJECT_ROOT%\setup.bat"
if errorlevel 1 (
    echo Startup stopped because setup did not complete.
    exit /b 1
)
call :find_npm
if not defined NPM_EXE (
    echo Startup stopped because npm could not be found.
    exit /b 1
)

:launch
echo Starting the Flask backend...
start "GryphDeck Backend" /D "%PROJECT_ROOT%" "%ComSpec%" /k ""%VENV_PYTHON%" run.py"

echo Starting the Next.js frontend...
start "GryphDeck Frontend" /D "%FRONTEND_DIR%" "%ComSpec%" /k ""%NPM_EXE%" run dev"

echo Waiting for the backend configuration page...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$deadline = (Get-Date).AddSeconds(20); do { try { $response = Invoke-WebRequest -UseBasicParsing '%CONFIG_URL%' -TimeoutSec 1; if ($response.StatusCode -eq 200) { exit 0 } } catch {}; Start-Sleep -Milliseconds 250 } while ((Get-Date) -lt $deadline); exit 1"

if errorlevel 1 echo The backend did not respond within 20 seconds; opening the page anyway.
start "" "%CONFIG_URL%"

echo GryphDeck is running. You can close this window.
exit /b 0

:find_npm
set "NPM_EXE="

for /f "delims=" %%I in ('where.exe node.exe 2^>nul') do (
    if not defined NPM_EXE if exist "%%~dpInpm.cmd" set "NPM_EXE=%%~dpInpm.cmd"
)

if defined NPM_EXE exit /b 0

if exist "%ProgramFiles%\nodejs\node.exe" if exist "%ProgramFiles%\nodejs\npm.cmd" (
    set "NPM_EXE=%ProgramFiles%\nodejs\npm.cmd"
)
exit /b 0
