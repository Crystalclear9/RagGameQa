#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查数据库状态

快速查看数据库配置和数据情况

使用方法:
    python scripts/check_db_status.py
"""

import sys
from pathlib import Path

# Windows编码
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))


def main():
    """主函数"""
    print("="*60)
    print("  数据库状态检查")
    print("="*60)
    
    # 检查连接
    print("\n[检查1] 数据库连接...")
    try:
        from config.settings import settings
        from sqlalchemy import create_engine, text
        
        db_url = settings.get_database_url()
        engine = create_engine(db_url, connect_args={'connect_timeout': 3})
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"  ✅ 连接成功")
            print(f"  版本: {version.split(',')[0]}")
        
        has_db = True
    except Exception as e:
        print(f"  ❌ 连接失败: {str(e)[:100]}")
        print(f"  💡 可以不使用数据库，直接运行: python run_server.py")
        has_db = False
    
    if not has_db:
        print("\n" + "="*60)
        print("  数据库未配置（这是正常的）")
        print("="*60)
        return
    
    # 检查表
    print("\n[检查2] 数据库表...")
    try:
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if tables:
            print(f"  ✅ 存在 {len(tables)} 个表:")
            for table in tables:
                print(f"     - {table}")
        else:
            print(f"  ⚠️  没有表，需要初始化")
            print(f"  运行: python scripts/setup_database.py")
    except Exception as e:
        print(f"  ❌ 检查失败: {e}")
    
    # 检查数据
    print("\n[检查3] 数据统计...")
    try:
        from config.database import SessionLocal, Game, Document, QueryLog
        
        db = SessionLocal()
        
        game_count = db.query(Game).count()
        doc_count = db.query(Document).count()
        log_count = db.query(QueryLog).count()
        
        print(f"  ✅ 游戏: {game_count} 个")
        print(f"  ✅ 文档: {doc_count} 个")
        print(f"  ✅ 日志: {log_count} 条")
        
        if game_count == 0:
            print(f"\n  ⚠️  没有数据，需要填充")
            print(f"  运行: python scripts/setup_database.py")
        elif doc_count == 0:
            print(f"\n  ⚠️  没有文档，建议添加")
            print(f"  运行: python scripts/add_sample_docs.py")
        else:
            print(f"\n  ✅ 数据充足，可以使用")
        
        db.close()
        
    except Exception as e:
        print(f"  ❌ 统计失败: {e}")
    
    print("\n" + "="*60)
    print("  检查完成")
    print("="*60)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

