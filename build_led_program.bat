@echo off
echo LED-Irányító 2000 újraépítése .exe formátumba...

cd /d "C:\Users\vatib\Projects"

"C:\Users\vatib\AppData\Local\Programs\Python\Python313\python.exe" -m PyInstaller --onefile --noconsole --icon=led_icon.ico led-program.py

echo.
echo ✅ Kész! Az .exe elérhető itt: C:\Users\vatib\Projects\dist\led-program.exe
pause
