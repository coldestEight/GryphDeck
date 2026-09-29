@echo off
setlocal

cd /d "%~dp0"
set "VENV_PYTHON=%CD%\Scripts\python.exe"

echo [1/4] Checking Python...
if exist "%VENV_PYTHON%" if exist "%CD%\pyvenv.cfg" goto install_python_requirements

call :find_python
if defined PYTHON_EXE goto create_venv

echo Python 3 was not found. Attempting to install Python 3.12 with winget...
call :require_winget Python https://www.python.org/downloads/windows/
if errorlevel 1 goto failed

winget install --exact --id Python.Python.3.12 --source winget --accept-package-agreements --accept-source-agreements
if errorlevel 1 (
    echo Failed to install Python automatically.
    echo Install Python from https://www.python.org/downloads/windows/ and run setup.bat again.
    goto failed
)

call :find_python
if not defined PYTHON_EXE (
    echo Python was installed, but this terminal cannot find it yet.
    echo Open a new terminal and run setup.bat again.
    goto failed
)

:create_venv
echo [2/4] Creating the virtual environment in the project root...
"%PYTHON_EXE%" %PYTHON_ARGS% -m venv "%CD%"
if errorlevel 1 (
    echo Failed to create the Python virtual environment.
    goto failed
)

:install_python_requirements
echo [3/4] Installing Python requirements...
"%VENV_PYTHON%" -m pip install --upgrade pip
if errorlevel 1 goto failed

"%VENV_PYTHON%" -m pip install -r "%CD%\requirements.txt"
if errorlevel 1 goto failed

echo [4/4] Checking Node.js and installing frontend packages...
call :find_npm
if defined NPM_EXE goto install_frontend

echo Node.js and npm were not found. Attempting to install Node.js LTS with winget...
call :require_winget Node.js https://nodejs.org/en/download
if errorlevel 1 goto failed

winget install --exact --id OpenJS.NodeJS.LTS --source winget --accept-package-agreements --accept-source-agreements
if errorlevel 1 (
    echo Failed to install Node.js automatically.
    echo Install Node.js LTS from https://nodejs.org/en/download and run setup.bat again.
    goto failed
)

call :find_npm
if not defined NPM_EXE (
    echo Node.js was installed, but this terminal cannot find npm yet.
    echo Open a new terminal and run setup.bat again.
    goto failed
)

:install_frontend
pushd "%CD%\frontend"
call "%NPM_EXE%" install
set "NPM_EXIT=%ERRORLEVEL%"
popd

if not "%NPM_EXIT%"=="0" goto failed

echo.
echo Setup complete.
echo Start Flask with: Scripts\python.exe run.py
echo Start Next.js with: cd frontend ^&^& npm run dev
exit /b 0

:find_python
set "PYTHON_EXE="
set "PYTHON_ARGS="

py -3 --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_EXE=py"
    set "PYTHON_ARGS=-3"
    exit /b 0
)

python --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_EXE=python"
    exit /b 0
)

for /d %%D in ("%LocalAppData%\Programs\Python\Python3*") do (
    if exist "%%~fD\python.exe" set "PYTHON_EXE=%%~fD\python.exe"
)
exit /b 0

:find_npm
set "NPM_EXE="

node --version >nul 2>&1
if errorlevel 1 goto find_npm_in_program_files

for /f "delims=" %%I in ('where.exe node.exe 2^>nul') do (
    if not defined NPM_EXE if exist "%%~dpInpm.cmd" set "NPM_EXE=%%~dpInpm.cmd"
)

if defined NPM_EXE exit /b 0

:find_npm_in_program_files
if exist "%ProgramFiles%\nodejs\node.exe" if exist "%ProgramFiles%\nodejs\npm.cmd" (
    set "NPM_EXE=%ProgramFiles%\nodejs\npm.cmd"
)
exit /b 0

:require_winget
winget --version >nul 2>&1
if not errorlevel 1 exit /b 0

echo winget is unavailable, so %~1 cannot be installed automatically.
echo Install it from %~2 and run setup.bat again.
exit /b 1

:failed
echo.
echo Setup did not complete. Review the error above, then run setup.bat again.
exit /b 1
