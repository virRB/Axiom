@echo off
setlocal EnableExtensions
title Axiom Installer

echo.
echo  ========================================
echo             AXIOM INSTALLER
echo  ========================================
echo.

where py >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python Launcher ^(py^) was not found.
    echo Install Python from https://www.python.org/downloads/
    echo Then run this installer again.
    goto :fail
)

echo [1/4] Checking Python...
py -c "import sys; print('Python:', sys.version.split()[0])"
if errorlevel 1 goto :fail

echo.
echo [2/4] Installing Axiom from PyPI...
py -m pip install --upgrade axiom-by-vir
if errorlevel 1 (
    echo ERROR: Axiom installation failed.
    goto :fail
)

echo.
echo [3/4] Locating the Axiom launcher...
for /f "delims=" %%P in ('py -c "import sys; print(sys.prefix)"') do set "PY_PREFIX=%%P"
set "SCRIPTS=%PY_PREFIX%\Scripts"
set "AXIOM_EXE=%SCRIPTS%\axiom.exe"

if not exist "%AXIOM_EXE%" (
    echo ERROR: Axiom was installed, but axiom.exe was not found at:
    echo "%AXIOM_EXE%"
    echo Check your Python installation and pip configuration.
    goto :fail
)

echo Found: "%AXIOM_EXE%"

echo.
echo [4/4] Adding Scripts directory to your user PATH...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
 "$scripts = $env:SCRIPTS; $current = [Environment]::GetEnvironmentVariable('Path', 'User');" ^
 "if ([string]::IsNullOrWhiteSpace($current)) { $current = '' };" ^
 "$parts = @($current -split ';' | Where-Object { $_.Trim() -ne '' });" ^
 "$exists = $false; foreach ($part in $parts) {" ^
 " if ([string]::Equals($part.Trim().TrimEnd('\'), $scripts.TrimEnd('\'), [StringComparison]::OrdinalIgnoreCase)) { $exists = $true }" ^
 "}; if (-not $exists) {" ^
 " if ($current -and -not $current.EndsWith(';')) { $current += ';' };" ^
 " $current += $scripts;" ^
 " [Environment]::SetEnvironmentVariable('Path', $current, 'User')" ^
 "}; Write-Output $(if ($exists) { 'Scripts directory already on user PATH.' } else { 'User PATH updated.' })"

if errorlevel 1 (
    echo WARNING: Could not update user PATH automatically.
    echo You can still run Axiom using its full executable path.
    goto :manual
)

echo.
echo ========================================
echo  AXIOM INSTALLED SUCCESSFULLY!
echo ========================================
echo.
echo Close this window and open a NEW PowerShell window.
echo Then run:
echo.
echo     axiom --help
echo.
echo If you have multiple Python installations, verify
echo that Axiom is installed in the intended environment.
echo.
pause
exit /b 0

:manual
echo.
echo Installer finished with a PATH warning.
echo Run Axiom directly using:
echo "%AXIOM_EXE%"
echo.
pause
exit /b 0

:fail
echo.
echo Installation did not complete successfully.
pause
exit /b 1