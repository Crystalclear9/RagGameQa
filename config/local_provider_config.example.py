"""Local Python provider config example.

Copy this to `config/local_provider_config.py` and put real keys there.
Only placeholder values are allowed in this tracked example file.
"""

LOCAL_PROVIDER_CONFIG = {
    "AI_PROVIDER": "gemini",
    "GEMINI_API_KEY": "your-gemini-api-key",
    "GEMINI_MODEL": "gemini-2.5-flash",
    "GEMINI_API_BASE": "https://generativelanguage.googleapis.com/v1beta",
    "NIM_API_KEY": "your-nim-api-key",
    "NIM_API_BASE": "https://integrate.api.nvidia.com/v1",
    "NIM_MODEL": "meta/llama-3.1-70b-instruct",
    "CLAUDE_API_KEY": "your-claude-api-key",
    "CLAUDE_MODEL": "claude-sonnet-4-6",
    "CLAUDE_API_BASE": "https://api.anthropic.com",
    "CLAUDE_API_VERSION": "2023-06-01",
    "JIRA_BASE_URL": "https://your-domain.atlassian.net",
    "JIRA_EMAIL": "your-jira-email@example.com",
    "JIRA_API_TOKEN": "your-jira-api-token",
    "JIRA_PROJECT_KEY": "RAG",
}
