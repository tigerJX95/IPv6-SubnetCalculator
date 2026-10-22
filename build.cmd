@echo off
rem SPDX-License-Identifier: GPL-3.0-or-later
rem Copyright (C) 2026 IPv6SubnetCalculator contributors
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if not errorlevel 1 (
  set "IPV6_PYTHON=py -3"
) else (
  set "IPV6_PYTHON=python"
)
%IPV6_PYTHON% -c "import sys; assert sys.version_info >= (3,10), 'Python 3.10 or newer is required'" || goto fail
set "IPV6_APP_VERSION="
for /f "delims=" %%V in ('%IPV6_PYTHON% -c "from app_info import APP_VERSION; print(APP_VERSION)"') do set "IPV6_APP_VERSION=%%V"
if not defined IPV6_APP_VERSION goto fail
set "IPV6_APP_NAME=IPv6SubnetCalculator_V%IPV6_APP_VERSION%"
%IPV6_PYTHON% -m pip install -r requirements.txt || goto fail
%IPV6_PYTHON% -m pip install --upgrade "pyinstaller>=6.22.3,<7" || goto fail
%IPV6_PYTHON% tools\build_manifest.py || goto fail
%IPV6_PYTHON% -m PyInstaller --noconfirm --clean --onefile --windowed ^
 --name "%IPV6_APP_NAME%" --icon app.ico ^
 --add-data "build_manifest.json;." ^
 --add-data "app.ico;." --add-data "assets;assets" ^
 --add-data "LICENSE;." --add-data "NOTICE;." ^
 --add-data "THIRD_PARTY_NOTICES.md;." --add-data "docs/licenses;docs/licenses" ^
 --add-data "docs/about;docs/about" ^
 --copy-metadata PyQt6 --copy-metadata PyQt6-Qt6 --copy-metadata PyQt6-sip ^
 --exclude-module tkinter --exclude-module PyQt5 --exclude-module PySide2 --exclude-module PySide6 ^
 main.py || goto fail
if not exist "dist\%IPV6_APP_NAME%.exe" goto fail
if not exist "dist\%IPV6_APP_NAME%_Licenses" mkdir "dist\%IPV6_APP_NAME%_Licenses" || goto fail
copy /y LICENSE "dist\%IPV6_APP_NAME%_Licenses\LICENSE" >nul || goto fail
copy /y NOTICE "dist\%IPV6_APP_NAME%_Licenses\NOTICE" >nul || goto fail
copy /y THIRD_PARTY_NOTICES.md "dist\%IPV6_APP_NAME%_Licenses\THIRD_PARTY_NOTICES.md" >nul || goto fail
xcopy /e /i /y "docs\licenses" "dist\%IPV6_APP_NAME%_Licenses\docs\licenses" >nul || goto fail
echo.
echo Keep the matching source and license files with your release.
echo Build completed: dist\%IPV6_APP_NAME%.exe
echo Optional ZIP: python tools\package_release.py
pause
exit /b 0
:fail
echo.
echo Build failed. Please check Python installation and the errors above.
pause
exit /b 1
