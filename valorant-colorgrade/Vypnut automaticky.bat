@echo off
rem Zrusi automaticke spustanie pri starte PC.
powershell -NoProfile -Command "Remove-Item (Join-Path ([Environment]::GetFolderPath('Startup')) 'Valorant Color Grade.lnk') -ErrorAction SilentlyContinue"
echo.
echo Automaticke spustanie je vypnute.
echo Ak ikonka v liste pri hodinach este bezi, klikni na nu pravym a daj Ukoncit.
echo.
pause
