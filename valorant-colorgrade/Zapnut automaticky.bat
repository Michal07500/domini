@echo off
rem Pri kazdom zapnuti PC sa potichu spusti Color Grade a caka na Valorant.
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
 "$lnk = Join-Path ([Environment]::GetFolderPath('Startup')) 'Valorant Color Grade.lnk';" ^
 "$s = (New-Object -ComObject WScript.Shell).CreateShortcut($lnk);" ^
 "$s.TargetPath = 'powershell.exe';" ^
 "$s.Arguments = '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File \"%~dp0ColorGrade.ps1\" -Auto';" ^
 "$s.WorkingDirectory = '%~dp0';" ^
 "$s.WindowStyle = 7;" ^
 "$s.Save()"
start "" powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%~dp0ColorGrade.ps1" -Auto
echo.
echo Hotovo. Color Grade sa teraz spusti sam pri kazdom zapnuti PC
echo a farby zapne vzdy, ked spustis Valorant.
echo Ikonku najdes v liste pri hodinach (mozno pod sipkou ^^).
echo.
pause
