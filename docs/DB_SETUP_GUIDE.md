# 📊 数据库配置指南

> RAG游戏问答系统 - PostgreSQL数据库配置

---

## 🎯 概述

本系统使用PostgreSQL作为主数据库，存储：
- 游戏信息
- 知识文档
- 查询日志
- 用户反馈
- 分析数据

---

## 📋 前置要求

- PostgreSQL 12+ (推荐 14+)
- Python包: `sqlalchemy`, `psycopg2-binary`, `asyncpg`

---

## 🚀 快速开始（Windows）

### 方法1: 使用已提供的脚本（推荐）✨

```bash
# 1. 安装依赖
pip install sqlalchemy psycopg2-binary

# 2. 创建数据库（如果PostgreSQL已安装）
# 打开PostgreSQL的SQL Shell或pgAdmin，执行：
CREATE DATABASE rag_game_qa;

# 3. 运行初始化脚本
python scripts/init_db.py

# 4. 添加示例文档
python scripts/add_sample_docs.py
```

### 方法2: 手动配置

详见下方完整步骤。

---

## 📝 完整配置步骤

### 步骤1: 安装PostgreSQL

#### Windows安装
1. **下载安装包**
   - 访问: https://www.postgresql.org/download/windows/
   - 下载最新版本安装器

2. **运行安装程序**
   ```
   - 选择安装目录
   - 设置端口：5432（默认）
   - 设置超级用户密码：记住这个密码！
   - 选择locale：Chinese, China
   ```

3. **验证安装**
   ```cmd
   psql --version
   # 应该显示: psql (PostgreSQL) 14.x 或更高版本
   ```

---

### 步骤2: 创建数据库

#### 方法A: 使用SQL Shell (推荐)

1. **打开SQL Shell (psql)**
   - 开始菜单 → PostgreSQL → SQL Shell (psql)

2. **连接到PostgreSQL**
   ```sql
   服务器 [localhost]: (直接回车)
   数据库 [postgres]: (直接回车)
   端口 [5432]: (直接回车)
   用户名 [postgres]: (直接回车)
   密码: (输入你的PostgreSQL密码)
   ```

3. **创建数据库**
   ```sql
   CREATE DATABASE rag_game_qa;
   \l  -- 查看数据库列表，确认创建成功
   \q  -- 退出
   ```

#### 方法B: 使用pgAdmin

1. 打开pgAdmin
2. 连接到PostgreSQL服务器
3. 右键 "Databases" → "Create" → "Database"
4. 输入数据库名: `rag_game_qa`
5. 点击"Save"

---

### 步骤3: 配置连接字符串

编辑 `.env` 文件，确保以下配置正确：

```bash
# 数据库配置
DATABASE_URL=postgresql://postgres:你的密码@localhost:5432/rag_game_qa

# 例如，如果密码是 "mypassword"：
# DATABASE_URL=postgresql://postgres:mypassword@localhost:5432/rag_game_qa
```

**格式说明**:
```
postgresql://用户名:密码@主机:端口/数据库名
```

---

### 步骤4: 安装Python依赖

```bash
# 安装数据库相关依赖
pip install sqlalchemy psycopg2-binary asyncpg alembic

# 或者安装完整依赖
pip install -r requirements.txt
```

---

### 步骤5: 初始化数据库

```bash
# 运行初始化脚本
python scripts/init_db.py
```

**期望输出**:
```
============================================================
  RAG游戏问答系统 - 数据库初始化
============================================================

============================================================
  步骤1: 检查数据库连接
============================================================
[INFO] 数据库URL: postgresql://postgres@...
[INFO] 正在连接数据库...
[OK] 连接成功!
[INFO] PostgreSQL版本: PostgreSQL 14.x

============================================================
  步骤2: 创建数据库表
============================================================
[INFO] 正在创建数据库表...
[OK] 成功创建 7 个表:
  - games
  - documents
  - query_logs
  - feedbacks
  - user_profiles
  - health_records
  - analytics_data

============================================================
  步骤3: 填充初始游戏数据
============================================================
[INFO] 准备添加 6 个游戏...
  [ADD] 魔兽世界
  [ADD] 英雄联盟
  [ADD] 原神
  [ADD] 我的世界
  [ADD] 无畏契约
  [ADD] Apex英雄

[OK] 成功添加 6 个游戏
```

---

### 步骤6: 添加示例文档

```bash
python scripts/add_sample_docs.py
```

**期望输出**:
```
============================================================
  添加示例文档
============================================================
[INFO] 初始化嵌入服务...
[OK] 嵌入模型: sentence-transformers/all-MiniLM-L6-v2
[OK] 向量维度: 384

[INFO] 准备添加 11 个文档...
  [1/11] [处理] 战士技能学习指南... [OK]
  [2/11] [处理] 组队系统说明... [OK]
  ...

[SUMMARY]
  新增: 11 个
  跳过: 0 个
```

---

## 🔍 验证数据库

### 方法1: 使用SQL查询

```sql
-- 连接到数据库
psql -U postgres -d rag_game_qa

-- 查看所有表
\dt

-- 查看游戏数据
SELECT game_id, game_name, version FROM games;

-- 查看文档数量
SELECT game_id, COUNT(*) FROM documents GROUP BY game_id;

-- 退出
\q
```

### 方法2: 使用Python脚本

创建 `scripts/check_db.py`:
```python
from config.database import SessionLocal, Game, Document

db = SessionLocal()

print("游戏列表:")
games = db.query(Game).all()
for game in games:
    doc_count = db.query(Document).filter(
        Document.game_id == game.game_id
    ).count()
    print(f"  {game.game_name}: {doc_count} 个文档")

db.close()
```

运行:
```bash
python scripts/check_db.py
```

---

## 📊 数据库表结构

### games (游戏信息表)
```sql
- id: 主键
- game_id: 游戏标识 (唯一)
- game_name: 游戏名称
- version: 版本号
- platforms: 支持平台 (JSON)
- languages: 支持语言 (JSON)
- created_at: 创建时间
- updated_at: 更新时间
```

### documents (文档表)
```sql
- id: 主键
- game_id: 游戏标识 (外键)
- content: 文档内容
- title: 标题
- category: 分类
- source: 来源
- metadata: 元数据 (JSON)
- embedding: 嵌入向量
- created_at: 创建时间
- updated_at: 更新时间
```

### query_logs (查询日志表)
```sql
- id: 主键
- game_id: 游戏标识
- user_id: 用户ID
- question: 问题
- answer: 答案
- confidence: 置信度
- processing_time: 处理时间
- retrieved_docs_count: 检索文档数
- user_context: 用户上下文 (JSON)
- created_at: 创建时间
```

其他表详见 `config/database.py`

---

## ❓ 常见问题

### Q1: 无法连接到数据库

**错误**: `could not connect to server: Connection refused`

**解决**:
1. 确认PostgreSQL服务正在运行
   ```cmd
   # Windows服务管理器
   services.msc
   # 查找 "postgresql-x64-14" 服务
   ```

2. 检查端口是否正确（默认5432）

3. 检查防火墙设置

### Q2: 密码认证失败

**错误**: `password authentication failed`

**解决**:
1. 确认 `.env` 中的密码正确
2. 重置PostgreSQL密码:
   ```sql
   ALTER USER postgres PASSWORD 'new_password';
   ```

### Q3: 数据库不存在

**错误**: `database "rag_game_qa" does not exist`

**解决**:
```sql
-- 连接到postgres数据库
psql -U postgres

-- 创建数据库
CREATE DATABASE rag_game_qa;
```

### Q4: 缺少psycopg2

**错误**: `No module named 'psycopg2'`

**解决**:
```bash
pip install psycopg2-binary
```

### Q5: 表已存在

**错误**: `table "xxx" already exists`

**解决**: 这是正常的，说明表已创建。如需重新创建：
```python
from config.database import drop_tables, create_tables

# 警告：这会删除所有数据！
drop_tables()
create_tables()
```

---

## 🛠️ 数据库管理

### 备份数据库

```bash
# 备份
pg_dump -U postgres -d rag_game_qa > backup.sql

# 恢复
psql -U postgres -d rag_game_qa < backup.sql
```

### 清空表数据

```sql
-- 连接到数据库
psql -U postgres -d rag_game_qa

-- 清空文档表
TRUNCATE TABLE documents CASCADE;

-- 清空所有表（保留结构）
TRUNCATE TABLE games, documents, query_logs, feedbacks, 
               user_profiles, health_records, analytics_data CASCADE;
```

### 删除数据库

```sql
-- 先断开所有连接
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = 'rag_game_qa';

-- 删除数据库
DROP DATABASE rag_game_qa;
```

---

## 📚 相关文件

| 文件 | 说明 |
|------|------|
| `config/database.py` | 数据库模型定义 |
| `scripts/init_db.py` | 数据库初始化脚本 |
| `scripts/add_sample_docs.py` | 添加示例文档 |
| `.env` | 数据库连接配置 |

---

## ✅ 验收标准

数据库配置完成后，应该能够：

- [x] 成功连接到PostgreSQL
- [x] 创建所有数据库表
- [x] 添加初始游戏数据（6个游戏）
- [x] 添加示例文档（11个文档）
- [x] 查询数据无错误

---

## 🚀 下一步

数据库配置完成后：

```bash
# 1. 测试检索功能
python scripts/test_retrieval.py

# 2. 启动API服务
python api/main.py

# 3. 测试问答功能
curl -X POST http://localhost:8000/api/v1/qa/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"魔兽世界中战士如何学习技能？","game_id":"wow"}'
```

---

**🎉 数据库配置完成！现在可以开始使用RAG系统了！**

