#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
启动RAG游戏问答系统服务器

使用方法:
    python run_server.py
"""

import sys
import os
from pathlib import Path

# Windows编码处理
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目根目录到路径
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

print("="*60)
print("  RAG游戏问答系统 - 启动服务器")
print("="*60)

try:
    # 检查配置
    print("\n[INFO] 正在检查配置...")
    from config.settings import settings
    
    print(f"[OK] APP_NAME: {settings.APP_NAME}")
    print(f"[OK] VERSION: {settings.APP_VERSION}")
    print(f"[OK] AI_PROVIDER: {settings.AI_PROVIDER}")
    print(f"[OK] HOST: {settings.API_HOST}")
    print(f"[OK] PORT: {settings.API_PORT}")
    
    # 启动服务
    print(f"\n[INFO] 正在启动服务...")
    print(f"[INFO] 地址: http://{settings.API_HOST}:{settings.API_PORT}")
    print(f"[INFO] 文档: http://localhost:{settings.API_PORT}/docs")
    print(f"[INFO] 健康检查: http://localhost:{settings.API_PORT}/health")
    print("\n" + "-"*60)
    print("[INFO] 按 Ctrl+C 停止服务")
    print("-"*60 + "\n")
    
    import uvicorn
    from api.main import app
    
    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        log_level=settings.LOG_LEVEL.lower()
    )
    
except KeyboardInterrupt:
    print("\n\n[INFO] 服务已停止")
    sys.exit(0)
    
except Exception as e:
    print(f"\n[ERROR] 启动失败: {e}")
    print("\n[TIPS] 请检查:")
    print("  1. 依赖是否安装: pip install -r requirements.txt")
    print("  2. .env文件是否存在")
    print("  3. 配置是否正确")
    print("\n运行测试诊断:")
    print("  python scripts/simple_test.py")
    
    import traceback
    print("\n详细错误:")
    traceback.print_exc()
    sys.exit(1)

