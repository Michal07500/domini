@echo off
rem Dvojklik = zapne color grade. Zavretie okna = vrati farby naspat.
start "" powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%~dp0ColorGrade.ps1"
