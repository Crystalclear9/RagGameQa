# ⚠️ Claude API Key 限制说明

## 🔍 问题发现

在测试过程中发现，你提供的API Key有使用限制：

```
Error code: 403
Your client is not authorized to use this API key
allowedClients: ['claude_code']
```

## 📝 问题说明

你的API Key: `cr_41127d92bf466a05017dc0fa1408bc0a2bde8e99f91f6752995a6f83756174ad`

**这是一个Claude Code专用的API Key，只能在Claude Code环境中使用，不能用于外部API调用。**

## 💡 解决方案

### 方案1: 使用模拟模式（开发测试）

修改代码使用模拟LLM响应，无需真实API：

```python
# core/generator/llm_generator.py

async def _call_llm(self, prompt: str) -> str:
    """调用大语言模型 - 开发模拟模式"""
    # 模拟响应，用于开发测试
    return """
    根据您的问题，这里是答案：
    
    战士可以通过以下方式学习技能：
    1. 访问主城或营地中的职业训练师
    2. 达到所需等级后与训练师对话
    3. 支付相应的金币学习新技能
    
    技能训练师通常位于职业大厅或训练区域。
    """
```

### 方案2: 获取Anthropic官方API Key

1. 访问: https://console.anthropic.com/
2. 注册账号
3. 获取正式的API Key（格式通常为 `sk-ant-api03-...`）
4. 替换 `.env` 文件中的 `CLAUDE_API_KEY`

**费用**: Claude API是付费服务，但有免费额度

### 方案3: 使用其他LLM提供商

可以切换到其他兼容的API：

1. **OpenAI GPT**
   - 获取API Key: https://platform.openai.com/
   - 修改 `.env`: `AI_PROVIDER=openai`

2. **本地模型**
   - 使用Ollama运行本地模型
   - 免费，但需要较好的硬件

3. **其他API服务**
   - 国内的通义千问、文心一言等
   - 需要相应的API适配

## 🚀 当前可以做的

即使没有可用的API Key，你仍然可以：

### 1. 完成项目结构
- ✅ 环境配置已完成
- ✅ 依赖包管理
- ✅ 代码框架搭建

### 2. 开发其他模块
- ✅ 检索模块（不依赖LLM）
- ✅ 知识库管理
- ✅ 数据处理
- ✅ API路由

### 3. 使用模拟模式测试
```bash
# 创建模拟模式的LLM生成器
python scripts/create_mock_llm.py
```

## 📊 测试结果总结

当前测试状态：

| 项目 | 状态 | 说明 |
|------|------|------|
| .env文件 | ✅ | 已创建 |
| python-dotenv | ✅ | 已安装 |
| anthropic包 | ✅ | 已安装 |
| **Claude API** | ❌ | **Key限制问题** |
| 配置加载 | ⚠️ | 缺少部分依赖 |
| LLM生成器 | ⚠️ | 缺少依赖包 |

## 🔧 下一步建议

### 立即可做（不需要API）

1. **安装剩余依赖包**
```bash
pip install sqlalchemy sentence-transformers
```

2. **创建模拟LLM生成器**
```bash
python scripts/create_mock_llm.py
```

3. **测试其他模块**
```bash
# 测试检索模块
python scripts/test_retriever.py

# 测试知识库
python scripts/test_knowledge_base.py
```

### 需要API Key（生产环境）

1. 获取正式的Claude API Key
2. 或使用OpenAI API
3. 或部署本地模型

## ⭐ 推荐方案

**对于学习和开发**: 使用模拟模式 ✅

**对于生产环境**: 获取正式API Key 💳

---

**需要帮助？** 我可以帮你：
1. 创建模拟LLM生成器
2. 配置本地模型
3. 适配其他API服务

