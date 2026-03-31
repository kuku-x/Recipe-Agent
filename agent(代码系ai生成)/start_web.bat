@echo off
chcp 65001 >nul
echo ========================================
echo 🍳 AI菜谱知识图谱生成器 - Web服务器
echo ========================================
echo.

echo 正在检查依赖...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo ❌ 依赖安装失败，请检查网络连接
    pause
    exit /b 1
)

echo.
echo ✅ 依赖安装完成
echo.
echo 正在启动Web服务器...
echo.
echo 🌐 请在浏览器中打开: http://localhost:5000
echo.
echo 按 Ctrl+C 停止服务器
echo ========================================
echo.

python web_server.py

pause