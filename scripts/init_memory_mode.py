#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
初始化内存模式 - 无需PostgreSQL

创建内存中的示例数据，用于测试和演示

使用方法:
    python scripts/init_memory_mode.py
"""

import sys
from pathlib import Path
import json

# Windows编码
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))


# 创建示例数据文件
SAMPLE_DATA = {
    "games": [
        {
            "game_id": "wow",
            "game_name": "魔兽世界",
            "version": "10.2.0",
            "platforms": ["PC", "Mac"],
            "languages": ["zh-CN", "en-US"]
        },
        {
            "game_id": "lol",
            "game_name": "英雄联盟",
            "version": "13.24",
            "platforms": ["PC"],
            "languages": ["zh-CN", "en-US"]
        },
        {
            "game_id": "genshin",
            "game_name": "原神",
            "version": "4.3.0",
            "platforms": ["PC", "Mobile", "PS5"],
            "languages": ["zh-CN", "en-US", "ja-JP"]
        }
    ],
    "documents": [
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
            "content": "开局红BUFF，然后打蓝BUFF区域的野怪，升到3级后可以考虑gank。注意观察小地图，优先帮助线上压力大的队友。",
            "category": "游戏攻略",
            "source": "职业选手分享"
        },
        {
            "game_id": "genshin",
            "title": "元素反应机制",
            "content": "原神的战斗核心是元素反应。水+火=蒸发（伤害提升），冰+火=融化（伤害提升），雷+水=感电（持续伤害），风元素可以扩散其他元素。",
            "category": "战斗系统",
            "source": "官方说明"
        }
    ]
}


def main():
    """主函数"""
    print("="*60)
    print("  RAG游戏问答系统 - 内存模式初始化")
    print("="*60)
    
    # 创建data目录
    data_dir = root_dir / "data"
    data_dir.mkdir(exist_ok=True)
    
    # 保存示例数据
    sample_file = data_dir / "sample_data.json"
    
    print(f"\n[INFO] 创建示例数据文件...")
    print(f"[INFO] 路径: {sample_file}")
    
    try:
        with open(sample_file, 'w', encoding='utf-8') as f:
            json.dump(SAMPLE_DATA, f, ensure_ascii=False, indent=2)
        
        print(f"[OK] 文件创建成功")
        print(f"\n[INFO] 数据统计:")
        print(f"  - 游戏: {len(SAMPLE_DATA['games'])} 个")
        print(f"  - 文档: {len(SAMPLE_DATA['documents'])} 个")
        
        # 显示游戏列表
        print(f"\n[INFO] 游戏列表:")
        for game in SAMPLE_DATA['games']:
            print(f"  - [{game['game_id']}] {game['game_name']} v{game['version']}")
        
        # 显示文档分布
        print(f"\n[INFO] 文档分布:")
        from collections import Counter
        game_doc_count = Counter(doc['game_id'] for doc in SAMPLE_DATA['documents'])
        for game_id, count in game_doc_count.items():
            game_name = next(g['game_name'] for g in SAMPLE_DATA['games'] if g['game_id'] == game_id)
            print(f"  - {game_name}: {count} 个文档")
        
        print("\n" + "="*60)
        print("  内存模式已初始化")
        print("="*60)
        print("\n[成功] 示例数据已准备")
        print("\n[说明]")
        print("  - 无需PostgreSQL即可运行")
        print("  - 数据存储在内存中（重启后清空）")
        print("  - 适合开发和测试")
        print("\n[下一步]")
        print("  python run_server.py")
        print("="*60 + "\n")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 创建失败: {e}")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

