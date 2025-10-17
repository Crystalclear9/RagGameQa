#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
添加示例文档脚本

功能：
1. 为各个游戏添加示例知识文档
2. 生成文档的嵌入向量
3. 验证文档是否添加成功

使用方法:
    python scripts/add_sample_docs.py
"""

import os
import sys
import asyncio
from pathlib import Path

# Windows编码处理
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目路径
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))


# 示例文档数据
SAMPLE_DOCS = [
    # 魔兽世界文档
    {
        "game_id": "wow",
        "title": "战士技能学习指南",
        "content": "战士可以通过访问职业训练师学习新技能。训练师通常位于主城和营地中，例如暴风城的战士区、奥格瑞玛的力量谷等。学习技能需要达到相应等级并支付金币。",
        "category": "职业技能",
        "source": "官方攻略"
    },
    {
        "game_id": "wow",
        "title": "组队系统说明",
        "content": "按I键打开社交面板，点击组队查找器，选择你想要进入的副本或活动，然后点击加入队列。系统会自动匹配其他玩家组成队伍。",
        "category": "社交功能",
        "source": "新手指南"
    },
    {
        "game_id": "wow",
        "title": "装备获取途径",
        "content": "装备可以通过多种方式获得：完成任务奖励、击败副本BOSS掉落、在拍卖行购买、通过专业技能制作、参与PVP活动获得荣誉点数兑换等。",
        "category": "装备系统",
        "source": "玩家攻略"
    },
    
    # 英雄联盟文档
    {
        "game_id": "lol",
        "title": "英雄联盟控制键位",
        "content": "Q、W、E、R为技能键，D、F为召唤师技能，B键回城，Tab键查看计分板，Alt+技能键为对自己施放技能。可以在设置中自定义按键。",
        "category": "操作指南",
        "source": "官方文档"
    },
    {
        "game_id": "lol",
        "title": "打野路线推荐",
        "content": "开局红BUFF，然后打蓝BUFF区域的野怪，升到3级后可以考虑gank。注意观察小地图，优先帮助线上压力大的队友。前期控制河道蟹可以获得视野和经验优势。",
        "category": "游戏攻略",
        "source": "职业选手分享"
    },
    
    # 原神文档
    {
        "game_id": "genshin",
        "title": "元素反应机制",
        "content": "原神的战斗核心是元素反应。水+火=蒸发（伤害提升），冰+火=融化（伤害提升），雷+水=感电（持续伤害），风元素可以扩散其他元素。合理利用元素反应可以大幅提升战斗效率。",
        "category": "战斗系统",
        "source": "官方说明"
    },
    {
        "game_id": "genshin",
        "title": "圣遗物选择指南",
        "content": "不同角色适合不同的圣遗物套装。输出角色优先选择攻击力、暴击、暴击伤害属性，辅助角色选择元素充能效率、元素精通。4件套效果通常比2+2更强。",
        "category": "装备系统",
        "source": "玩家攻略"
    },
    
    # 我的世界文档
    {
        "game_id": "minecraft",
        "title": "生存模式开局指南",
        "content": "第一天务必收集木头制作工作台和木镐，然后挖掘石头制作石质工具。在天黑前建造简单的庇护所。收集煤炭制作火把照明，这样可以防止怪物生成。",
        "category": "新手指南",
        "source": "官方Wiki"
    },
    {
        "game_id": "minecraft",
        "title": "红石基础教程",
        "content": "红石粉可以传递信号，红石火把可以反转信号，中继器可以延长信号和延时。利用这些基础元件可以制作自动门、陷阱、自动农场等复杂机械。",
        "category": "高级技巧",
        "source": "红石教程"
    },
    
    # 无畏契约文档
    {
        "game_id": "valorant",
        "title": "枪械后坐力控制",
        "content": "射击时鼠标应该向下微调来压制后坐力。范迪尔向上踢，幻影向左上踢。建议在练习场反复练习，熟悉各把枪的后坐力模式。短点射比扫射更容易控制。",
        "category": "射击技巧",
        "source": "职业选手教学"
    },
    
    # Apex英雄文档
    {
        "game_id": "apex",
        "title": "传奇角色选择建议",
        "content": "新手推荐使用命脉、寻血猎犬、班加罗尔等操作简单的传奇。命脉的无人机可以快速回血，寻血猎犬的扫描可以发现敌人，班加罗尔的烟雾弹便于撤退和进攻。",
        "category": "角色攻略",
        "source": "新手教程"
    }
]


def print_section(title):
    """打印分节标题"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


async def add_documents():
    """添加示例文档"""
    print_section("添加示例文档")
    
    try:
        from config.database import SessionLocal, Document
        from core.knowledge_base.embedding_service import EmbeddingService
        
        print("[INFO] 初始化嵌入服务...")
        embedding_service = EmbeddingService()
        print(f"[OK] 嵌入模型: {embedding_service.model_name}")
        print(f"[OK] 向量维度: {embedding_service.get_embedding_dimension()}")
        
        db = SessionLocal()
        
        print(f"\n[INFO] 准备添加 {len(SAMPLE_DOCS)} 个文档...")
        
        added_count = 0
        skipped_count = 0
        
        for i, doc_data in enumerate(SAMPLE_DOCS, 1):
            # 检查是否已存在
            existing = db.query(Document).filter(
                Document.game_id == doc_data["game_id"],
                Document.title == doc_data["title"]
            ).first()
            
            if existing:
                print(f"  [{i}/{len(SAMPLE_DOCS)}] [SKIP] {doc_data['title']} (已存在)")
                skipped_count += 1
                continue
            
            # 生成嵌入向量
            print(f"  [{i}/{len(SAMPLE_DOCS)}] [处理] {doc_data['title']}...", end='')
            embedding = await embedding_service.encode_text(doc_data["content"])
            
            # 创建文档
            document = Document(
                game_id=doc_data["game_id"],
                title=doc_data["title"],
                content=doc_data["content"],
                category=doc_data["category"],
                source=doc_data["source"],
                embedding=str(embedding.tolist())
            )
            
            db.add(document)
            print(" [OK]")
            added_count += 1
        
        db.commit()
        
        print(f"\n[SUMMARY]")
        print(f"  新增: {added_count} 个")
        print(f"  跳过: {skipped_count} 个")
        print(f"  总计: {len(SAMPLE_DOCS)} 个")
        
        # 显示统计信息
        print(f"\n[INFO] 各游戏文档数量:")
        from sqlalchemy import func
        stats = db.query(
            Document.game_id,
            func.count(Document.id).label('count')
        ).group_by(Document.game_id).all()
        
        for game_id, count in stats:
            print(f"  - {game_id}: {count} 个文档")
        
        db.close()
        return True
        
    except ImportError as e:
        print(f"[ERROR] 缺少依赖: {e}")
        print("[INFO] 请运行: pip install sentence-transformers")
        return False
        
    except Exception as e:
        print(f"\n[ERROR] 添加文档失败: {str(e)}")
        import traceback
        print(traceback.format_exc()[:500])
        if 'db' in locals():
            db.rollback()
            db.close()
        return False


async def verify_documents():
    """验证文档"""
    print_section("验证文档")
    
    try:
        from config.database import SessionLocal, Document
        
        db = SessionLocal()
        
        # 统计
        total = db.query(Document).count()
        print(f"[OK] 数据库中共有 {total} 个文档")
        
        # 随机抽取一个文档测试
        if total > 0:
            sample_doc = db.query(Document).first()
            print(f"\n[INFO] 示例文档:")
            print(f"  游戏: {sample_doc.game_id}")
            print(f"  标题: {sample_doc.title}")
            print(f"  分类: {sample_doc.category}")
            print(f"  内容: {sample_doc.content[:50]}...")
            
            # 检查嵌入向量
            if sample_doc.embedding:
                import ast
                embedding = ast.literal_eval(sample_doc.embedding)
                print(f"  向量维度: {len(embedding)}")
                print("[OK] 嵌入向量存在")
            else:
                print("[WARNING] 嵌入向量缺失")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] 验证失败: {str(e)}")
        return False


async def main():
    """主函数"""
    print("\n" + "="*60)
    print("  RAG游戏问答系统 - 添加示例文档")
    print("="*60)
    
    # 添加文档
    success = await add_documents()
    
    if not success:
        print("\n[FAILED] 添加文档失败")
        return False
    
    # 验证文档
    await verify_documents()
    
    # 完成
    print("\n" + "="*60)
    print("  完成!")
    print("="*60)
    print("\n下一步:")
    print("  1. 测试检索: python scripts/test_retrieval.py")
    print("  2. 启动服务: python api/main.py")
    print("  3. 测试问答: POST /api/v1/qa/ask")
    print("="*60 + "\n")
    
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[INFO] 用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

