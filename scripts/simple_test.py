#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单配置测试 - 无交互测试环境配置

使用方法:
    python scripts/simple_test.py
"""

import os
import sys
from pathlib import Path

# Windows编码处理
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目路径
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))


def test_env_file():
    """测试1: .env文件"""
    print("\n===== 测试1: .env文件 =====")
    env_file = root_dir / ".env"
    if env_file.exists():
        print("[OK] .env文件存在")
        return True
    else:
        print("[FAIL] .env文件不存在")
        return False


def test_dotenv():
    """测试2: python-dotenv"""
    print("\n===== 测试2: python-dotenv =====")
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("[OK] python-dotenv 可用")
        return True
    except ImportError:
        print("[FAIL] python-dotenv 未安装")
        print("[INFO] 安装: pip install python-dotenv")
        return False


def test_settings():
    """测试3: 配置加载"""
    print("\n===== 测试3: 配置加载 =====")
    try:
        from config.settings import settings
        print(f"[OK] APP_NAME: {settings.APP_NAME}")
        print(f"[OK] AI_PROVIDER: {settings.AI_PROVIDER}")
        print(f"[OK] CLAUDE_MODEL: {settings.CLAUDE_MODEL}")
        print(f"[OK] API_PORT: {settings.API_PORT}")
        
        if settings.CLAUDE_API_KEY:
            key_preview = settings.CLAUDE_API_KEY[:20] + "..."
            print(f"[OK] CLAUDE_API_KEY: {key_preview}")
        else:
            print("[WARN] CLAUDE_API_KEY 未设置")
        
        return True
    except Exception as e:
        print(f"[FAIL] 配置加载失败: {e}")
        return False


def test_anthropic():
    """测试4: anthropic包"""
    print("\n===== 测试4: anthropic包 =====")
    try:
        import anthropic
        print(f"[OK] anthropic 版本: {anthropic.__version__}")
        return True
    except ImportError:
        print("[FAIL] anthropic 未安装")
        print("[INFO] 安装: pip install anthropic")
        return False


def test_claude_api():
    """测试5: Claude API连接"""
    print("\n===== 测试5: Claude API连接 =====")
    try:
        import anthropic
        from config.settings import settings
        
        if not settings.CLAUDE_API_KEY:
            print("[SKIP] CLAUDE_API_KEY 未设置")
            return False
        
        print(f"[INFO] 正在连接 Claude API...")
        print(f"[INFO] 模型: {settings.CLAUDE_MODEL}")
        
        client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)
        
        message = client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=50,
            messages=[
                {"role": "user", "content": "请用一句话介绍你自己"}
            ]
        )
        
        response_text = message.content[0].text
        print(f"[OK] API调用成功!")
        print(f"[INFO] 响应: {response_text[:80]}...")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Claude API测试失败: {str(e)[:200]}")
        return False


def test_llm_generator():
    """测试6: LLM生成器"""
    print("\n===== 测试6: LLM生成器 =====")
    try:
        from core.generator.llm_generator import LLMGenerator
        
        print("[INFO] 初始化LLM生成器...")
        generator = LLMGenerator("test_game")
        
        print(f"[OK] AI Provider: {generator.ai_provider}")
        print(f"[OK] Model: {generator.model_name}")
        print(f"[OK] Max Tokens: {generator.max_tokens}")
        
        return True
    except Exception as e:
        print(f"[FAIL] LLM生成器初始化失败: {str(e)[:200]}")
        import traceback
        print(traceback.format_exc()[:500])
        return False


def main():
    """主函数"""
    print("="*60)
    print(" RAG游戏问答系统 - 环境配置简单测试")
    print("="*60)
    
    results = []
    
    # 运行所有测试
    results.append(("env_file", test_env_file()))
    results.append(("dotenv", test_dotenv()))
    results.append(("settings", test_settings()))
    results.append(("anthropic", test_anthropic()))
    results.append(("claude_api", test_claude_api()))
    results.append(("llm_generator", test_llm_generator()))
    
    # 总结
    print("\n" + "="*60)
    print(" 测试总结")
    print("="*60)
    
    passed = sum(1 for _, status in results if status)
    total = len(results)
    
    print(f"\n通过: {passed}/{total}")
    
    for name, status in results:
        status_text = "[OK]" if status else "[FAIL]"
        print(f"{status_text} {name}")
    
    print("\n" + "="*60)
    
    if passed >= 5:  # 至少5项通过
        print("[SUCCESS] 环境配置正常!")
        print("[INFO] 可以继续下一步操作")
    elif passed >= 3:
        print("[WARNING] 部分测试失败")
        print("[INFO] 核心功能可能可用，但建议检查失败项")
    else:
        print("[ERROR] 多项测试失败")
        print("[INFO] 请检查环境配置")
    
    print("="*60 + "\n")
    
    return passed >= 3


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n[INFO] 用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

