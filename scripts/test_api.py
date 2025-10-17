#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API完整功能测试

测试所有API端点的功能性

使用方法:
    # 先启动服务: python run_server.py
    # 然后在新终端运行: python scripts/test_api.py
"""

import sys
from pathlib import Path

# Windows编码
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

import time


def print_section(title):
    """打印分节标题"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def test_with_client():
    """使用测试客户端测试（推荐）"""
    print_section("使用测试客户端测试")
    
    try:
        from fastapi.testclient import TestClient
        from api.main import app
        
        client = TestClient(app)
        print("[OK] 测试客户端创建成功")
        
        # 测试1: 根路径
        print("\n[测试1] GET /")
        response = client.get("/")
        print(f"  状态码: {response.status_code}")
        data = response.json()
        print(f"  系统: {data.get('message')}")
        print(f"  版本: {data.get('version')}")
        print(f"  功能: {data.get('features')}")
        assert response.status_code == 200, "根路径测试失败"
        print("  ✅ 通过")
        
        # 测试2: 健康检查
        print("\n[测试2] GET /health")
        response = client.get("/health")
        print(f"  状态码: {response.status_code}")
        data = response.json()
        print(f"  状态: {data.get('status')}")
        assert response.status_code == 200, "健康检查测试失败"
        assert data.get('status') == 'ok', "健康状态异常"
        print("  ✅ 通过")
        
        # 测试3: QA ping
        print("\n[测试3] GET /api/v1/qa/ping")
        response = client.get("/api/v1/qa/ping")
        print(f"  状态码: {response.status_code}")
        data = response.json()
        print(f"  响应: {data}")
        assert response.status_code == 200, "QA ping测试失败"
        print("  ✅ 通过")
        
        # 测试4: 问答接口 - 魔兽世界
        print("\n[测试4] POST /api/v1/qa/ask - 魔兽世界")
        start_time = time.time()
        response = client.post("/api/v1/qa/ask", json={
            "question": "魔兽世界中战士如何学习技能？",
            "game_id": "wow"
        })
        elapsed = time.time() - start_time
        
        print(f"  状态码: {response.status_code}")
        print(f"  耗时: {elapsed:.2f}秒")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  答案预览: {data.get('answer', '')[:100]}...")
            print(f"  置信度: {data.get('confidence')}")
            print(f"  来源数: {len(data.get('sources', []))}")
            print("  ✅ 通过")
        else:
            print(f"  ❌ 失败: {response.text}")
        
        # 测试5: 问答接口 - 英雄联盟
        print("\n[测试5] POST /api/v1/qa/ask - 英雄联盟")
        response = client.post("/api/v1/qa/ask", json={
            "question": "如何打野？",
            "game_id": "lol"
        })
        print(f"  状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  答案预览: {data.get('answer', '')[:80]}...")
            print("  ✅ 通过")
        
        # 测试6: 问答接口 - 原神
        print("\n[测试6] POST /api/v1/qa/ask - 原神")
        response = client.post("/api/v1/qa/ask", json={
            "question": "如何触发元素反应？",
            "game_id": "genshin"
        })
        print(f"  状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  答案预览: {data.get('answer', '')[:80]}...")
            print("  ✅ 通过")
        
        # 测试7: 参数验证
        print("\n[测试7] 参数验证测试")
        response = client.post("/api/v1/qa/ask", json={
            "question": "",  # 空问题
            "game_id": "wow"
        })
        print(f"  空问题状态码: {response.status_code}")
        assert response.status_code == 400, "应该返回400错误"
        print("  ✅ 通过")
        
        return True
        
    except AssertionError as e:
        print(f"\n  ❌ 断言失败: {e}")
        return False
    except Exception as e:
        print(f"\n  ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_with_requests():
    """使用requests测试（需服务运行）"""
    print_section("使用requests测试（需服务运行）")
    
    try:
        import requests
        
        BASE_URL = "http://localhost:8000"
        
        # 测试连接
        print("\n[测试] 检查服务是否运行...")
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=2)
            if response.status_code == 200:
                print("  ✅ 服务正在运行")
            else:
                print("  ⚠️  服务响应异常")
                return False
        except requests.exceptions.ConnectionError:
            print("  ❌ 服务未运行")
            print("  请先启动服务: python run_server.py")
            return False
        
        # 测试问答
        print("\n[测试] POST /api/v1/qa/ask")
        response = requests.post(
            f"{BASE_URL}/api/v1/qa/ask",
            json={
                "question": "如何学习技能？",
                "game_id": "wow"
            },
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"  ✅ 问答成功")
            print(f"  答案: {result.get('answer', '')[:100]}...")
            return True
        else:
            print(f"  ❌ 请求失败: {response.status_code}")
            return False
            
    except ImportError:
        print("  [SKIP] requests未安装，跳过此测试")
        return None
    except Exception as e:
        print(f"  ❌ 测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("  RAG游戏问答系统 - API功能测试")
    print("="*60)
    print("\n[说明] 这个脚本会测试所有API端点")
    
    results = {}
    
    # 方法1: 使用测试客户端（推荐）
    results['test_client'] = test_with_client()
    
    # 方法2: 使用requests（需服务运行）
    results['requests'] = test_with_requests()
    
    # 总结
    print("\n" + "="*60)
    print("  测试总结")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v is True)
    total = sum(1 for v in results.values() if v is not None)
    
    print(f"\n通过: {passed}/{total}\n")
    
    for name, status in results.items():
        if status is True:
            print(f"✅ {name}")
        elif status is False:
            print(f"❌ {name}")
        else:
            print(f"⚪ {name} (跳过)")
    
    print("\n" + "="*60)
    
    if passed >= total * 0.8:  # 80%通过
        print("[SUCCESS] 测试通过！API功能正常")
    else:
        print("[WARNING] 部分测试失败")
    
    print("="*60 + "\n")
    
    return passed >= total * 0.8


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

