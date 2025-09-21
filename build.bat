REM Build Tracker.py into .exe, it will appear in new Builds folder

pyinstaller --onefile --distpath "Builds" --clean Tracker.py
rmdir /s /q build
del /q Tracker.spec