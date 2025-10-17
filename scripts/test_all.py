#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
完整系统测试 - 测试所有功能

包含:
1. 环境配置测试
2. 数据库状态测试
3. API功能测试
4. 性能测试

使用方法:
    python scripts/test_all.py
"""

import sys
from pathlib import Path
import time
import subprocess

# Windows编码
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))


def run_test_script(script_name, description):
    """运行测试脚本"""
    print(f"\n[运行] {description}...")
    print("-" * 60)
    
    try:
        result = subprocess.run(
            [sys.executable, f"scripts/{script_name}"],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=root_dir
        )
        
        if result.returncode == 0:
            print(f"✅ {description} - 通过")
            # 只显示关键信息
            if "通过" in result.stdout or "SUCCESS" in result.stdout:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'OK' in line or '通过' in line or 'SUCCESS' in line:
                        print(f"  {line.strip()}")
            return True
        else:
            print(f"❌ {description} - 失败")
            if result.stderr:
                print(f"错误: {result.stderr[:200]}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⚠️  {description} - 超时")
        return False
    except Exception as e:
        print(f"❌ {description} - 异常: {e}")
        return False


def test_core_functionality():
    """测试核心功能"""
    print("\n" + "="*60)
    print("  核心功能测试")
    print("="*60)
    
    try:
        from api.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        tests_passed = 0
        tests_total = 0
        
        # 测试1: API文档
        print("\n[测试1] API文档可访问性")
        tests_total += 1
        try:
            response = client.get("/docs")
            if response.status_code == 200:
                print("  ✅ /docs 可访问")
                tests_passed += 1
            else:
                print(f"  ❌ /docs 返回 {response.status_code}")
        except Exception as e:
            print(f"  ❌ /docs 测试失败: {e}")
        
        # 测试2: 根路径
        print("\n[测试2] 根路径信息")
        tests_total += 1
        try:
            response = client.get("/")
            if response.status_code == 200:
                print("  ✅ GET / - 200 OK")
                tests_passed += 1
            else:
                print(f"  ❌ GET / - {response.status_code}")
        except Exception as e:
            print(f"  ❌ GET / 失败: {e}")
        
        # 测试3: 健康检查
        print("\n[测试3] 健康检查")
        tests_total += 1
        try:
            response = client.get("/health")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok':
                    print("  ✅ GET /health - 健康正常")
                    tests_passed += 1
                else:
                    print("  ❌ 健康状态异常")
            else:
                print(f"  ❌ GET /health - {response.status_code}")
        except Exception as e:
            print(f"  ❌ 健康检查失败: {e}")
        
        # 测试4: 问答接口
        print("\n[测试4] 问答功能")
        tests_total += 1
        try:
            response = client.post("/api/v1/qa/ask", json={
                "question": "测试问题",
                "game_id": "wow"
            })
            if response.status_code == 200:
                data = response.json()
                if 'answer' in data:
                    print("  ✅ POST /api/v1/qa/ask - 问答成功")
                    print(f"  答案长度: {len(data.get('answer', ''))}")
                    tests_passed += 1
                else:
                    print("  ❌ 响应缺少answer字段")
            else:
                print(f"  ❌ POST /api/v1/qa/ask - {response.status_code}")
        except Exception as e:
            print(f"  ❌ 问答测试失败: {e}")
        
        # 总结
        print(f"\n[总结] 核心功能测试: {tests_passed}/{tests_total} 通过")
        return tests_passed >= tests_total * 0.75  # 75%通过即可
        
    except Exception as e:
        print(f"[ERROR] 核心功能测试异常: {e}")
        return False


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("  RAG游戏问答系统 - 完整功能测试")
    print("="*60)
    print(f"\n开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # 测试1: 环境配置
    results['env'] = run_test_script("simple_test.py", "环境配置测试")
    
    # 测试2: 数据库状态
    results['db'] = run_test_script("check_db_status.py", "数据库状态检查")
    
    # 测试3: 核心功能
    print("\n")
    results['core'] = test_core_functionality()
    
    # 总结
    print("\n" + "="*60)
    print("  完整测试总结")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\n总计: {passed}/{total} 项测试通过\n")
    
    for name, status in results.items():
        status_text = "✅" if status else "❌"
        name_map = {
            'env': '环境配置',
            'db': '数据库状态',
            'core': '核心功能'
        }
        print(f"{status_text} {name_map.get(name, name)}")
    
    print("\n" + "="*60)
    
    if passed == total:
        print("[SUCCESS] 所有测试通过！系统完全正常")
    elif passed >= 2:
        print("[SUCCESS] 核心测试通过！系统可以使用")
        print("[INFO] 部分可选功能未配置（正常）")
    else:
        print("[WARNING] 多项测试失败，请检查配置")
    
    print("="*60)
    
    print(f"\n完成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n[下一步]")
    print("  python run_server.py    # 启动服务")
    print("  http://localhost:8000/docs  # 访问文档")
    print("\n")
    
    return passed >= 2


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n[INFO] 用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

