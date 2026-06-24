@echo off

REM Auto-detect ArcGIS Python folder in C:\Python27
set "ARCGIS_DIR="

REM Find first ArcGIS directory inside C:\Python27
for /d %%i in ("C:\Python27\ArcGIS*") do (
    set "ARCGIS_DIR=%%~nxi"
    goto :found_arcgis_dir
)

:found_arcgis_dir

if "%ARCGIS_DIR%"=="" (
    echo ERROR: No ArcGIS directory found in C:\Python27
    echo Please install ArcGIS Desktop or ArcGIS Pro with Python 2.7 support
    echo.
    pause
    exit /b 1
)

REM Construct the full path
set "ARCGIS_PYTHON=C:\Python27\%ARCGIS_DIR%"

REM Verify python.exe exists
if not exist "%ARCGIS_PYTHON%\python.exe" (
    echo ERROR: python.exe not found in %ARCGIS_PYTHON%
    pause
    exit /b 1
)

REM Reset PATH completely - start with detected ESRI Python only
set PATH=%ARCGIS_PYTHON%;%ARCGIS_PYTHON%\Scripts

REM Add essential Windows directories
set PATH=%PATH%;C:\Windows\system32
set PATH=%PATH%;C:\Windows
set PATH=%PATH%;C:\Windows\System32\Wbem
set PATH=%PATH%;C:\Windows\System32\WindowsPowerShell\v1.0

REM Add common program directories if they exist
if exist "C:\Program Files\Git\cmd" set PATH=%PATH%;C:\Program Files\Git\cmd
if exist "C:\Program Files\dotnet" set PATH=%PATH%;C:\Program Files\dotnet
if exist "C:\Program Files (x86)\Git\cmd" set PATH=%PATH%;C:\Program Files (x86)\Git\cmd

echo | set /p="Python Version: "
python --version
echo | set /p="ArcPy Status: "
python -c "import arcpy; print('Available - Version:', arcpy.GetInstallInfo()['Version'])" 2>nul || echo Not available
echo Environment Ready!
echo.

REM Keep CMD open for further commands
cmd /k