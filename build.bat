@echo off

pip install -r requirements.txt

pip install pyinstaller

pyinstaller ^
--onefile ^
--windowed ^
--name GDriveMounter ^
main.py

pause