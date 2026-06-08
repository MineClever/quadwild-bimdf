@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "ROOT_DIR=%~dp0"
if "%ROOT_DIR:~-1%"=="\" set "ROOT_DIR=%ROOT_DIR:~0,-1%"

set "CONFIG=Release"
set "BUILD_ROOT=%ROOT_DIR%\build"
set "BUILD_CLANG=%BUILD_ROOT%\windows-clangcl"
set "BUILD_DEFAULT=%BUILD_ROOT%\windows-default"
set "RELEASE_DIR=%ROOT_DIR%\release\windows"
set "BUILD_DIR="
set "CMAKE_EXE="

call :find_vs_cmake
if defined CMAKE_EXE (
    echo [INFO] Visual Studio CMake detected: %CMAKE_EXE%
) else (
    set "CMAKE_EXE=cmake"
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

:find_vs_cmake
set "CMAKE_EXE="
call :probe_vs_cmake_powershell
if defined CMAKE_EXE exit /b 0
call :probe_vs_uninstall_cmake "HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
if defined CMAKE_EXE exit /b 0
call :probe_vs_uninstall_cmake "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
if defined CMAKE_EXE exit /b 0
call :probe_vs_cmake_setup_key "HKLM\SOFTWARE\Microsoft\VisualStudio\17.0\Setup\rdbgwiz"
if defined CMAKE_EXE exit /b 0
call :probe_vs_cmake_setup_key "HKLM\SOFTWARE\Microsoft\VisualStudio\16.9\Setup\rdbgwiz"
if defined CMAKE_EXE exit /b 0
call :probe_vs_cmake_setup_key "HKLM\SOFTWARE\Microsoft\VisualStudio\16.0\Setup\rdbgwiz"
if defined CMAKE_EXE exit /b 0
call :probe_vs_cmake_setup_key "HKLM\SOFTWARE\Microsoft\VisualStudio\15.0\Setup\rdbgwiz"
if defined CMAKE_EXE exit /b 0
call :probe_vs_cmake_setup_key "HKLM\SOFTWARE\WOW6432Node\Microsoft\VisualStudio\17.0\Setup\rdbgwiz"
if defined CMAKE_EXE exit /b 0
call :probe_vs_cmake_setup_key "HKLM\SOFTWARE\WOW6432Node\Microsoft\VisualStudio\16.9\Setup\rdbgwiz"
if defined CMAKE_EXE exit /b 0
call :probe_vs_cmake_setup_key "HKLM\SOFTWARE\WOW6432Node\Microsoft\VisualStudio\16.0\Setup\rdbgwiz"
if defined CMAKE_EXE exit /b 0
call :probe_vs_cmake_setup_key "HKLM\SOFTWARE\WOW6432Node\Microsoft\VisualStudio\15.0\Setup\rdbgwiz"
if defined CMAKE_EXE exit /b 0
call :probe_vs_cmake_key "HKLM\SOFTWARE\Microsoft\VisualStudio\SxS\VS7" "17.0"
if defined CMAKE_EXE exit /b 0
call :probe_vs_cmake_key "HKLM\SOFTWARE\Microsoft\VisualStudio\SxS\VS7" "16.0"
if defined CMAKE_EXE exit /b 0
call :probe_vs_cmake_key "HKLM\SOFTWARE\Microsoft\VisualStudio\SxS\VS7" "15.0"
if defined CMAKE_EXE exit /b 0
call :probe_vs_cmake_key "HKLM\SOFTWARE\WOW6432Node\Microsoft\VisualStudio\SxS\VS7" "17.0"
if defined CMAKE_EXE exit /b 0
call :probe_vs_cmake_key "HKLM\SOFTWARE\WOW6432Node\Microsoft\VisualStudio\SxS\VS7" "16.0"
if defined CMAKE_EXE exit /b 0
call :probe_vs_cmake_key "HKLM\SOFTWARE\WOW6432Node\Microsoft\VisualStudio\SxS\VS7" "15.0"
exit /b 0

:probe_vs_cmake_powershell
for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "$roots = @('HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall','HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall'); foreach ($root in $roots) { foreach ($key in Get-ChildItem -Path $root -ErrorAction SilentlyContinue) { $item = Get-ItemProperty $key.PSPath -ErrorAction SilentlyContinue; if ($item.DisplayName -like 'Visual Studio*2022*' -and $item.InstallLocation) { $candidate = Join-Path $item.InstallLocation 'Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe'; if (Test-Path $candidate) { Write-Output $candidate; break } } } }"`) do (
    set "CMAKE_EXE=%%I"
    goto :eof
)

exit /b 0

:probe_vs_uninstall_cmake
set "VS_UNINSTALL_ROOT_KEY=%~1"

for /f "tokens=1,2,*" %%A in ('reg query "%VS_UNINSTALL_ROOT_KEY%" /s /f "Visual Studio 2022" 2^>nul') do (
    if /I "%%A"=="InstallLocation" (
        set "VS_INSTALL_ROOT=%%C"
        call :check_vs_cmake_path
        if defined CMAKE_EXE exit /b 0
    )
)

exit /b 0

:probe_vs_cmake_setup_key
set "VS_SETUP_KEY=%~1"
set "VS_SETUP_PATH="

for /f "tokens=1,2,*" %%A in ('reg query "%VS_SETUP_KEY%" /ve 2^>nul') do (
    if /I "%%A"=="(Default)" (
        set "VS_SETUP_PATH=%%C"
    )
)

if not defined VS_SETUP_PATH exit /b 0

set "VS_SETUP_PATH=%VS_SETUP_PATH:"=%"
set "VS_INSTALL_ROOT=%VS_SETUP_PATH:\Common7\IDE\rdbgwiz.exe=%"

if not "%VS_INSTALL_ROOT%"=="%VS_SETUP_PATH%" (
    call :check_vs_cmake_path
)

exit /b 0

:probe_vs_cmake_key
set "VS_REG_KEY=%~1"
set "VS_REG_VALUE=%~2"
set "VS_INSTALL_ROOT="

for /f "tokens=1,2,*" %%A in ('reg query "%VS_REG_KEY%" /v "%VS_REG_VALUE%" 2^>nul') do (
    if /I "%%A"=="%VS_REG_VALUE%" (
        set "VS_INSTALL_ROOT=%%C"
    )
)

if not defined VS_INSTALL_ROOT exit /b 0

call :check_vs_cmake_path

exit /b 0

:check_vs_cmake_path
if not defined VS_INSTALL_ROOT exit /b 0

set "VS_CMAKE_DIR=%VS_INSTALL_ROOT%\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin"
if exist "%VS_CMAKE_DIR%\cmake.exe" (
    set "CMAKE_EXE=%VS_CMAKE_DIR%\cmake.exe"
)

exit /b 0
