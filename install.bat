@echo off
rem Install the ImageStudio generation skill to the current user's skills dir.
setlocal
set "SRC=%~dp0"
set "DEST=%USERPROFILE%\.agents\skills\imagestudio"

echo [imagestudio-skill] Installing to %DEST%
if not exist "%DEST%\scripts" mkdir "%DEST%\scripts"
copy /y "%SRC%SKILL.md" "%DEST%\SKILL.md" >nul
copy /y "%SRC%scripts\imagestudio_image_gen.py" "%DEST%\scripts\imagestudio_image_gen.py" >nul

echo [imagestudio-skill] Done. Configure your member key (optional, env IMAGESTUDIO_API_KEY also works):
echo   %USERPROFILE%\.imagestudio\config.json
echo   {"base_url": "http://127.0.0.1:8020", "api_key": "sk-your-member-key"}
endlocal
