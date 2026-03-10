# RAG 游戏问答系统

这是一个给游戏资料问答用的 RAG 项目。现在这套代码已经把几个关键环节串起来了：本地知识库检索、联网补充、知识同步、问答反馈统计，以及一个可直接演示的 Web 界面。

目前默认带有多款游戏的样例数据，可以直接启动体验；如果你自己补充文档或接入外部数据库，也能继续往下扩展。

## 现在能做什么

- 基于本地文档做游戏问答
- 支持关键词检索、向量检索和可选重排序
- 本地结果不足时，支持联网补充
- 支持把联网结果写回数据库，作为后续 RAG 的知识来源
- 支持 SQLite 和 PostgreSQL
- 提供图形化页面、Swagger 文档和基础分析接口
- 支持反馈收集、优先级报告和 Jira 导出
- 保留了无障碍相关模块和多模态接口

## 运行环境

建议环境：

- Python 3.11
- Windows、Linux 都可以
- 如果要接 PostgreSQL，需要本地数据库服务可用

如果你只是想先把项目跑起来，不配置任何在线模型也没关系，系统会使用 `mock` 模式。

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 初始化数据

```bash
python scripts/init_db.py
```

这个脚本会初始化数据库，并导入样例游戏和样例文档。

### 3. 启动服务

```bash
python run_server.py
```

启动后默认可以访问：

- Web 界面：`http://localhost:8000/app`
- Swagger 文档：`http://localhost:8000/docs`
- 健康检查：`http://localhost:8000/health`

## 模型和 API Key 怎么配

项目不会要求你在网页里输入密钥。模型相关配置统一写在本地 Python 文件里：

`config/local_provider_config.py`

推荐做法：

1. 复制一份示例文件
2. 按你的情况填好 provider、model、api key
3. 重启服务

示例文件：

`config/local_provider_config.example.py`

这个本地配置文件已经被 `.gitignore` 忽略，不会被提交到远程仓库。

### 一个最小配置例子

```python
LOCAL_PROVIDER_CONFIG = {
    "AI_PROVIDER": "gemini",
    "GEMINI_API_KEY": "your-api-key",
    "GEMINI_MODEL": "gemini-2.5-flash",
}
```

如果你想用 NIM、Claude 或 Jira，也是改这个文件。

## 数据库说明

项目支持两种方式：

### SQLite

这是默认方案，开箱即用，适合本地开发和演示。

### PostgreSQL

如果你想把知识库、查询日志和反馈数据放到外部数据库，可以配置 PostgreSQL。

需要注意：

- 本地没装 PostgreSQL 驱动时，系统会自动回退到 SQLite
- PostgreSQL 服务不可达时，也会自动回退到 SQLite

常用检查命令：

```bash
python scripts/check_db_status.py
```

如果你准备启用 PostgreSQL，可以看看这些脚本：

- `python scripts/create_postgres_db.py`
- `python scripts/bootstrap_external_db.py`
- `python scripts/setup_database.py`

## 联网知识同步

这部分已经接上主流程了，不只是“联网查一下”，而是可以把联网抓到的内容落到库里，之后继续参与 RAG 检索。

常用脚本：

```bash
python scripts/sync_online_knowledge.py
```

图形界面里也可以直接操作：

- 同步当前游戏
- 保存自动同步计划
- 手动立即执行同步计划

## 常用脚本

下面这些脚本现在都还有实际用途：

| 脚本 | 作用 |
| --- | --- |
| `python scripts/init_db.py` | 初始化数据库和样例数据 |
| `python scripts/check_db_status.py` | 查看当前数据库连接状态 |
| `python scripts/test_all.py` | 跑一轮完整自检 |
| `python scripts/test_api.py` | 测试主要 API |
| `python scripts/sync_online_knowledge.py` | 把在线资料同步进知识库 |
| `python scripts/configure_sync_scheduler.py` | 配置自动同步计划 |
| `python scripts/export_priority_to_jira.py` | 导出反馈优先级到 Jira |

## 目录结构

```text
api/            FastAPI 入口和各类路由
accessibility/  分步引导、老年友好、家庭协作
config/         配置、数据库、运行时设置
core/           RAG 主流程、检索、生成、知识同步
data/           样例数据、本地数据库、爬虫来源
frontend/       Web 页面
integrations/   外部系统集成，目前主要是 Jira
multimodal/     语音、图像、触觉等模块
scripts/        初始化、测试、运维脚本
utils/          通用工具函数
deployment/     Docker 部署文件
```

## 当前项目里哪些内容是真正需要的

如果只看“运行这套系统”本身，核心需要的是：

- `api/`
- `accessibility/`
- `config/`
- `core/`
- `data/`
- `frontend/`
- `integrations/`
- `multimodal/`
- `utils/`
- `run_server.py`
- `requirements.txt`

下面这些更偏开发辅助，不影响主程序启动：

- `scripts/`
- `deployment/`
- `.env.example`
- `README.md`

另外有两类内容不属于项目源码本体：

- `.venv/`
- 所有 `__pycache__/`

它们是本地环境和运行缓存，本地可以保留，但不建议继续作为仓库内容的一部分。

## 已知情况

- 没有外部数据库时，系统会回退到 SQLite，这属于正常行为
- 没有在线模型 API Key 时，系统会走 `mock` 模式
- 如果环境里缺少 `sentence-transformers`，向量检索会降级，但服务仍然能启动

## 一个最常见的使用流程

```bash
pip install -r requirements.txt
python scripts/init_db.py
python run_server.py
```

然后：

1. 打开 `http://localhost:8000/app`
2. 先用默认样例数据体验问答
3. 如果需要真实模型，再去补 `config/local_provider_config.py`
4. 如果需要更完整的知识库，再跑联网同步
