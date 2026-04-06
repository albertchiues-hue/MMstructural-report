@echo off
REM ============================================================
REM   PRINT ALL PDFs (2 copies each)
REM   Just double-click this file to print!
REM ============================================================

REM Get the folder where this file lives
set "SCRIPT_DIR=%~dp0"

REM Count PDF files
set COUNT=0
for %%F in ("%SCRIPT_DIR%*.pdf") do set /a COUNT+=1

REM If no PDFs found, show error and exit
if %COUNT%==0 (
    powershell -Command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.MessageBox]::Show('No PDF files were found in this folder.', 'PDF Printer - Error', 'OK', 'Error')"
    exit /b
)

REM Build a list of filenames to show the user
set "FILE_LIST="
for %%F in ("%SCRIPT_DIR%*.pdf") do (
    if defined FILE_LIST (
        set "FILE_LIST=!FILE_LIST!, %%~nxF"
    ) else (
        set "FILE_LIST=%%~nxF"
    )
)

REM Enable delayed expansion for the file list
setlocal EnableDelayedExpansion

REM Ask user to confirm before printing
powershell -Command "Add-Type -AssemblyName System.Windows.Forms; $result = [System.Windows.Forms.MessageBox]::Show('Found %COUNT% PDF file(s):`n`n!FILE_LIST!`n`nThis will print 2 COPIES of each to your default printer.`n`nContinue?', 'PDF Printer', 'YesNo', 'Question'); if ($result -eq 'No') { exit 1 }"
if %ERRORLEVEL% NEQ 0 (
    endlocal
    exit /b
)

REM Print each PDF twice
set CURRENT=0
for %%F in ("%SCRIPT_DIR%*.pdf") do (
    set /a CURRENT+=1

    REM Copy 1
    echo Printing copy 1 of 2: %%~nxF
    start /min "" "%%F" /print
    timeout /t 3 /nobreak >nul

    REM Copy 2
    echo Printing copy 2 of 2: %%~nxF
    start /min "" "%%F" /print
    timeout /t 3 /nobreak >nul
)

endlocal

REM Show success message
powershell -Command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.MessageBox]::Show('Done! Sent %COUNT% PDF file(s) to the printer (2 copies each).', 'PDF Printer - Complete', 'OK', 'Information')"
