#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库完整设置脚本

功能：
1. 检查PostgreSQL连接
2. 创建数据库（如需要）
3. 初始化表结构
4. 添加初始游戏数据
5. 添加示例文档数据

使用方法:
    python scripts/setup_database.py
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

import asyncio


def print_header():
    """打印标题"""
    print("\n" + "="*60)
    print("  RAG游戏问答系统 - 数据库完整设置")
    print("="*60)


def print_section(title):
    """打印分节标题"""
    print("\n" + "-"*60)
    print(f"  {title}")
    print("-"*60)


def check_postgres_installed():
    """检查PostgreSQL是否安装"""
    print_section("检查PostgreSQL安装")
    
    import subprocess
    try:
        result = subprocess.run(['psql', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"[OK] PostgreSQL已安装: {version}")
            return True
        else:
            print("[WARN] PostgreSQL未找到")
            return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("[WARN] PostgreSQL未安装或不在PATH中")
        return False


def test_database_connection():
    """测试数据库连接"""
    print_section("测试数据库连接")
    
    try:
        from config.settings import settings
        from sqlalchemy import create_engine, text
        
        db_url = settings.get_database_url()
        print(f"[INFO] 数据库URL: {db_url.split('@')[1] if '@' in db_url else 'localhost'}")
        
        print("[INFO] 正在连接...")
        engine = create_engine(db_url, connect_args={'connect_timeout': 5})
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"[OK] 连接成功!")
            print(f"[INFO] 版本: {version.split(',')[0]}")
        
        return True, engine
        
    except Exception as e:
        error_msg = str(e)
        print(f"[FAIL] 连接失败: {error_msg[:200]}")
        
        if "does not exist" in error_msg:
            print("\n[提示] 数据库不存在，需要创建")
            print("[命令] 运行: psql -U postgres")
            print("[SQL]   CREATE DATABASE rag_game_qa;")
        elif "password authentication failed" in error_msg:
            print("\n[提示] 密码错误，请检查.env文件中的DATABASE_URL")
        elif "Connection refused" in error_msg or "connection to server" in error_msg:
            print("\n[提示] PostgreSQL服务未运行")
            print("[解决] 启动PostgreSQL服务")
        
        return False, None


def create_tables(engine):
    """创建数据库表"""
    print_section("创建数据库表")
    
    try:
        from config.database import Base
        from sqlalchemy import inspect
        
        print("[INFO] 正在创建表...")
        Base.metadata.create_all(bind=engine)
        
        # 获取所有表名
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"[OK] 成功创建 {len(tables)} 个表:")
        for table in tables:
            print(f"  - {table}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] 创建表失败: {e}")
        return False


def seed_games(engine):
    """填充游戏数据"""
    print_section("填充游戏数据")
    
    try:
        from config.database import SessionLocal, Game
        
        db = SessionLocal()
        
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
                "languages": '["zh-CN", "en-US"]'
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
        
        added = 0
        for game_data in games:
            existing = db.query(Game).filter(
                Game.game_id == game_data["game_id"]
            ).first()
            
            if existing:
                print(f"  [SKIP] {game_data['game_name']} (已存在)")
            else:
                game = Game(**game_data)
                db.add(game)
                print(f"  [ADD] {game_data['game_name']}")
                added += 1
        
        db.commit()
        print(f"\n[OK] 新增 {added} 个游戏")
        
        # 显示所有游戏
        all_games = db.query(Game).all()
        print(f"[INFO] 数据库中共有 {len(all_games)} 个游戏")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"[FAIL] 填充游戏数据失败: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()
        return False


async def seed_documents(engine):
    """填充示例文档"""
    print_section("填充示例文档")
    
    try:
        from config.database import SessionLocal, Document
        from core.knowledge_base.embedding_service import EmbeddingService
        
        print("[INFO] 初始化嵌入服务...")
        embedding_service = EmbeddingService()
        print(f"[OK] 模型: {embedding_service.model_name}")
        
        db = SessionLocal()
        
        sample_docs = [
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
                "game_id": "lol",
                "title": "英雄联盟控制键位",
                "content": "Q、W、E、R为技能键，D、F为召唤师技能，B键回城，Tab键查看计分板。",
                "category": "操作指南",
                "source": "官方文档"
            }
        ]
        
        print(f"[INFO] 准备添加 {len(sample_docs)} 个文档...")
        
        added = 0
        for doc_data in sample_docs:
            existing = db.query(Document).filter(
                Document.game_id == doc_data["game_id"],
                Document.title == doc_data["title"]
            ).first()
            
            if existing:
                print(f"  [SKIP] {doc_data['title'][:30]}... (已存在)")
            else:
                print(f"  [处理] {doc_data['title'][:30]}...", end='')
                embedding = await embedding_service.encode_text(doc_data["content"])
                
                doc = Document(
                    game_id=doc_data["game_id"],
                    title=doc_data["title"],
                    content=doc_data["content"],
                    category=doc_data["category"],
                    source=doc_data["source"],
                    doc_metadata="{}",
                    embedding=str(embedding.tolist())
                )
                db.add(doc)
                print(" [OK]")
                added += 1
        
        db.commit()
        print(f"\n[OK] 新增 {added} 个文档")
        
        # 统计
        total = db.query(Document).count()
        print(f"[INFO] 数据库中共有 {total} 个文档")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"[FAIL] 填充文档失败: {e}")
        import traceback
        print(traceback.format_exc()[:500])
        if 'db' in locals():
            db.rollback()
            db.close()
        return False


def show_summary(engine):
    """显示统计摘要"""
    print_section("数据库统计")
    
    try:
        from config.database import SessionLocal, Game, Document
        from sqlalchemy import func
        
        db = SessionLocal()
        
        # 游戏统计
        game_count = db.query(Game).count()
        print(f"[INFO] 游戏数量: {game_count}")
        
        # 文档统计
        doc_count = db.query(Document).count()
        print(f"[INFO] 文档总数: {doc_count}")
        
        # 按游戏统计
        if doc_count > 0:
            print("\n[INFO] 各游戏文档分布:")
            stats = db.query(
                Game.game_name,
                func.count(Document.id).label('count')
            ).outerjoin(
                Document, Game.game_id == Document.game_id
            ).group_by(Game.game_name).all()
            
            for game_name, count in stats:
                print(f"  - {game_name}: {count} 个文档")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"[FAIL] 统计失败: {e}")
        return False


async def main():
    """主函数"""
    print_header()
    
    # 步骤1: 检查PostgreSQL
    has_postgres = check_postgres_installed()
    
    # 步骤2: 测试连接
    success, engine = test_database_connection()
    
    if not success:
        print("\n" + "="*60)
        print("  数据库连接失败")
        print("="*60)
        print("\n[选项1] 配置PostgreSQL后重试")
        print("  - 安装PostgreSQL")
        print("  - 创建数据库: CREATE DATABASE rag_game_qa;")
        print("  - 更新.env中的密码")
        print("  - 重新运行本脚本")
        print("\n[选项2] 暂时跳过数据库")
        print("  - 系统可以使用内存模式运行")
        print("  - 直接运行: python run_server.py")
        print("="*60 + "\n")
        return False
    
    # 步骤3: 创建表
    print()
    success = create_tables(engine)
    if not success:
        print("\n[ERROR] 创建表失败")
        return False
    
    # 步骤4: 填充游戏数据
    print()
    success = seed_games(engine)
    if not success:
        print("\n[WARN] 填充游戏数据失败，但表已创建")
    
    # 步骤5: 填充文档数据
    print()
    success = await seed_documents(engine)
    if not success:
        print("\n[WARN] 填充文档数据失败")
    
    # 步骤6: 显示统计
    print()
    show_summary(engine)
    
    # 完成
    print("\n" + "="*60)
    print("  数据库设置完成!")
    print("="*60)
    print("\n[成功] 数据库已准备就绪")
    print("\n[下一步]")
    print("  1. 启动服务: python run_server.py")
    print("  2. 访问文档: http://localhost:8000/docs")
    print("  3. 测试问答功能")
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

