@echo off
chcp 65001
echo ========================================================
echo          正在开始打包 ZenFile (v1.0.0)...
echo ========================================================

:: 1. 清理旧的构建文件 (防止缓存导致的问题)
if exist "build" (
    echo [1/3] 正在清理 build 文件夹...
    rmdir /s /q "build"
)
if exist "dist" (
    echo [2/3] 正在清理 dist 文件夹...
    rmdir /s /q "dist"
)
if exist "*.spec" (
    del /f /q "*.spec"
)

:: 2. 执行 PyInstaller 打包命令
echo [3/3] 正在执行 PyInstaller...
echo.

pyinstaller -F -w -n ZenFile ^
    --icon="assets\icons\logo.ico" ^
    --add-data="assets;assets" ^
    --hidden-import pynput.keyboard._win32 ^
    --hidden-import pynput.mouse._win32 ^
    --hidden-import tkinter ^
main.py

:: 3. 完成提示
if %errorlevel% equ 0 (
    echo.
    echo ========================================================
    echo             ✅ 打包成功！
    echo      可执行文件位置: dist\ZenFile.exe
    echo ========================================================
    :: 自动打开生成目录
    start explorer dist
) else (
    echo.
    echo ========================================================
    echo             ❌ 打包失败，请检查错误信息。
    echo ========================================================
    pause
)

pause