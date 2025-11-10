@echo off
echo ========================================
echo NLPForge Frontend - Package Installation
echo ========================================
echo.

echo Installing missing Radix UI component...
call npm install @radix-ui/react-scroll-area

echo.
echo Installing development dependencies...
call npm install --save-dev msw @storybook/addon-interactions @storybook/testing-library

echo.
echo Installing optional monitoring packages...
set /p install_monitoring="Install Sentry and PostHog? (y/n): "
if /i "%install_monitoring%"=="y" (
    call npm install @sentry/nextjs posthog-js
    echo Monitoring packages installed!
) else (
    echo Skipping monitoring packages.
)

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Run 'npm run dev' to start the development server
echo 2. Check IMPLEMENTATION_STATUS.md for progress
echo 3. Review COMPLETE_IMPLEMENTATION_GUIDE.md for detailed docs
echo.
pause
