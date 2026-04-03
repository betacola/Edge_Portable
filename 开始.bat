@echo off
chcp 65001 >nul

set "APP_DIR=%~dp0Edge"
set "EDGE_EXE="

:: 只遍历 Edge 文件夹
for /d %%d in ("%APP_DIR%\*") do (
    if exist "%%d\msedge.exe" (
        set "EDGE_EXE=%%d\msedge.exe"
        goto :found
    )
)

echo 未找到版本目录中的 msedge.exe
pause
exit /b 1

:found
powershell -NoProfile -ExecutionPolicy Bypass -Command "$s=New-Object -ComObject WScript.Shell; $l=$s.CreateShortcut('%~dp0Edge.lnk'); $l.TargetPath='%EDGE_EXE%'; $l.Arguments='--disable-background-networking'; $l.WorkingDirectory='%~dp0'; $l.IconLocation='%EDGE_EXE%,0'; $l.Save()"

if exist "%~dp0Edge.lnk" (
    echo 快捷方式创建成功
    echo 指向：%EDGE_EXE%
    exit /b 0
) else (
    echo 快捷方式创建失败
    pause
    exit /b 1
)
