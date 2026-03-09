# 使用说明

## 1. API Key 现在填在哪里

现在不再要求在网页里输入 API Key。

请直接编辑：

`config/local_provider_config.py`

这个文件已经被 `.gitignore` 忽略，不会被提交到仓库。

如果你想先看示例，可以参考：

`config/local_provider_config.example.py`

## 2. Gemini 配置示例

```python
LOCAL_PROVIDER_CONFIG = {
    "AI_PROVIDER": "gemini",
    "GEMINI_API_KEY": "你的 Gemini API Key",
    "GEMINI_MODEL": "gemini-2.5-flash",
    "GEMINI_API_BASE": "https://generativelanguage.googleapis.com/v1beta",
}
```

## 3. Claude 配置示例

```python
LOCAL_PROVIDER_CONFIG = {
    "AI_PROVIDER": "claude",
    "CLAUDE_API_KEY": "你的 Claude API Key",
    "CLAUDE_MODEL": "claude-sonnet-4-6",
    "CLAUDE_API_BASE": "https://api.anthropic.com",
    "CLAUDE_API_VERSION": "2023-06-01",
}
```

## 4. 修改后如何生效

修改 `config/local_provider_config.py` 后，重新启动服务：

```bash
python run_server.py
```

然后访问：

- GUI: `http://localhost:8000/app`
- Swagger: `http://localhost:8000/docs`

## 5. 现在网页展示什么

网页现在只展示这个项目本身需要的内容：

- RAG 系统概览
- 核心模块
- 接口清单
- 模块实现状态
- Python 配置位置
- 问答演示
- 反馈统计

已经移除了负责人、指导老师、经费等与系统功能无关的展示内容。

## 6. 当前模块核查结论

按你给出的文档来看，项目不是“全部完全实现”，而是分为三类：

- 已实现
  - 通用 RAG 问答框架
  - 混合检索
  - 多游戏适配
  - 反馈闭环基础接口
  - Web GUI 与 Swagger
  - Gemini / Claude 接入

- 部分实现
  - 多模态语音 / 图像 / 触觉
  - 语义耐心值模型
  - 祖孙协作模式
  - 方言识别

- 未完整实现
  - 分布式爬虫集群与分钟级自动更新
  - Jira 工单闭环
  - NVIDIA NIM 推理优化

这些状态已经同步显示在页面和 `/api/v1/project/module-audit` 接口里。
