# RAG 游戏问答智能体 (GameQA)

> 基于 **检索增强生成 (RAG)** 架构的游戏领域智能问答系统。支持多游戏知识库、多模型热切换、联网知识同步与现代化聊天交互界面。

---

## ✨ 功能亮点

| 模块 | 能力 |
|------|------|
| **RAG 核心引擎** | BM25 + Sentence-Transformers 混合检索，可选 BERT 重排序 |
| **多模型架构** | DeepSeek / Gemini / Claude / NVIDIA NIM / Mock 一键切换 |
| **现代化 Chat UI** | 粒子动画品牌标识、多会话管理、实时对话交互 |
| **智能容错** | 自动重试（最多 3 次）、请求中止与撤回、120s 超时保底 |
| **自定义游戏领域** | 内置魔兽世界/英雄联盟/原神/我的世界，支持任意添加/删除 |
| **会话管理** | LocalStorage 持久化、多会话并行、一键新建/删除 |
| **黑话别名容忍** | LLM 自动映射游戏社区黑话（如"皇子" → "嘉文四世"） |
| **联网知识同步** | 本地知识不足时自动触发联网补充检索 |
| **知识同步调度** | 支持定时自动同步与手动触发 |
| **辅助功能** | 分步引导模式、长辈/祖孙协作模式 |
| **数据库双模式** | PostgreSQL（生产）+ SQLite（自动回退） |
| **多模态（实验）** | BLIP-2 图像描述、Wav2Vec2.0 语音/方言识别 |
| **数据分析** | 查询统计、置信度分析、优先级报告、Jira 导出 |

---

## 📁 项目结构

```text
rag_game_qa_system/
├── api/                FastAPI 入口、路由与中间件
│   ├── main.py         应用主入口（含安全中间件、缓存控制）
│   └── routes/         qa / analytics / project / runtime / multimodal / health 路由
├── accessibility/      辅助功能模块
│   └── elderly_support/  分步引导、家庭协作、触觉反馈
├── config/             配置层
│   ├── settings.py     全局配置类（含所有模型参数、超时、RAG 开关）
│   ├── database.py     数据库初始化与 SQLite 回退逻辑
│   ├── local_provider_config.py          ← 你的私有配置（已 .gitignore）
│   └── local_provider_config.example.py  ← 配置模板
├── core/               核心业务逻辑
│   ├── generator/      LLM 生成器（含 DeepSeek/Gemini/Claude/NIM 调用）
│   │   ├── llm_generator.py    多模型统一调用 + 系统提示词工程
│   │   ├── domain_adapter.py   游戏领域适配器
│   │   └── response_formatter.py 回答格式化
│   ├── retriever/      检索层（BM25 + 向量检索 + BERT 重排序）
│   ├── rag_engine.py   RAG 主流程编排
│   └── knowledge_base/ 知识库管理与同步调度
├── data/               数据存储
│   ├── rag_game_qa.db  SQLite 数据库文件
│   ├── sample_data.json 示例游戏知识
│   └── crawlers/       分布式爬虫
├── frontend/           Web 前端
│   ├── index.html      页面结构（粒子 Logo、侧边栏、聊天区）
│   ├── styles.css      样式系统（手风琴动画、头像交互、停止按钮）
│   └── app.js          应用逻辑（会话管理、重试、中止、自定义领域）
├── multimodal/         多模态模块
│   ├── speech/         ASR 语音识别、方言识别
│   └── visual/         BLIP-2 图像描述
├── integrations/       外部集成
│   └── jira/           Jira 问题导出
├── scripts/            运维与初始化脚本
├── deployment/         Docker 部署配置
├── utils/              通用工具（安全脱敏、文本处理）
├── run_server.py       一键启动入口
└── requirements.txt    Python 依赖清单
```

---

## 🖥️ 图形界面详解

启动服务后访问 `http://localhost:8000/app`，界面采用现代化聊天风格设计。

### 侧边栏（左侧）

| 区域 | 功能 |
|------|------|
| **品牌标识** | HTML5 Canvas 粒子动画网络 Logo |
| **新对话** | 一键创建新会话，自动继承当前选中的游戏领域 |
| **游戏领域选择** | 可折叠手风琴面板，内置 4 款游戏，支持点击切换 |
| **自定义游戏输入** | 输入框 + `+` 按钮，可动态添加任意游戏领域（如"黑神话悟空"） |
| **自定义领域删除** | 每个自定义领域徽章右侧带红色 `×` 一键移除 |
| **历史会话列表** | 显示所有会话标题，支持点击切换、悬停显示删除按钮 |

### 聊天主区域（右侧）

| 功能 | 说明 |
|------|------|
| **实时对话** | 类 ChatGPT 式气泡布局，支持长文本自动换行 |
| **头像动画交互** | 点击机器人头像触发 360° 旋转 + 蓝色光晕爆发；点击用户头像触发弹性摇晃 + 水波纹扩散 |
| **发送 / 停止按钮** | 发送后按钮变为红色脉冲 ⏹ 停止按钮，可随时中止请求 |
| **中止撤回** | 点击停止后，用户消息与加载气泡完全从界面和会话中删除，问题自动回填输入框 |
| **自动重试** | 检测到"连接失败"或超时后自动重试最多 3 次，显示"第 N/3 次重试中" |
| **失败可编辑** | 3 次重试仍失败时，点击错误消息气泡可将问题还原到输入框重新编辑发送 |
| **检索来源** | 回答下方展示知识来源文档出处 |
| **置信度** | 底栏实时显示生成状态与置信度评分 |

### 插件面板

| 插件 | 说明 |
|------|------|
| **联网搜索** | 本地知识不足时自动触发在线检索补充 |
| **分步辅助** | 生成更详细的操作步骤向导 |
| **长辈模式** | 精简易懂的回答口吻，适合非核心玩家 |
| **语音输入** | 基于 Web Speech API 的语音识别输入 |

---

## ⚙️ 运行环境

- **Python** 3.11+
- **操作系统**：Windows / Linux / macOS
- **可选**：PostgreSQL（推荐用于生产环境）
- **可选**：模型 API Key（DeepSeek / Gemini / Claude / NVIDIA NIM）

> 没有模型 API Key？可使用 `mock` 模式立即启动体验界面。

---

## 🚀 快速开始

### 1. 安装依赖

```powershell
pip install -r requirements.txt
```

如需 PostgreSQL 支持：

```powershell
pip install psycopg[binary]
```

### 2. 复制配置模板

```powershell
Copy-Item .env.example .env
Copy-Item config\local_provider_config.example.py config\local_provider_config.py
```

### 3. 配置模型（按需选择一种）

编辑 `config/local_provider_config.py`：

**最小可运行（无需 API Key）：**

```python
LOCAL_PROVIDER_CONFIG = {
    "AI_PROVIDER": "mock",
}
```

**DeepSeek 配置（推荐）：**

```python
LOCAL_PROVIDER_CONFIG = {
    "AI_PROVIDER": "deepseek",
    "DEEPSEEK_API_KEY": "your-deepseek-api-key",
    "DEEPSEEK_API_BASE": "https://api.siliconflow.cn/v1",   # 或 https://api.deepseek.com/v1
    "DEEPSEEK_MODEL": "deepseek-ai/DeepSeek-V3",
}
```

**Gemini 配置：**

```python
LOCAL_PROVIDER_CONFIG = {
    "AI_PROVIDER": "gemini",
    "GEMINI_API_KEY": "your-gemini-api-key",
    "GEMINI_MODEL": "gemini-2.5-flash",
    "GEMINI_API_BASE": "https://generativelanguage.googleapis.com/v1beta",
}
```

**Claude 配置：**

```python
LOCAL_PROVIDER_CONFIG = {
    "AI_PROVIDER": "claude",
    "CLAUDE_API_KEY": "your-claude-api-key",
    "CLAUDE_MODEL": "claude-sonnet-4-6",
    "CLAUDE_API_BASE": "https://api.anthropic.com",
    "CLAUDE_API_VERSION": "2023-06-01",
}
```

**NVIDIA NIM 配置：**

```python
LOCAL_PROVIDER_CONFIG = {
    "AI_PROVIDER": "nim",
    "NIM_API_KEY": "your-nim-api-key",
    "NIM_API_BASE": "https://integrate.api.nvidia.com/v1",
    "NIM_MODEL": "meta/llama-3.1-70b-instruct",
}
```

> ⚠️ 修改配置后需要重启服务。密钥不要写入 `.env.example`、README 或前端页面。

### 4. 启动服务

```powershell
python run_server.py
```

默认地址：

| 入口 | 地址 |
|------|------|
| **Web 界面** | `http://localhost:8000/app` |
| **Swagger 文档** | `http://localhost:8000/docs` |
| **健康检查** | `http://localhost:8000/health` |

---

## 📚 配置机制

项目配置分为两层，生效优先级如下：

```
config/local_provider_config.py  >  .env  >  代码默认值
```

**推荐做法：**

- 服务地址、数据库、RAG 行为开关 → 放在 `.env`
- API Key、模型名称、Jira 凭据 → 放在 `config/local_provider_config.py`

`config/local_provider_config.py` 已加入 `.gitignore`，不会被提交到远程仓库。

### 关键配置项（`.env`）

| 字段 | 默认值 | 说明 |
|------|--------|------|
| `API_HOST` | `0.0.0.0` | 服务监听地址 |
| `API_PORT` | `8000` | 服务端口 |
| `DATABASE_URL` | `postgresql://...` | 主数据库地址 |
| `AI_PROVIDER` | `mock` | 模型提供方 |
| `RAG_DATA_MODE` | `database` | `database` / `memory` / `auto` |
| `TOP_K_RESULTS` | `5` | 默认召回文档数 |
| `ENABLE_WEB_RETRIEVAL` | `True` | 联网补充检索开关 |
| `WEB_RETRIEVAL_TRIGGER_DOC_COUNT` | `2` | 本地文档少于该值时触发联网 |
| `WEB_RETRIEVAL_MAX_RESULTS` | `3` | 单次联网最大结果数 |
| `TIMEOUT_SECONDS` | `120` | LLM 请求超时（秒） |
| `ENABLE_BERT_RERANKER` | `False` | BERT 重排序开关 |
| `KNOWLEDGE_SYNC_SCHEDULER_ENABLED` | `False` | 自动同步计划开关 |
| `KNOWLEDGE_SYNC_INTERVAL_MINUTES` | `60` | 自动同步间隔（分钟） |
| `KNOWLEDGE_SYNC_GAMES` | `wow,lol,genshin` | 自动同步的游戏列表 |

### 敏感配置项（`config/local_provider_config.py`）

| 字段 | 说明 |
|------|------|
| `AI_PROVIDER` | 当前使用的模型提供方 |
| `DEEPSEEK_API_KEY` / `DEEPSEEK_API_BASE` / `DEEPSEEK_MODEL` | DeepSeek 配置 |
| `GEMINI_API_KEY` / `GEMINI_MODEL` | Gemini 配置 |
| `CLAUDE_API_KEY` / `CLAUDE_MODEL` | Claude 配置 |
| `NIM_API_KEY` / `NIM_MODEL` | NIM 配置 |
| `JIRA_BASE_URL` / `JIRA_EMAIL` / `JIRA_API_TOKEN` / `JIRA_PROJECT_KEY` | Jira 导出 |

---

## 🗄️ 数据库部署

### 路径 A：本地快速演示（SQLite，零配置）

系统启动时自动检测 PostgreSQL 可用性，不可达时**自动回退到 SQLite**（`data/rag_game_qa.db`），无需任何额外操作。

```powershell
python run_server.py
```

可选：先同步一批知识以获得更好的问答效果：

```powershell
python scripts/sync_online_knowledge.py --game-id lol
python scripts/add_sample_docs.py
```

### 路径 B：Windows 一键 PostgreSQL（无需 Docker）

```powershell
.\scripts\setup_postgres_windows.ps1
```

> 无需管理员权限，自动下载、解压并绑定在项目本地。

### 路径 C：生产级 PostgreSQL

```powershell
# 1. 配置 .env 中的 DATABASE_URL
# 2. 创建数据库
python scripts/create_postgres_db.py

# 3. 初始化表与样例数据
python scripts/bootstrap_external_db.py

# 4. 确认连接状态
python scripts/check_db_status.py

# 5. 启动
python run_server.py
```

---

## 🔌 API 接口

Swagger 交互文档：`http://localhost:8000/docs`

### 问答

```
POST /api/v1/qa/ask
```

```json
{
  "question": "原神里蒸发反应怎么触发？",
  "game_id": "genshin",
  "top_k": 5,
  "include_sources": true,
  "enable_web_retrieval": true,
  "include_assistive_guide": false,
  "include_family_guide": false,
  "user_context": { "user_id": "web-user", "user_type": "normal" }
}
```

### 知识同步

```
POST /api/v1/project/knowledge-sync
```

```json
{
  "game_id": "wow",
  "max_results_per_query": 2
}
```

### 同步调度

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/project/knowledge-sync/scheduler` | 查看调度状态 |
| POST | `/api/v1/project/knowledge-sync/scheduler` | 配置调度计划 |
| POST | `/api/v1/project/knowledge-sync/scheduler/run` | 立即执行一次 |

### 统计与分析

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/analytics/query-stats` | 查询统计 |
| GET | `/api/v1/analytics/priority-report` | 优先级报告 |
| POST | `/api/v1/analytics/feedback` | 提交反馈 |
| POST | `/api/v1/analytics/jira/export` | 导出到 Jira |

### 运行时配置

```
GET  /api/v1/runtime/config
PUT  /api/v1/runtime/config
```

### 模块核查

```
GET /api/v1/project/module-audit
```

### 多模态（实验性）

```
POST /api/v1/multimodal/image-describe    # 图像描述
POST /api/v1/multimodal/speech-recognize   # 语音识别
```

### 健康检查

```
GET /health
GET /api/v1/health/detailed
```

---

## 🧠 LLM 提示词工程

系统在 `core/generator/llm_generator.py` 中实现了精心设计的提示词策略：

### 黑话/俗名容忍规则

LLM 被指示使用内建的游戏知识自动映射社区俗称到官方名称：

- "皇子" → 德玛西亚皇子·嘉文四世
- "瞎子" → 盲僧·李青
- "大树" → 扭曲树精·茂凯

### 详尽输出规则

强制要求 LLM 提供结构化的长篇详细回答，包含：分阶段分析、数值数据、装备路线、符文推荐等，防止输出被截断或过于简短。

### 安全兜底

当检索到的知识库内容不足且无法通过游戏常识判断时，LLM 会明确告知用户"未找到相关资料"，不会编造信息。

---

## 🛠️ 常用脚本

| 脚本 | 用途 |
|------|------|
| `python run_server.py` | 启动服务 |
| `python scripts/check_db_status.py` | 查看当前数据库后端状态 |
| `python scripts/sync_online_knowledge.py --game-id wow` | 拉取联网知识 |
| `python scripts/add_sample_docs.py` | 添加本地示例文档 |
| `python scripts/create_postgres_db.py` | 创建 PostgreSQL 数据库 |
| `python scripts/bootstrap_external_db.py` | 初始化 PostgreSQL 并写入样例 |
| `.\scripts\setup_postgres_windows.ps1` | Windows 一键安装 PostgreSQL |
| `python scripts/simple_test.py` | 基础功能检查 |
| `python scripts/test_all.py` | 完整测试套件 |

---

## 🔧 前端技术实现

### 粒子动画 Logo

使用 HTML5 Canvas 绘制 Plexus 粒子网络作为品牌标识，粒子在 32×32 画布中实时运动并连线，营造科技感。

### 会话管理

- 基于 `localStorage` 的多会话持久化存储
- 每个会话独立绑定游戏领域 (`gameId`)
- 会话标题自动从第一个问题中提取
- 删除会话时自动继承当前活跃的游戏领域，不会强制重置

### 手风琴折叠

游戏领域列表支持点击标题折叠/展开，带有 CSS 过渡动画（`max-height` + `opacity` 渐变），箭头图标同步旋转。

### 头像交互动画

| 头像 | CSS 动画 |
|------|----------|
| 机器人 | `avatar-spin-glow`：360° 旋转 + 蓝色 `drop-shadow` 光晕渐变 |
| 用户 | `avatar-bounce`：弹性缩放 + 左右摇晃 |
| 通用 | `ripple-expand`：从头像中心扩散的水波纹环 |

### 请求中止 (AbortController)

- 发送按钮在请求期间变为红色脉冲 ⏹ 停止按钮
- 使用 `AbortController` + `signal` 实现真正的 HTTP 请求取消
- 中止后从 DOM 和 `localStorage` 中完全删除用户消息和加载气泡
- 原问题自动回填到输入框供编辑后重新发送

### 自动重试

- 前端检测响应文本中的失败关键词（`连接失败`、`请求异常`、`请稍后重试`、`timeout`）
- 自动循环重试最多 3 次，加载气泡实时显示重试进度
- 3 次失败后允许点击错误消息还原问题

### 静态资源缓存控制

服务器中间件对 `/assets/` 路径强制设置 `Cache-Control: no-store, no-cache, max-age=0, must-revalidate`，配合 `?v=` 版本号参数，确保每次重启后浏览器加载最新文件。

---

## ❓ 故障排查

### 启动时提示 PostgreSQL 连接失败

正常现象。系统会自动回退到 SQLite，不影响使用。检查方式：

```powershell
python scripts/check_db_status.py
```

关注 `Using fallback` 和 `Active backend` 字段。

### DeepSeek 连接失败 / 超时

1. 检查 API Key 是否正确配置在 `config/local_provider_config.py`
2. 检查 `DEEPSEEK_API_BASE` 是否可达（可能需要代理）
3. 系统默认超时已设置为 **120 秒**，且前端自动重试 **3 次**
4. 如果使用 SiliconFlow 等三方托管，高峰期可能需要更长等待

### 改了 API Key 但没有生效

按顺序检查：

1. 修改的是否是 `config/local_provider_config.py`（而不是 `.env.example`）
2. `AI_PROVIDER` 是否与密钥类型匹配
3. 修改后是否重启了服务

### 问答结果为空或结果质量差

1. 数据库中可能尚未写入足够的知识文档
2. 执行知识同步：`python scripts/sync_online_knowledge.py --game-id lol`
3. 确保 `ENABLE_WEB_RETRIEVAL` 为 `True`

### 浏览器加载的是旧版界面

1. 已在服务端强制禁用 `/assets/` 路径的缓存
2. 按 `Ctrl + F5` 硬刷新页面
3. 检查 HTML 中的 `?v=` 版本号是否已更新

---

## 🔐 安全说明

- `config/local_provider_config.py` 已加入 `.gitignore`，不会提交到 Git
- `.venv` 和 `__pycache__` 已停止跟踪
- 服务端日志对敏感信息（API Key、数据库连接串）做自动脱敏处理
- HTTP 响应头自动设置 `X-Content-Type-Options`、`X-Frame-Options`、`Referrer-Policy` 等安全头
- 不建议将真实密钥写入前端页面或公开脚本

---

## 🤝 Jira 集成

在 `config/local_provider_config.py` 中配置 Jira 凭据：

```python
LOCAL_PROVIDER_CONFIG = {
    "JIRA_BASE_URL": "https://your-domain.atlassian.net",
    "JIRA_EMAIL": "your-email@example.com",
    "JIRA_API_TOKEN": "your-jira-api-token",
    "JIRA_PROJECT_KEY": "RAG",
}
```

配置完成后可在 Web 界面中预览导出，或调用 `POST /api/v1/analytics/jira/export`。

---

## 📄 License

本项目仅供学习与研究用途。
