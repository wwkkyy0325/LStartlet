@echo off
echo Running local checks...

echo.
echo === Running tests ===
python tests/run_tests.py
if %ERRORLEVEL% NEQ 0 (
    echo Tests failed!
    exit /b 1
)

echo.
echo === Running black format check ===
black --check --diff .
if %ERRORLEVEL% NEQ 0 (
    echo Black formatting failed! Run 'black .' to fix.
    exit /b 1
)

echo.
echo === Running mypy type check ===
mypy .
if %ERRORLEVEL% NEQ 0 (
    echo MyPy type check failed!
    exit /b 1
)

echo.
echo All checks passed! Ready to commit.