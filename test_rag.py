# 测试RAG引擎
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from core.rag_engine import RAGEngine

async def test_rag():
    try:
        print("创建RAG引擎...")
        rag = RAGEngine('wow')
        
        print("测试查询...")
        result = await rag.query('战士如何学习技能？')
        
        print("结果:")
        print(f"答案: {result.get('answer', '')}")
        print(f"置信度: {result.get('confidence', 0)}")
        print(f"来源数量: {len(result.get('sources', []))}")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_rag())
