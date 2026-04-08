@echo off
echo Running local checks...

echo.
echo === Running tests ===
python -m pytest tests/ -x --tb=short
if %ERRORLEVEL% NEQ 0 (
    echo Tests failed!
    exit /b 1
)

echo.
echo === Running black format auto-fix ===
black .
if %ERRORLEVEL% NEQ 0 (
    echo Black formatting failed!
    exit /b 1
)

echo.
echo === Running mypy type check ===
cd src
mypy LStartlet
if %ERRORLEVEL% NEQ 0 (
    echo MyPy type check failed!
    exit /b 1
)
cd ..

echo.
echo All checks passed! Ready to commit.