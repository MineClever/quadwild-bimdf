@echo off
setlocal EnableExtensions

set "ROOT_DIR=%~dp0"
if "%ROOT_DIR:~-1%"=="\" set "ROOT_DIR=%ROOT_DIR:~0,-1%"

set "CONFIG=Release"
set "BUILD_ROOT=%ROOT_DIR%\build"
set "BUILD_CLANG=%BUILD_ROOT%\windows-clangcl"
set "BUILD_DEFAULT=%BUILD_ROOT%\windows-default"
set "RELEASE_DIR=%ROOT_DIR%\release\windows"
set "BUILD_DIR="
set "CMAKE_EXE=cmake"
set "VS_CMAKE=H:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe"

if exist "%VS_CMAKE%" (
    set "CMAKE_EXE=%VS_CMAKE%"
)

if /I "%CMAKE_EXE%"=="cmake" (
    where cmake >nul 2>nul
    if errorlevel 1 (
        echo [ERROR] cmake was not found in PATH.
        exit /b 1
    )
)
if not exist "%CMAKE_EXE%" if /I not "%CMAKE_EXE%"=="cmake" (
    echo [ERROR] cmake was not found at %CMAKE_EXE%
    exit /b 1
)

echo [INFO] Repository root: %ROOT_DIR%
echo [INFO] Build configuration: %CONFIG%
echo [INFO] CMake executable: %CMAKE_EXE%

call :configure_clangcl
if not errorlevel 1 (
    set "BUILD_DIR=%BUILD_CLANG%"
    goto build
)

echo [WARN] ClangCl configure failed. Falling back to the default generator.
call :configure_default
if errorlevel 1 (
    echo [ERROR] Default generator configure failed.
    exit /b 1
)
set "BUILD_DIR=%BUILD_DEFAULT%"

:build
echo [INFO] Building from %BUILD_DIR%
"%CMAKE_EXE%" --build "%BUILD_DIR%" --config %CONFIG%
if errorlevel 1 (
    echo [ERROR] Build failed.
    exit /b 1
)

call :collect_outputs "%BUILD_DIR%"
if errorlevel 1 (
    echo [ERROR] Failed to collect runnable binaries.
    exit /b 1
)

echo [INFO] Build complete.
echo [INFO] Runnable output directory: %RELEASE_DIR%
exit /b 0

:configure_clangcl
echo [INFO] Configuring with ClangCl toolset...
if not exist "%BUILD_CLANG%" mkdir "%BUILD_CLANG%"
"%CMAKE_EXE%" -S "%ROOT_DIR%" -B "%BUILD_CLANG%" -T "ClangCl" -DSATSUMA_ENABLE_BLOSSOM5=0 -DCMAKE_INTERPROCEDURAL_OPTIMIZATION=ON > "%BUILD_CLANG%\configure.log" 2>&1
exit /b %errorlevel%

:configure_default
echo [INFO] Configuring with the default generator...
"%CMAKE_EXE%" -S "%ROOT_DIR%" -B "%BUILD_DEFAULT%" -DSATSUMA_ENABLE_BLOSSOM5=0 -DCMAKE_INTERPROCEDURAL_OPTIMIZATION=ON
exit /b %errorlevel%

:collect_outputs
set "SOURCE_BUILD_DIR=%~1"
set "BIN_DIR=%SOURCE_BUILD_DIR%\Build\bin\%CONFIG%"
if not exist "%BIN_DIR%\quadwild.exe" set "BIN_DIR=%SOURCE_BUILD_DIR%\Build\bin"

if not exist "%BIN_DIR%\quadwild.exe" (
    echo [ERROR] quadwild.exe was not found under %SOURCE_BUILD_DIR%\Build\bin
    exit /b 1
)

"%CMAKE_EXE%" -E make_directory "%RELEASE_DIR%"
if errorlevel 1 exit /b 1

if exist "%RELEASE_DIR%\config" (
    rmdir /s /q "%RELEASE_DIR%\config"
    if errorlevel 1 exit /b 1
)

"%CMAKE_EXE%" -E copy_directory "%ROOT_DIR%\config" "%RELEASE_DIR%\config"
if errorlevel 1 exit /b 1

"%CMAKE_EXE%" -E copy "%ROOT_DIR%\README_release.md" "%RELEASE_DIR%\README_release.md"
if errorlevel 1 exit /b 1

"%CMAKE_EXE%" -E copy "%BIN_DIR%\quadwild.exe" "%RELEASE_DIR%\quadwild.exe"
if errorlevel 1 exit /b 1

if exist "%BIN_DIR%\quad_from_patches.exe" (
    "%CMAKE_EXE%" -E copy "%BIN_DIR%\quad_from_patches.exe" "%RELEASE_DIR%\quad_from_patches.exe"
    if errorlevel 1 exit /b 1
)

if exist "%BIN_DIR%\cli_trace.exe" (
    "%CMAKE_EXE%" -E copy "%BIN_DIR%\cli_trace.exe" "%RELEASE_DIR%\cli_trace.exe"
    if errorlevel 1 exit /b 1
)

if exist "%BIN_DIR%\viz_mesh_results.exe" (
    "%CMAKE_EXE%" -E copy "%BIN_DIR%\viz_mesh_results.exe" "%RELEASE_DIR%\viz_mesh_results.exe"
    if errorlevel 1 exit /b 1
)

exit /b 0
