@echo off
REM test/run_pe_test.bat - Windows batch file to run P/E tests

echo ======================================
echo Stock Analysis P/E Test Suite
echo ======================================
echo.

REM Check if we're in the right directory
if not exist "app.py" (
    echo ERROR: Cannot find app.py
    echo Please run this from your project root directory
    echo Current directory: %CD%
    pause
    exit /b 1
)

echo ✓ Found app.py - running from correct directory
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found
    echo Please install Python and ensure it's in your PATH
    pause
    exit /b 1
)

echo ✓ Python is available
echo.

REM Check if test directory exists
if not exist "test" (
    echo ERROR: test directory not found
    echo Please create the test directory with the test files
    pause
    exit /b 1
)

echo ✓ Test directory found
echo.

REM Run the simple P/E test (standalone, no complex imports)
echo Running Simple P/E Test...
echo ======================================
python test/simple_pe_test.py

echo.
echo ======================================
echo Test completed!
echo.

REM Check if detailed results file was created
for %%f in (test/simple_pe_test_results_*.json) do (
    echo Results saved to: %%f
    goto :found_results
)

echo No results file found
:found_results

echo.
echo Press any key to exit...
pause >nul