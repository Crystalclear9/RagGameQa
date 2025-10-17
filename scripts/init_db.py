#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库初始化脚本

功能：
1. 创建所有数据库表
2. 添加初始游戏数据
3. 验证数据库连接

使用方法:
    python scripts/init_db.py
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


def print_section(title):
    """打印分节标题"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def check_database_connection():
    """检查数据库连接"""
    print_section("步骤1: 检查数据库连接")
    
    try:
        from config.settings import settings
        from sqlalchemy import create_engine, text
        
        db_url = settings.get_database_url()
        print(f"[INFO] 数据库URL: {db_url.split('@')[0]}@...")
        
        print("[INFO] 正在连接数据库...")
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"[OK] 连接成功!")
            print(f"[INFO] PostgreSQL版本: {version.split(',')[0]}")
        
        return True, engine
        
    except ImportError as e:
        print(f"[ERROR] 缺少依赖包: {e}")
        print("[INFO] 请运行: pip install sqlalchemy psycopg2-binary")
        return False, None
        
    except Exception as e:
        print(f"[ERROR] 数据库连接失败: {str(e)}")
        print("\n[TIPS] 请检查:")
        print("  1. PostgreSQL是否已安装并运行")
        print("  2. 数据库是否已创建: CREATE DATABASE rag_game_qa;")
        print("  3. .env文件中DATABASE_URL是否正确")
        print("  4. 用户名密码是否正确")
        return False, None


def create_database_tables():
    """创建数据库表"""
    print_section("步骤2: 创建数据库表")
    
    try:
        from config.database import create_tables, Base, engine
        
        print("[INFO] 正在创建数据库表...")
        create_tables()
        
        # 获取所有表名
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"[OK] 成功创建 {len(tables)} 个表:")
        for table in tables:
            print(f"  - {table}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 创建表失败: {str(e)}")
        import traceback
        print(traceback.format_exc()[:500])
        return False


def seed_initial_data():
    """填充初始数据"""
    print_section("步骤3: 填充初始游戏数据")
    
    try:
        from config.database import SessionLocal, Game
        
        db = SessionLocal()
        
        # 定义初始游戏数据
        games = [
            {
                "game_id": "wow",
                "game_name": "魔兽世界",
                "version": "10.2.0",
                "platforms": '["PC", "Mac"]',
                "languages": '["zh-CN", "en-US"]'
            },
            {
                "game_id": "lol",
                "game_name": "英雄联盟",
                "version": "13.24",
                "platforms": '["PC"]',
                "languages": '["zh-CN", "en-US", "ko-KR"]'
            },
            {
                "game_id": "genshin",
                "game_name": "原神",
                "version": "4.3.0",
                "platforms": '["PC", "Mobile", "PS5"]',
                "languages": '["zh-CN", "en-US", "ja-JP"]'
            },
            {
                "game_id": "minecraft",
                "game_name": "我的世界",
                "version": "1.20.4",
                "platforms": '["PC", "Mobile", "Console"]',
                "languages": '["zh-CN", "en-US"]'
            },
            {
                "game_id": "valorant",
                "game_name": "无畏契约",
                "version": "7.12",
                "platforms": '["PC"]',
                "languages": '["zh-CN", "en-US"]'
            },
            {
                "game_id": "apex",
                "game_name": "Apex英雄",
                "version": "20.1",
                "platforms": '["PC", "Console"]',
                "languages": '["zh-CN", "en-US"]'
            }
        ]
        
        print(f"[INFO] 准备添加 {len(games)} 个游戏...")
        
        added_count = 0
        for game_data in games:
            # 检查是否已存在
            existing = db.query(Game).filter(
                Game.game_id == game_data["game_id"]
            ).first()
            
            if existing:
                print(f"  [SKIP] {game_data['game_name']} (已存在)")
            else:
                game = Game(**game_data)
                db.add(game)
                print(f"  [ADD] {game_data['game_name']}")
                added_count += 1
        
        db.commit()
        print(f"\n[OK] 成功添加 {added_count} 个游戏")
        
        # 显示当前所有游戏
        all_games = db.query(Game).all()
        print(f"\n[INFO] 数据库中共有 {len(all_games)} 个游戏:")
        for game in all_games:
            print(f"  - [{game.game_id}] {game.game_name} v{game.version}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] 填充数据失败: {str(e)}")
        import traceback
        print(traceback.format_exc()[:500])
        if 'db' in locals():
            db.rollback()
            db.close()
        return False


def verify_database():
    """验证数据库"""
    print_section("步骤4: 验证数据库")
    
    try:
        from config.database import SessionLocal, Game, Document
        
        db = SessionLocal()
        
        # 统计数据
        game_count = db.query(Game).count()
        doc_count = db.query(Document).count()
        
        print(f"[OK] 游戏数量: {game_count}")
        print(f"[OK] 文档数量: {doc_count}")
        
        if game_count > 0:
            print("\n[SUCCESS] 数据库初始化成功！")
        else:
            print("\n[WARNING] 数据库为空，请添加数据")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] 验证失败: {str(e)}")
        return False


def main():
    """主函数"""
    print("\n" + "="*60)
    print("  RAG游戏问答系统 - 数据库初始化")
    print("="*60)
    
    # 步骤1: 检查数据库连接
    success, engine = check_database_connection()
    if not success:
        print("\n[FAILED] 数据库连接失败，无法继续")
        return False
    
    # 步骤2: 创建数据库表
    success = create_database_tables()
    if not success:
        print("\n[FAILED] 创建表失败")
        return False
    
    # 步骤3: 填充初始数据
    success = seed_initial_data()
    if not success:
        print("\n[WARNING] 填充数据失败，但表已创建")
    
    # 步骤4: 验证数据库
    verify_database()
    
    # 完成
    print("\n" + "="*60)
    print("  完成!")
    print("="*60)
    print("\n下一步:")
    print("  1. 添加示例文档: python scripts/add_sample_docs.py")
    print("  2. 启动服务: python api/main.py")
    print("  3. 访问文档: http://localhost:8000/docs")
    print("="*60 + "\n")
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[INFO] 用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

