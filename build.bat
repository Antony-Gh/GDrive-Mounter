@echo off

pip install -r requirements.txt

pip install pyinstaller

set ICON_ARG=
if exist resources\icon.ico (
    set ICON_ARG=--icon resources\icon.ico
)

pyinstaller ^
--onefile ^
--windowed ^
%ICON_ARG% ^
--name GDriveMounter ^
--add-data "resources;resources" ^
main.py

pause
