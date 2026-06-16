@echo off

call ..\build.bat

if not exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    echo Inno Setup 6 not found.
    echo Install from https://jrsoftware.org/isinfo.php
    pause
    exit /b 1
)

"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" setup.iss

pause
