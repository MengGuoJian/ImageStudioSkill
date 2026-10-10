@echo off
rem Install the ImageStudio generation skill to the current user's skills dir.
setlocal
set "SRC=%~dp0"
set "DEST=%USERPROFILE%\.agents\skills\imagestudio"

echo [imagestudio-skill] Installing to %DEST%
if not exist "%DEST%\scripts" mkdir "%DEST%\scripts"
copy /y "%SRC%SKILL.md" "%DEST%\SKILL.md" >nul
copy /y "%SRC%README.md" "%DEST%\README.md" >nul
copy /y "%SRC%scripts\imagestudio_image_gen.py" "%DEST%\scripts\imagestudio_image_gen.py" >nul

echo [imagestudio-skill] Done. Start ImageStudio and run the script with --check.
endlocal
