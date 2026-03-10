# RAG 游戏问答系统

这个项目现在已经不是单纯的接口骨架了。它可以用本地知识库做检索，也可以在结果不够时联网补充；可以跑 SQLite，也可以切到 PostgreSQL；有 FastAPI 接口，也有一个能直接演示问答、反馈、模块状态和知识同步的网页控制台。

目前默认支持 `mock`、`gemini`、`claude` 三种生成模式。模型密钥不再要求用户在网页里输入，而是放在本地 Python 配置文件中，已经被 `.gitignore` 忽略，不会被推到远程仓库。

## 现在能做什么

- 游戏问答主链路已经打通：检索、生成、来源返回、日志记录都能跑。
- 检索链路采用混合方案：`jieba + BM25 + 向量检索 + 可选 BERT 重排序`。
- 数据库支持 `SQLite` 和 `PostgreSQL`，PostgreSQL 不可用时会自动回退到 SQLite。
- 支持联网检索补充，且可以把在线资料手动同步进数据库，后续问答直接复用本地文档。
- 页面内可以直接演示问答、提交反馈、看查询统计、看模块核查、触发知识同步。
- 老年友好分步引导、祖孙协作模式已经接进主问答流程。

## 还没有彻底做完的部分

- 多模态接口已经预留，但目前还是轻量实现，不是完整生产版本。
- 爬虫模块和手动同步已经有了，真正稳定的定时调度和“分钟级更新”还没有补完。
- Jira 联动、NVIDIA NIM 推理优化还没做。

## 目录说明

```text
rag_game_qa_system/
├── api/                     # FastAPI 路由
├── config/                  # 配置、数据库、Provider
├── core/                    # RAG 主链路、检索器、知识库工具
├── accessibility/           # 老年友好 / 家庭协作
├── multimodal/              # 语音、图像、触觉接口
├── frontend/                # 网页控制台
├── data/                    # 样例知识、展示数据、SQLite 文件
└── scripts/                 # 建库、导数、状态检查、联网同步脚本
```

## 1. 安装依赖

```bash
pip install -r requirements.txt
```

如果你只想先跑起来，核心依赖至少要保证这些能装上：

```bash
pip install fastapi uvicorn sqlalchemy python-dotenv jieba requests sentence-transformers psycopg[binary]
```

## 2. 配置模型 API

先复制一份本地配置文件：

```bash
copy config\local_provider_config.example.py config\local_provider_config.py
```

然后直接编辑 `config/local_provider_config.py`，把你的 Provider 和 Key 写进去，例如：

```python
LOCAL_PROVIDER_CONFIG = {
    "AI_PROVIDER": "gemini",
    "GEMINI_API_KEY": "你的 key",
    "GEMINI_MODEL": "gemini-2.5-flash",
}
```

如果你想用 Claude，就把 `AI_PROVIDER` 改成 `claude`，再填 `CLAUDE_API_KEY` 和模型名。

这个文件已经在 `.gitignore` 里，不会被提交到远程仓库。

## 3. 启动项目

### 方案 A：先用本地 SQLite 跑通

这是最省事的方式，不需要额外装数据库。

```bash
python run_server.py
```

启动后可以访问：

- 网页控制台：[http://localhost:8000/app](http://localhost:8000/app)
- Swagger：[http://localhost:8000/docs](http://localhost:8000/docs)
- 健康检查：[http://localhost:8000/health](http://localhost:8000/health)

### 方案 B：使用 PostgreSQL

如果本地已经有 PostgreSQL，只需要把 `DATABASE_URL` 写到 `.env` 或 `config/local_provider_config.py` 里，例如：

```python
LOCAL_PROVIDER_CONFIG = {
    "DATABASE_URL": "postgresql://postgres:password@localhost:5432/rag_game_qa",
}
```

如果数据库还没建好，可以直接跑：

```bash
python scripts/create_postgres_db.py
python scripts/bootstrap_external_db.py
```

如果你本机没有 PostgreSQL，也可以先用 Docker 临时拉一个：

```bash
docker run --name rag-game-qa-postgres -e POSTGRES_PASSWORD=password -e POSTGRES_DB=rag_game_qa -p 5432:5432 -d postgres:15-alpine
```

然后再执行上面的建库和导数脚本。

## 4. 联网知识同步

现在系统里有两种“联网”方式：

1. 问答时临时联网补充。
2. 把在线资料同步进数据库，后续问答优先走本地库。

### 在网页里同步

打开控制台 [http://localhost:8000/app](http://localhost:8000/app)，找到“联网知识同步”卡片，点击“同步当前游戏”即可。

### 用脚本同步

```bash
python scripts/sync_online_knowledge.py --game-id wow
python scripts/sync_online_knowledge.py --game-id genshin --query 元素反应 --query 圣遗物 --top-k 2
```

### 用 API 同步

```bash
curl -X POST http://localhost:8000/api/v1/project/knowledge-sync \
  -H "Content-Type: application/json" \
  -d "{\"game_id\":\"wow\",\"max_results_per_query\":2}"
```

## 5. 常用接口

### 提问

```bash
curl -X POST http://localhost:8000/api/v1/qa/ask \
  -H "Content-Type: application/json" \
  -d "{\"game_id\":\"wow\",\"question\":\"战士如何学习技能？\",\"enable_web_retrieval\":true}"
```

### 查看项目总览

```bash
curl http://localhost:8000/api/v1/project/overview
```

### 查看数据库状态

```bash
python scripts/check_db_status.py
```

## 6. 页面里可以直接看的东西

- 系统当前用的 Provider 和模型
- 数据库后端、是否回退到 SQLite
- 当前知识库覆盖情况
- 模块实现状态核查
- 批量演示问题
- 查询统计、反馈统计、高频问题、优先级报告
- 联网知识是否已经同步入库

## 7. 排错建议

### 看到 `No module named 'psycopg2'`

这通常只是说明 PostgreSQL 驱动没装好，系统会退回 SQLite。想启用 PostgreSQL，安装下面任意一个即可：

```bash
pip install psycopg[binary]
```

或：

```bash
pip install psycopg2-binary
```

### 服务启动后马上退出

先检查：

```bash
python scripts/check_db_status.py
```

再确认：

- `config/local_provider_config.py` 语法没有写错
- `DATABASE_URL` 如果是 PostgreSQL，数据库真的已经启动
- 本地端口 `8000` 没被别的程序占用

## 8. 一个更实际的使用顺序

1. 先配置好 `config/local_provider_config.py`。
2. 跑 `python run_server.py`。
3. 打开 [http://localhost:8000/app](http://localhost:8000/app)。
4. 先在“联网知识同步”里给目标游戏同步一轮资料。
5. 再到“问答演示”里提问题。
6. 根据结果提交反馈，页面右侧看统计变化。

## 9. 说明

这个仓库现在已经把“只是接口壳子”和“真正能跑的 RAG 演示系统”区分开了。能跑通的部分已经尽量落到代码和页面里；还没做完的部分，也会在模块核查页里明确标出来，而不是写得很满。
