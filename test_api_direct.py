# API测试脚本
import requests
import json

def test_qa_api():
    url = "http://localhost:8000/api/v1/qa/ask"
    data = {
        "question": "战士如何学习技能？",
        "game_id": "wow"
    }
    
    try:
        print("发送请求...")
        response = requests.post(url, json=data, timeout=30)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("成功!")
            print(f"答案: {result.get('answer', '')}")
            print(f"置信度: {result.get('confidence', 0)}")
            print(f"来源数量: {len(result.get('sources', []))}")
        else:
            print(f"错误: {response.text}")
            
    except Exception as e:
        print(f"请求失败: {e}")

if __name__ == "__main__":
    test_qa_api()
