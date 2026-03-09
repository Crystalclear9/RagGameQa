"""本地 Python Provider 配置示例。

复制为 `config/local_provider_config.py` 后，在这个文件里直接填写你的真实 API Key。
该文件已被 `.gitignore` 忽略，不会被提交到仓库。
"""

LOCAL_PROVIDER_CONFIG = {
    # 可选: mock / gemini / claude
    "AI_PROVIDER": "mock",

    # Gemini
    "GEMINI_API_KEY": "",
    "GEMINI_MODEL": "gemini-2.5-flash",
    "GEMINI_API_BASE": "https://generativelanguage.googleapis.com/v1beta",

    # Claude
    "CLAUDE_API_KEY": "",
    "CLAUDE_MODEL": "claude-sonnet-4-6",
    "CLAUDE_API_BASE": "https://api.anthropic.com",
    "CLAUDE_API_VERSION": "2023-06-01",
}
