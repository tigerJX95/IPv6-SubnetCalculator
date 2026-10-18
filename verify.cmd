@echo off
rem SPDX-License-Identifier: GPL-3.0-or-later
rem Copyright (C) 2026 IPv6SubnetCalculator contributors
setlocal
cd /d "%~dp0"
set "IPV6_VERIFY_APP=IPv6SubnetCalculator_V1.1"
if not exist "dist\%IPV6_VERIFY_APP%.exe" (
  echo Please run build.cmd first, then run verify.cmd again.
  pause
  exit /b 1
)
where py >nul 2>&1
if not errorlevel 1 (
  set "IPV6_VERIFY_PYTHON=py -3"
) else (
  set "IPV6_VERIFY_PYTHON=python"
)
%IPV6_VERIFY_PYTHON% tools\verify.py --exe "dist\%IPV6_VERIFY_APP%.exe" --report-dir verification
set "IPV6_VERIFY_EXIT=%ERRORLEVEL%"
echo.
echo Reports: verification\SUMMARY.md and verification\summary.json
pause
exit /b %IPV6_VERIFY_EXIT%
