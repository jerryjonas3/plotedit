@echo off
rem Start plotedit. Double-click this file on Windows.
rem
rem The Mac and Linux twin is run.command. Everything it does is reversible and
rem stays inside this folder: it makes a .venv here, installs the Python
rem packages into THAT, and starts a server on your own machine. It touches no
rem system Python and installs nothing globally.
setlocal enabledelayedexpansion
pushd "%~dp0"

rem --- Python ---------------------------------------------------------------
rem The py launcher ships with the python.org installer and is the reliable way
rem to find a version; plain "python" on Windows is often the Microsoft Store
rem stub, which opens the Store instead of running anything.
set "PY="
for %%C in ("py -3.12" "py -3.11" "py -3" "python") do (
  %%~C -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
  if !errorlevel! equ 0 (
    if "!PY!"=="" set "PY=%%~C"
  )
)
if "%PY%"=="" (
  echo.
  echo   plotedit needs Python 3.10 or newer.
  echo   Install it from https://www.python.org/downloads/
  echo   and tick "Add python.exe to PATH" in the installer.
  echo.
  pause
  exit /b 1
)

rem --- dependencies, in a folder of our own ---------------------------------
if not exist ".venv\Scripts\python.exe" (
  echo.
  echo   First run - setting up. This takes a minute, and only happens once.
  %PY% -m venv .venv || goto :failed
)
call ".venv\Scripts\activate.bat" || goto :failed
python -m pip install --quiet --upgrade pip || goto :failed
python -m pip install --quiet -r server\requirements.txt || goto :failed

rem --- the editor -----------------------------------------------------------
rem A release download already has web\dist. A clone of the repository does not.
if not exist "web\dist\index.html" (
  where npm >nul 2>&1
  if errorlevel 1 (
    echo.
    echo   The editor has not been built, and Node is not installed.
    echo   Either download a release ^(which has it built already^),
    echo   or install Node from https://nodejs.org and run this again.
    echo.
    pause
    exit /b 1
  )
  echo.
  echo   Building the editor ^(first run only^)...
  pushd web
  call npm install --silent || (popd ^& goto :failed)
  call npm run build || (popd ^& goto :failed)
  popd
)

echo.
echo   Starting plotedit - your browser will open in a moment.
echo   Leave this window open while you work. Close it, or press Ctrl-C, to stop.
echo.
python server\serve.py
set "RC=!errorlevel!"
popd
rem A server that falls over must not take its message with it. Every failure
rem above this line pauses; without this one, a crash at STARTUP - port 8000 already
rem in use is the common cause - closed the window on an empty screen and left the
rem person with nothing to report. A Mac keeps the traceback in the Terminal; here
rem the window is the only place it ever existed.
if not "!RC!"=="0" (
  echo.
  echo   plotedit stopped with an error. The message above says why.
  echo.
  echo   If it mentions the address already being in use, plotedit is already
  echo   running in another window. Use that one, or start this on another port:
  echo       set PLOTEDIT_PORT=8010 ^&^& run.bat
  echo.
  pause
)
exit /b !RC!

:failed
echo.
echo   Setup failed. The message above says why.
echo.
pause
exit /b 1
