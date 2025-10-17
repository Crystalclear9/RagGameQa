# 🚀 快速开始 - 环境配置指南

> 使用Claude API的RAG游戏问答系统配置指南

---

## 📋 前置要求

- Python 3.8+
- pip (Python包管理器)
- (可选) PostgreSQL 数据库
- (可选) Redis 缓存服务

---

## ⚡ 快速配置（3步完成）

### 方法1: 自动配置（推荐）

```bash
# 一键完成配置
python scripts/quick_setup.py
```

### 方法2: 手动配置

#### 步骤1: 创建环境配置

```bash
# 创建.env文件
python scripts/create_env.py
```

**或者手动创建 `.env` 文件，内容如下：**

```bash
# .env
AI_PROVIDER=claude
CLAUDE_API_KEY=cr_41127d92bf466a05017dc0fa1408bc0a2bde8e99f91f6752995a6f83756174ad
CLAUDE_MODEL=claude-3-5-sonnet-20241022
DATABASE_URL=postgresql://postgres:password@localhost:5432/rag_game_qa
```

#### 步骤2: 安装依赖

```bash
# 安装核心依赖
pip install anthropic python-dotenv fastapi uvicorn sentence-transformers

# 或安装完整依赖
pip install -r requirements.txt
```

#### 步骤3: 测试配置

```bash
# 运行配置测试
python scripts/test_config.py
```

---

## 🔍 配置测试说明

运行 `python scripts/test_config.py` 会测试以下内容：

| 测试项 | 说明 | 必需 |
|--------|------|------|
| ✅ .env文件检查 | 环境配置文件是否存在 | 是 |
| ✅ 配置加载 | 配置项是否正确加载 | 是 |
| ✅ Claude API | API连接是否正常 | 是 |
| ⚪ 数据库连接 | PostgreSQL是否可用 | 否* |
| ✅ 嵌入模型 | Sentence-Transformers | 是 |
| ✅ LLM生成器 | 完整的答案生成测试 | 是 |

\* 数据库非必需，但建议配置以使用完整功能

---

## 📊 测试输出示例

```
============================================================
  测试3: Claude API 连接测试
============================================================
✅ anthropic包安装
✅ API Key检查
   cr_41127d92bf466a05...

📡 发送测试请求到Claude API...
✅ API调用成功
   模型: claude-3-5-sonnet-20241022
   响应: 我是Claude，一个由Anthropic开发的AI助手...
```

---

## 🎯 支持的Claude模型

你的API Key可以使用以下模型：

| 模型名称 | 说明 | 推荐用途 |
|---------|------|---------|
| `claude-3-5-sonnet-20241022` | 最新版本，性能最佳 | 🌟 推荐 |
| `claude-3-5-sonnet-20240620` | 稳定版本 | 生产环境 |
| `claude-3-opus-20240229` | 最强性能 | 复杂任务 |
| `claude-3-sonnet-20240229` | 平衡性能 | 日常使用 |
| `claude-3-haiku-20240307` | 快速响应 | 简单查询 |

**修改模型**: 编辑 `.env` 文件中的 `CLAUDE_MODEL` 配置

---

## 🔧 配置详解

### Claude API 配置

```bash
# .env

# AI Provider (claude | openai)
AI_PROVIDER=claude

# Claude API配置
CLAUDE_API_KEY=cr_41127d92bf466a05017dc0fa1408bc0a2bde8e99f91f6752995a6f83756174ad
CLAUDE_API_BASE=https://api.anthropic.com
CLAUDE_MODEL=claude-3-5-sonnet-20241022
CLAUDE_MAX_TOKENS=2000
CLAUDE_TEMPERATURE=0.7
```

### 应用配置

```bash
# API服务配置
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# 日志级别
LOG_LEVEL=info
```

### 数据库配置（可选）

```bash
# PostgreSQL
DATABASE_URL=postgresql://postgres:password@localhost:5432/rag_game_qa

# Redis (缓存)
REDIS_URL=redis://localhost:6379
```

---

## ❓ 常见问题

### Q1: anthropic包安装失败？

```bash
# 尝试升级pip
python -m pip install --upgrade pip

# 重新安装
pip install anthropic
```

### Q2: Claude API调用失败？

检查：
1. API Key是否正确
2. 网络连接是否正常
3. 是否有代理设置

```bash
# 测试网络连接
curl https://api.anthropic.com
```

### Q3: 嵌入模型下载慢？

首次运行会下载模型文件（~100MB），可以：
1. 使用镜像源
2. 手动下载模型文件
3. 使用代理

### Q4: 数据库连接失败？

如果不需要数据库功能：
1. 可以先跳过数据库测试
2. 使用内存模式运行
3. 后续再配置数据库

---

## 📝 配置文件说明

| 文件 | 说明 | 必需 |
|------|------|------|
| `.env` | 环境变量配置 | ✅ 是 |
| `.env.example` | 配置模板 | 参考 |
| `config/settings.py` | 配置加载逻辑 | 只读 |
| `requirements.txt` | Python依赖 | 参考 |

---

## 🚀 启动服务

配置完成后：

```bash
# 启动API服务
python api/main.py

# 访问文档
浏览器打开: http://localhost:8000/docs
```

---

## 📞 需要帮助？

如果遇到问题：

1. 📖 查看 `CODE_FIX_CHECKLIST.md` 详细说明
2. 🔍 运行 `python scripts/test_config.py` 诊断问题
3. 📝 查看日志输出

---

**🎉 配置完成后，开始体验RAG游戏问答系统吧！**

