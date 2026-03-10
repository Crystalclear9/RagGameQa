# RAG 游戏问答系统

这是一个面向游戏资料问答的 RAG 应用，提供本地知识库检索、联网补充检索、知识同步、反馈分析和 Web 控制台。项目默认可直接本地运行，也支持切换到 PostgreSQL 作为外部持久化数据库。

当前仓库已经整理为可以直接演示和继续开发的状态，日常使用主要围绕以下几部分：

- `FastAPI` 接口与 Swagger 文档
- `/app` 图形化界面
- 本地数据库检索与联网知识同步
- 问答日志、反馈统计、优先级分析
- Jira 导出

## 目录结构

```text
api/            FastAPI 入口与路由
accessibility/  分步引导、家庭协作等辅助模块
config/         配置、数据库、运行时设置
core/           RAG 主流程、检索与知识同步
data/           示例数据、爬虫和本地数据库文件
frontend/       Web 图形界面
integrations/   外部系统集成
multimodal/     语音、图像、触觉相关模块
scripts/        初始化、测试、同步和运维脚本
utils/          通用工具与安全处理
deployment/     Docker 相关文件
```

## 运行环境

- Python 3.11
- Windows 或 Linux
- 可选：PostgreSQL
- 可选：Gemini、Claude、NVIDIA NIM 的 API Key

如果暂时不接入在线模型，可以直接使用 `mock` 模式启动项目。

## 配置机制

项目配置分为两层：

1. `.env`
2. `config/local_provider_config.py`

最终生效顺序如下：

`config/local_provider_config.py` > `.env`

也就是说，若两个位置都定义了同名字段，以 `config/local_provider_config.py` 为准。

推荐做法：

- 服务地址、数据库、RAG 行为开关放在 `.env`
- API Key、模型名称、Jira 凭据放在 `config/local_provider_config.py`

`config/local_provider_config.py` 已加入 `.gitignore`，不会被提交到远程仓库。

## 安装与准备

### 1. 安装依赖

PowerShell:

```powershell
pip install -r requirements.txt
```

如果要使用 PostgreSQL，建议额外安装驱动：

```powershell
pip install psycopg[binary]
```

### 2. 复制配置模板

```powershell
Copy-Item .env.example .env
Copy-Item config\local_provider_config.example.py config\local_provider_config.py
```

### 3. 准备模型配置

实际模型和密钥建议写在 `config/local_provider_config.py` 中，不建议通过网页输入。

最小可运行配置：

```python
LOCAL_PROVIDER_CONFIG = {
    "AI_PROVIDER": "mock",
}
```

Gemini 配置示例：

```python
LOCAL_PROVIDER_CONFIG = {
    "AI_PROVIDER": "gemini",
    "GEMINI_API_KEY": "your-gemini-api-key",
    "GEMINI_MODEL": "gemini-2.5-flash",
    "GEMINI_API_BASE": "https://generativelanguage.googleapis.com/v1beta",
}
```

Claude 配置示例：

```python
LOCAL_PROVIDER_CONFIG = {
    "AI_PROVIDER": "claude",
    "CLAUDE_API_KEY": "your-claude-api-key",
    "CLAUDE_MODEL": "claude-sonnet-4-6",
    "CLAUDE_API_BASE": "https://api.anthropic.com",
    "CLAUDE_API_VERSION": "2023-06-01",
}
```

NVIDIA NIM 配置示例：

```python
LOCAL_PROVIDER_CONFIG = {
    "AI_PROVIDER": "nim",
    "NIM_API_KEY": "your-nim-api-key",
    "NIM_API_BASE": "https://integrate.api.nvidia.com/v1",
    "NIM_MODEL": "meta/llama-3.1-70b-instruct",
}
```

说明：

- 上述模型名是仓库当前默认示例，可按你的账号权限替换为同提供方支持的模型
- 修改 `config/local_provider_config.py` 后，需要重启服务
- 真实密钥不要写入 `.env.example`、README 或前端页面

## 启动方式

项目有两条推荐路径：本地快速演示和外部 PostgreSQL 部署。

### 路径 A：本地快速演示（SQLite）

适合第一次跑通、课程展示和单机调试。

#### 步骤 1：保持默认数据库配置

`.env.example` 中默认的 `DATABASE_URL` 指向 PostgreSQL，但应用在启动时会自动检测数据库可用性。

如果当前环境没有 PostgreSQL 驱动或服务不可达，系统会自动回退到：

`data/rag_game_qa.db`

这是当前项目的 SQLite 回退库。

#### 步骤 2：可选，先同步一批知识

如果你希望启动后就能直接问到一些内容，建议先执行一次知识同步：

```powershell
python scripts/sync_online_knowledge.py --game-id genshin
```

也可以指定查询词：

```powershell
python scripts/sync_online_knowledge.py --game-id wow --query "warrior abilities" --query "dungeon finder"
```

这条脚本会：

- 自动创建当前数据库中的表
- 自动补齐游戏记录
- 从联网检索结果中写入知识文档

如果你想做离线演示，也可以先启动服务一次创建 SQLite 表，再执行：

```powershell
python scripts/add_sample_docs.py
```

#### 步骤 3：启动服务

```powershell
python run_server.py
```

默认地址：

- Web 界面：`http://localhost:8000/app`
- Swagger 文档：`http://localhost:8000/docs`
- 健康检查：`http://localhost:8000/health`

#### 步骤 4：确认当前数据库状态

```powershell
python scripts/check_db_status.py
```

重点关注以下字段：

- `Requested backend`
- `Active backend`
- `Using fallback`
- `Active URL`

如果 `Using fallback: True`，说明当前正在使用 SQLite。

### 路径 B：接入 PostgreSQL

适合需要稳定持久化、多人共享数据库或后续部署的场景。

#### 步骤 1：确认 `.env` 中的数据库地址

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/rag_game_qa
```

#### 步骤 2：创建数据库

```powershell
python scripts/create_postgres_db.py
```

#### 步骤 3：初始化表并写入样例数据

```powershell
python scripts/bootstrap_external_db.py
```

这个脚本会：

- 验证当前活动数据库确实是 PostgreSQL
- 创建表结构
- 写入 `data/sample_data.json` 中的游戏和文档
- 在可用时生成嵌入向量

#### 步骤 4：检查连接状态

```powershell
python scripts/check_db_status.py
```

如果输出中 `Using fallback: False`，说明当前已经真正接入外部 PostgreSQL。

#### 步骤 5：启动服务

```powershell
python run_server.py
```

## 关键配置项

### `.env`

以下参数最常用：

| 字段 | 默认值 | 说明 |
| --- | --- | --- |
| `API_HOST` | `0.0.0.0` | 服务监听地址 |
| `API_PORT` | `8000` | 服务端口 |
| `DATABASE_URL` | `postgresql://postgres:password@localhost:5432/rag_game_qa` | 主数据库地址 |
| `AI_PROVIDER` | `mock` | 默认提供方，可被 Python 配置覆盖 |
| `RAG_DATA_MODE` | `database` | 可选 `database`、`memory`、`auto` |
| `TOP_K_RESULTS` | `5` | 默认召回文档数 |
| `ENABLE_WEB_RETRIEVAL` | `True` | 是否允许本地结果不足时触发联网补充 |
| `WEB_RETRIEVAL_TRIGGER_DOC_COUNT` | `2` | 本地文档少于该值时触发联网补充 |
| `WEB_RETRIEVAL_MAX_RESULTS` | `3` | 单次联网检索的最大结果数 |
| `ENABLE_BERT_RERANKER` | `False` | 是否启用 BERT 重排序 |
| `KNOWLEDGE_SYNC_SCHEDULER_ENABLED` | `False` | 是否启用自动同步计划 |
| `KNOWLEDGE_SYNC_INTERVAL_MINUTES` | `60` | 自动同步间隔，单位分钟 |
| `KNOWLEDGE_SYNC_GAMES` | `wow,lol,genshin` | 自动同步的游戏列表 |

### `config/local_provider_config.py`

这个文件建议保存所有敏感配置，例如：

- `GEMINI_API_KEY`
- `CLAUDE_API_KEY`
- `NIM_API_KEY`
- `JIRA_API_TOKEN`
- 具体模型名

常用字段如下：

| 字段 | 说明 |
| --- | --- |
| `AI_PROVIDER` | 当前使用的模型提供方 |
| `GEMINI_API_KEY` | Gemini API Key |
| `GEMINI_MODEL` | Gemini 模型名 |
| `CLAUDE_API_KEY` | Claude API Key |
| `CLAUDE_MODEL` | Claude 模型名 |
| `NIM_API_KEY` | NVIDIA NIM API Key |
| `NIM_MODEL` | NIM 使用的模型名 |
| `JIRA_BASE_URL` | Jira 实例地址 |
| `JIRA_EMAIL` | Jira 登录邮箱 |
| `JIRA_API_TOKEN` | Jira API Token |
| `JIRA_PROJECT_KEY` | Jira 项目标识 |

## 图形界面使用

启动后访问：

`http://localhost:8000/app`

界面主要分为四个区域：

### 1. 系统概览

用于查看：

- 当前数据库后端
- 当前 provider 状态
- 已接入模块
- 项目接口清单
- 模块核查结果

### 2. 知识同步

用于：

- 同步当前游戏的联网知识
- 配置自动同步计划
- 立即执行一次计划任务
- 查看最近同步状态
- 预览或创建 Jira 导出

### 3. 问答演示

建议使用顺序：

1. 选择游戏
2. 选择用户类型
3. 选择来源数量
4. 按需勾选联网补充、分步引导、祖孙协作模式
5. 输入问题并提交

结果页会返回：

- 回答内容
- 置信度
- 来源文档
- 分步引导结果
- 协作摘要

### 4. 数据看板

可查看：

- 近 7 天查询次数
- 平均置信度
- 平均耗时
- 高频问题
- 优先级报告

## API 使用

Swagger 文档：

`http://localhost:8000/docs`

下面列几个常用接口。

### 1. 问答接口

`POST /api/v1/qa/ask`

示例请求：

```json
{
  "question": "原神里蒸发反应怎么触发？",
  "game_id": "genshin",
  "top_k": 5,
  "include_sources": true,
  "enable_web_retrieval": true,
  "user_context": {
    "user_id": "demo-user",
    "user_type": "normal"
  }
}
```

### 2. 联网知识同步

`POST /api/v1/project/knowledge-sync`

示例请求：

```json
{
  "game_id": "wow",
  "max_results_per_query": 2
}
```

### 3. 自动同步计划

- `GET /api/v1/project/knowledge-sync/scheduler`
- `POST /api/v1/project/knowledge-sync/scheduler`
- `POST /api/v1/project/knowledge-sync/scheduler/run`

### 4. 统计与分析

- `GET /api/v1/analytics/query-stats`
- `GET /api/v1/analytics/priority-report`
- `POST /api/v1/analytics/feedback`
- `POST /api/v1/analytics/jira/export`

### 5. 模块核查

`GET /api/v1/project/module-audit`

这个接口可以直接查看当前项目设计模块的实现状态。

## 常用脚本

```powershell
python run_server.py
python scripts/check_db_status.py
python scripts/sync_online_knowledge.py --game-id wow
python scripts/create_postgres_db.py
python scripts/bootstrap_external_db.py
python scripts/add_sample_docs.py
python scripts/simple_test.py
python scripts/test_all.py
```

脚本用途说明：

- `run_server.py`：启动服务
- `check_db_status.py`：查看当前实际使用的数据库后端
- `sync_online_knowledge.py`：拉取联网知识并写入数据库
- `create_postgres_db.py`：创建 PostgreSQL 数据库
- `bootstrap_external_db.py`：初始化外部 PostgreSQL 并写入样例数据
- `add_sample_docs.py`：添加本地样例文档
- `simple_test.py` / `test_all.py`：基础检查与测试

补充说明：

- `scripts/init_db.py` 更适合在 PostgreSQL 已经准备好之后使用
- 如果本机没有 PostgreSQL，不建议把 `scripts/init_db.py` 当作第一次启动入口
- 对于纯本地演示，优先使用 `run_server.py` + SQLite 回退，或使用 `sync_online_knowledge.py` 先补一批数据

## Jira 配置

如果需要把反馈导出到 Jira，可在 `config/local_provider_config.py` 中增加：

```python
LOCAL_PROVIDER_CONFIG = {
    "JIRA_BASE_URL": "https://your-domain.atlassian.net",
    "JIRA_EMAIL": "your-email@example.com",
    "JIRA_API_TOKEN": "your-jira-api-token",
    "JIRA_PROJECT_KEY": "RAG",
}
```

配置完成后，可以在图形界面中预览当前游戏导出，也可以直接调用：

`POST /api/v1/analytics/jira/export`

## 故障排查

### 1. 启动时提示 PostgreSQL 连接失败

这通常说明发生了两种情况之一：

- PostgreSQL 驱动未安装
- PostgreSQL 服务不可达

如果服务随后仍然正常启动，通常表示系统已经自动切换到 SQLite，不影响本地演示。

### 2. `scripts/init_db.py` 直接失败

这不是前端或 API 的问题，而是该脚本默认按 `.env` 中的 `DATABASE_URL` 直接连接数据库。

如果当前没有可用 PostgreSQL，请改用以下流程：

1. `python run_server.py`
2. `python scripts/check_db_status.py`
3. `python scripts/sync_online_knowledge.py --game-id genshin`

### 3. 改了 API Key 但没有生效

按顺序检查：

1. 是否修改的是 `config/local_provider_config.py`
2. `AI_PROVIDER` 是否与对应密钥匹配
3. 修改后是否重启了 `python run_server.py`

### 4. 问答能返回，但来源为空或结果较弱

通常有以下原因：

- 本地数据库中尚未写入足够文档
- 嵌入模型没有成功加载
- 联网检索被关闭

建议先执行一次：

```powershell
python scripts/sync_online_knowledge.py --game-id genshin
```

### 5. 如何确认当前到底是 SQLite 还是 PostgreSQL

```powershell
python scripts/check_db_status.py
```

输出中的 `Active backend` 和 `Using fallback` 即为最终结果。

## 安全说明

- `config/local_provider_config.py` 已被忽略，不会进入 Git
- `.venv` 和 `__pycache__` 已停止跟踪，不会再推送到远程仓库
- 服务端日志会对敏感信息做脱敏处理
- 不建议把真实密钥写入前端页面或公开脚本
