@echo off
rem SPDX-License-Identifier: GPL-3.0-or-later
rem Copyright (C) 2026 IPv6SubnetCalculator contributors
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if not errorlevel 1 (
  set "IPV6_VERIFY_PYTHON=py -3"
) else (
  set "IPV6_VERIFY_PYTHON=python"
)
set "IPV6_VERIFY_VERSION="
for /f "delims=" %%V in ('%IPV6_VERIFY_PYTHON% -c "from app_info import APP_VERSION; print(APP_VERSION)"') do set "IPV6_VERIFY_VERSION=%%V"
if not defined IPV6_VERIFY_VERSION (
  echo Cannot read APP_VERSION. Please check Python and app_info.py.
  pause
  exit /b 1
)
set "IPV6_VERIFY_APP=IPv6SubnetCalculator_V%IPV6_VERIFY_VERSION%"
if not exist "dist\%IPV6_VERIFY_APP%.exe" (
  echo Please run build.cmd first, then run verify.cmd again.
  echo Expected executable: dist\%IPV6_VERIFY_APP%.exe
  pause
  exit /b 1
)
%IPV6_VERIFY_PYTHON% tools\verify.py --exe "dist\%IPV6_VERIFY_APP%.exe" --report-dir verification
set "IPV6_VERIFY_EXIT=%ERRORLEVEL%"
echo.
echo Reports: verification\SUMMARY.md and verification\summary.json
pause
exit /b %IPV6_VERIFY_EXIT%
