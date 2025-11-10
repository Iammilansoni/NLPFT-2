@echo off
echo ========================================
echo NLPForge - Creating Page Files
echo ========================================
echo.

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo Creating page files from templates...
echo.

REM Dashboard page
if exist "src\app\dashboard\page.tsx" (
    echo [SKIP] dashboard\page.tsx already exists
) else (
    echo Creating dashboard\page.tsx...
    copy /Y "page-templates\dashboard-page.tsx" "src\app\dashboard\page.tsx" >nul 2>&1
    if exist "src\app\dashboard\page.tsx" (
        echo [OK] dashboard\page.tsx
    ) else (
        echo [MANUAL] Please copy dashboard code manually
    )
)

REM Query Runner page
if exist "src\app\run\new\page.tsx" (
    echo [SKIP] run\new\page.tsx already exists
) else (
    echo Creating run\new\page.tsx...
    copy /Y "page-templates\run-new-page.tsx" "src\app\run\new\page.tsx" >nul 2>&1
    if exist "src\app\run\new\page.tsx" (
        echo [OK] run\new\page.tsx
    ) else (
        echo [MANUAL] Please copy run/new code manually
    )
)

echo.
echo ========================================
echo Page Creation Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Restart your dev server (Ctrl+C then npm run dev)
echo 2. Visit http://localhost:3000/dashboard
echo 3. Visit http://localhost:3000/run/new
echo.
echo Note: If files were not created automatically,
echo check the page-templates folder for the code.
echo.
pause
