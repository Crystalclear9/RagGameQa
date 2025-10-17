# ⚡ 数据库快速配置（3分钟）

## 📋 前提条件

**PostgreSQL是否已安装？**

### ✅ 已安装PostgreSQL

继续下一步 →

### ❌ 未安装PostgreSQL

#### 快速安装（Windows）:

1. **下载**: https://www.postgresql.org/download/windows/
2. **安装**: 双击安装，记住设置的密码
3. **验证**: 
   ```cmd
   psql --version
   ```

---

## 🚀 快速开始（3步）

### 步骤1: 创建数据库（2分钟）

**方法A: 使用SQL Shell**（推荐）

```bash
# 1. 打开SQL Shell (psql)
# Windows: 开始菜单 → PostgreSQL → SQL Shell

# 2. 连接（全部回车，最后输入密码）
服务器 [localhost]: (回车)
数据库 [postgres]: (回车)  
端口 [5432]: (回车)
用户名 [postgres]: (回车)
密码: (输入你的PostgreSQL密码)

# 3. 创建数据库
CREATE DATABASE rag_game_qa;

# 4. 验证
\l    -- 应该看到 rag_game_qa
\q    -- 退出
```

**方法B: 如果没有PostgreSQL**

暂时跳过数据库，系统仍可运行（使用模拟数据）

---

### 步骤2: 更新配置（30秒）

编辑 `.env` 文件（在项目根目录）:

```bash
# 找到这一行，将 "password" 改为你的PostgreSQL密码
DATABASE_URL=postgresql://postgres:password@localhost:5432/rag_game_qa

# 例如，如果密码是 "123456":
DATABASE_URL=postgresql://postgres:123456@localhost:5432/rag_game_qa
```

---

### 步骤3: 运行初始化（30秒）

```bash
# 初始化数据库
python scripts/init_db.py
```

**期望看到**:
```
[OK] 连接成功!
[OK] 成功创建 7 个表
[OK] 成功添加 6 个游戏
```

**如果成功** → 继续添加示例数据：
```bash
python scripts/add_sample_docs.py
```

---

## ❓ 遇到问题？

### 问题1: `database "rag_game_qa" does not exist`

**解决**: 步骤1没有完成，需要创建数据库

### 问题2: `password authentication failed`

**解决**: `.env` 文件中的密码不正确

### 问题3: `could not connect to server`

**解决**: 
- PostgreSQL服务未启动
- 检查 Windows 服务管理器 (services.msc)
- 找到 "postgresql" 服务，点击启动

### 问题4: 没有安装PostgreSQL

**临时方案**: 
1. 暂时跳过数据库配置
2. 系统会使用内存模式运行
3. 后续安装PostgreSQL后再配置

---

## ✅ 验证

运行以下命令验证：

```bash
python scripts/init_db.py
```

如果看到 "完成!" 就成功了！

---

## 📚 完整文档

详细配置说明见: `DB_SETUP_GUIDE.md`

