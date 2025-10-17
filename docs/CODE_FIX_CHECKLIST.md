# RAG游戏问答系统 - 代码修复清单

> 本清单按优先级和依赖关系组织，建议按顺序逐步完成

---

## 📋 总体概览

项目是一个基于FastAPI的RESTful API服务，核心功能是游戏问答RAG系统。
已移除多模态交互、无障碍支持和健康管理相关功能的依赖包。

**预计修复难度**: 中等  
**预计完成时间**: 4-6小时  

---

## 🔧 阶段1: 环境配置与依赖修复

### 1.1 创建环境配置文件

**问题**: 缺少 `.env` 文件和环境配置示例

**修复步骤**:
```bash
# 创建 .env 文件
touch .env
```

**需要配置的内容** (.env):
```bash
# 应用配置
APP_NAME="RAG Game QA System"
APP_VERSION="1.0.0"
DEBUG=True
ENV=dev

# API配置
API_HOST=0.0.0.0
API_PORT=8000
CORS_ALLOW_ORIGINS=*
LOG_LEVEL=info

# 数据库配置
DATABASE_URL=postgresql://postgres:password@localhost:5432/rag_game_qa
REDIS_URL=redis://localhost:6379

# 模型配置
DEFAULT_MODEL=gpt-4
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
MAX_TOKENS=2000

# OpenAI配置 (如使用GPT-4)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1

# 检索配置
TOP_K_RESULTS=5
SIMILARITY_THRESHOLD=0.7
```

**相关文件**: `config/settings.py`

---

### 1.2 数据库连接配置

**问题**: 需要确保PostgreSQL数据库已安装并正确配置

**修复步骤**:
```bash
# 1. 安装PostgreSQL (如果未安装)
# Windows: 下载安装包 https://www.postgresql.org/download/windows/

# 2. 创建数据库
psql -U postgres
CREATE DATABASE rag_game_qa;
\q

# 3. 测试连接
psql -U postgres -d rag_game_qa -c "SELECT version();"
```

**验证**: 确保 `DATABASE_URL` 可以连接

---

### 1.3 Redis配置 (可选，用于缓存)

**问题**: Redis用于缓存，但不是核心功能

**修复步骤**:
```bash
# Windows: 下载Redis for Windows
# 或使用Docker运行
docker run -d -p 6379:6379 redis:latest
```

**临时方案**: 如果不使用Redis，修改代码中的Redis依赖为可选

---

## 🔧 阶段2: 核心模块依赖修复

### 2.1 修复多模态相关导入错误

**问题**: `api/routes/multimodal_routes.py` 引用了已移除依赖的模块

**受影响文件**:
- `api/routes/multimodal_routes.py` (行5-7)
- `api/main.py` (行58: 注册multimodal路由)

**修复方案1 - 完全移除** (推荐):
```python
# api/main.py
# 注释掉或删除这一行
# app.include_router(multimodal_routes.router, prefix="/api/v1/multimodal", tags=["多模态"])
```

**修复方案2 - 保留但返回错误**:
```python
# api/routes/multimodal_routes.py
# 将所有端点改为返回"功能未启用"

@router.post("/speech/recognize")
async def recognize_speech(*args, **kwargs):
    raise HTTPException(status_code=501, detail="多模态功能未启用")
```

---

### 2.2 修复健康管理路由问题

**问题**: `api/routes/health_routes.py` 功能完整但依赖已移除的包

**受影响文件**:
- `api/routes/health_routes.py`
- `api/main.py` (行60: 注册health路由)

**修复方案1 - 完全移除**:
```python
# api/main.py
# 注释掉这一行
# app.include_router(health_routes.router, prefix="/api/v1/health", tags=["健康"])
```

**修复方案2 - 保留基础健康检查**:
创建简化版 `health_routes.py`:
```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/ping")
async def health_check():
    return {"status": "ok", "message": "服务正常运行"}
```

---

### 2.3 修复无障碍支持相关代码

**问题**: `core/generator/response_formatter.py` 中使用了 `pypinyin`

**受影响代码**:
```python
# response_formatter.py 行5-8
try:
    from pypinyin import lazy_pinyin
except Exception:
    lazy_pinyin = None  # 可选依赖
```

**当前状态**: ✅ 已正确处理为可选依赖，无需修复

**建议**: 如果完全不需要拼音功能，可以删除相关代码

---

### 2.4 修复缺失的辅助模块

**问题**: 以下模块被引用但可能未实现

**需要检查的文件**:
1. `multimodal/speech/dialect_recognizer.py`
2. `multimodal/speech/noise_suppression.py`
3. 各个 `__init__.py` 文件

**修复步骤**:
```bash
# 检查是否存在
ls multimodal/speech/dialect_recognizer.py
ls multimodal/speech/noise_suppression.py
```

**如果不存在，创建空实现**:
```python
# multimodal/speech/dialect_recognizer.py
class DialectRecognizer:
    async def recognize_dialect(self, text: str):
        return {"dialect": "standard", "confidence": 1.0}

# multimodal/speech/noise_suppression.py
class NoiseSuppression:
    async def suppress_noise(self, audio_data: bytes):
        return audio_data  # 无处理
```

---

## 🔧 阶段3: 数据库初始化

### 3.1 创建数据库表

**问题**: 数据库表需要初始化

**修复步骤**:
```python
# 创建初始化脚本 scripts/init_db.py
from config.database import create_tables, drop_tables, SessionLocal
from config.database import Game, Document

def init_database():
    """初始化数据库"""
    print("创建数据库表...")
    create_tables()
    print("数据库表创建成功！")

def seed_data():
    """填充初始数据"""
    db = SessionLocal()
    try:
        # 添加示例游戏
        games = [
            Game(game_id="wow", game_name="魔兽世界", version="10.2.0", 
                 platforms='["PC", "Mac"]', languages='["zh-CN", "en-US"]'),
            Game(game_id="lol", game_name="英雄联盟", version="13.24", 
                 platforms='["PC"]', languages='["zh-CN", "en-US"]'),
            Game(game_id="genshin", game_name="原神", version="4.3.0", 
                 platforms='["PC", "Mobile", "PS5"]', languages='["zh-CN", "en-US", "ja-JP"]'),
        ]
        
        for game in games:
            existing = db.query(Game).filter(Game.game_id == game.game_id).first()
            if not existing:
                db.add(game)
                print(f"添加游戏: {game.game_name}")
        
        db.commit()
        print("初始数据填充成功！")
    except Exception as e:
        print(f"数据填充失败: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_database()
    seed_data()
```

**运行初始化**:
```bash
python scripts/init_db.py
```

---

### 3.2 创建示例文档数据

**问题**: 知识库需要示例数据才能测试检索功能

**修复步骤**:
```python
# scripts/add_sample_docs.py
from config.database import SessionLocal, Document
from core.knowledge_base.embedding_service import EmbeddingService
import asyncio

async def add_sample_documents():
    """添加示例文档"""
    db = SessionLocal()
    embedding_service = EmbeddingService()
    
    sample_docs = [
        {
            "game_id": "wow",
            "title": "战士技能学习指南",
            "content": "战士可以通过访问职业训练师学习新技能。训练师通常位于主城和营地中。",
            "category": "职业技能",
            "source": "官方攻略"
        },
        {
            "game_id": "wow",
            "title": "组队系统说明",
            "content": "按I键打开社交面板，点击组队查找器，选择副本后点击加入队列。",
            "category": "社交功能",
            "source": "新手指南"
        },
        {
            "game_id": "lol",
            "title": "英雄联盟控制键位",
            "content": "Q、W、E、R为技能键，D、F为召唤师技能，B键回城。",
            "category": "操作指南",
            "source": "官方文档"
        }
    ]
    
    try:
        for doc_data in sample_docs:
            # 生成嵌入向量
            embedding = await embedding_service.encode_text(doc_data["content"])
            
            doc = Document(
                game_id=doc_data["game_id"],
                title=doc_data["title"],
                content=doc_data["content"],
                category=doc_data["category"],
                source=doc_data["source"],
                embedding=str(embedding.tolist())
            )
            db.add(doc)
            print(f"添加文档: {doc.title}")
        
        db.commit()
        print(f"成功添加 {len(sample_docs)} 个示例文档")
    except Exception as e:
        print(f"添加文档失败: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(add_sample_documents())
```

**运行**:
```bash
python scripts/add_sample_docs.py
```

---

## 🔧 阶段4: 多模态模块修复 (可选)

### 4.1 评估是否需要多模态功能

**决策点**:
- ✅ **完全移除**: 删除 `multimodal/` 目录和相关路由
- ⚠️ **保留代码结构**: 保留文件但禁用功能
- ❌ **恢复功能**: 重新安装依赖包

**推荐方案**: 保留代码结构，禁用功能

---

### 4.2 如果选择完全移除

**步骤**:
```bash
# 1. 删除目录 (可选，建议重命名备份)
mv multimodal multimodal_disabled
mv accessibility accessibility_disabled

# 2. 修改 api/main.py
# 删除 multimodal_routes 和 health_routes 的导入和注册

# 3. 删除 requirements.txt 中相关包（已完成）
```

---

### 4.3 如果选择保留代码结构

**创建占位实现**:
```python
# multimodal/speech/dialect_recognizer.py
from typing import Dict, Any

class DialectRecognizer:
    """方言识别器 - 占位实现"""
    async def recognize_dialect(self, text: str) -> Dict[str, Any]:
        return {"dialect": "standard", "confidence": 1.0}

# multimodal/speech/noise_suppression.py
class NoiseSuppression:
    """噪声抑制 - 占位实现"""
    async def suppress_noise(self, audio_data: bytes) -> bytes:
        return audio_data
```

---

## 🔧 阶段5: API路由修复

### 5.1 修复 api/main.py

**当前问题**:
1. 导入了可能不需要的路由
2. 缺少错误处理
3. 缺少基础健康检查

**修复后的 api/main.py**:
```python
# 主API入口
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import logging
from api.routes import qa_routes, analytics_routes  # 只导入核心路由
from config.settings import settings

# 可选导入
try:
    from api.routes import health_routes
    HAS_HEALTH = True
except ImportError:
    HAS_HEALTH = False

try:
    from api.routes import multimodal_routes
    HAS_MULTIMODAL = True
except ImportError:
    HAS_MULTIMODAL = False

# 配置日志
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
logger = logging.getLogger(__name__)

app = FastAPI(
    title="RAG Game QA System",
    description="基于RAG的游戏问答系统",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logger.info(
        f"{request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.3f}s"
    )
    return response

# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "服务器内部错误，请稍后重试",
            "detail": str(exc) if settings.DEBUG else None,
        },
    )

# 注册核心路由
app.include_router(qa_routes.router, prefix="/api/v1/qa", tags=["问答"])
app.include_router(analytics_routes.router, prefix="/api/v1/analytics", tags=["分析"])

# 可选路由
if HAS_HEALTH:
    app.include_router(health_routes.router, prefix="/api/v1/health", tags=["健康"])
if HAS_MULTIMODAL:
    app.include_router(multimodal_routes.router, prefix="/api/v1/multimodal", tags=["多模态"])

@app.get("/")
async def root():
    return {
        "message": "RAG Game QA System API",
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc",
        "features": {
            "qa": True,
            "analytics": True,
            "health": HAS_HEALTH,
            "multimodal": HAS_MULTIMODAL
        }
    }

@app.get("/health")
async def health_check():
    """基础健康检查"""
    return {"status": "ok", "version": settings.APP_VERSION}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT, log_level=settings.LOG_LEVEL)
```

---

### 5.2 确保所有路由的 __init__.py

**检查文件**: `api/routes/__init__.py`

```python
# api/routes/__init__.py
from . import qa_routes
from . import analytics_routes

try:
    from . import health_routes
except ImportError:
    health_routes = None

try:
    from . import multimodal_routes
except ImportError:
    multimodal_routes = None

__all__ = ["qa_routes", "analytics_routes", "health_routes", "multimodal_routes"]
```

---

## 🔧 阶段6: 工具模块完善

### 6.1 检查并创建工具模块

**需要的文件**:
- `utils/constants.py` - 常量定义
- `utils/file_utils.py` - 文件操作
- `utils/text_utils.py` - 文本处理
- `utils/logging_config.py` - 日志配置

**修复步骤**:

#### 6.1.1 utils/constants.py
```python
# 常量定义
# 游戏相关
SUPPORTED_GAMES = ["wow", "lol", "genshin", "minecraft", "valorant", "apex"]

# 模型相关
DEFAULT_EMBEDDING_DIM = 384
MAX_CONTEXT_LENGTH = 2000
DEFAULT_TOP_K = 5

# 检索相关
MIN_SIMILARITY_THRESHOLD = 0.5
DEFAULT_SIMILARITY_THRESHOLD = 0.7

# 分类
KNOWLEDGE_CATEGORIES = [
    "职业技能", "装备系统", "副本攻略", "PVP指南",
    "任务流程", "经济系统", "社交功能", "Bug反馈"
]

# 用户类型
USER_TYPES = ["normal", "elderly", "visual_impairment", "hearing_impairment"]
```

#### 6.1.2 utils/text_utils.py
```python
# 文本处理工具
import re
from typing import List

def clean_text(text: str) -> str:
    """清理文本"""
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text

def truncate_text(text: str, max_length: int = 200) -> str:
    """截断文本"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."

def split_into_sentences(text: str) -> List[str]:
    """分句"""
    sentences = re.split(r'[。！？.!?]', text)
    return [s.strip() for s in sentences if s.strip()]
```

#### 6.1.3 utils/file_utils.py
```python
# 文件操作工具
import os
import json
from pathlib import Path
from typing import Any, Dict

def ensure_dir(directory: str):
    """确保目录存在"""
    Path(directory).mkdir(parents=True, exist_ok=True)

def load_json(file_path: str) -> Dict[str, Any]:
    """加载JSON文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data: Dict[str, Any], file_path: str):
    """保存JSON文件"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
```

#### 6.1.4 utils/logging_config.py
```python
# 日志配置
import logging
import sys
from pathlib import Path

def setup_logging(log_level: str = "INFO", log_file: str = None):
    """设置日志"""
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    handlers = [logging.StreamHandler(sys.stdout)]
    
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )
```

---

## 🔧 阶段7: 测试与验证

### 7.1 创建测试脚本

**创建 scripts/test_api.py**:
```python
# API测试脚本
import requests
import json

BASE_URL = "http://localhost:8000"

def test_root():
    """测试根路径"""
    response = requests.get(f"{BASE_URL}/")
    print("Root:", response.json())
    assert response.status_code == 200

def test_health():
    """测试健康检查"""
    response = requests.get(f"{BASE_URL}/health")
    print("Health:", response.json())
    assert response.status_code == 200

def test_qa():
    """测试问答接口"""
    data = {
        "question": "魔兽世界中战士如何学习技能？",
        "game_id": "wow"
    }
    response = requests.post(f"{BASE_URL}/api/v1/qa/ask", json=data)
    print("QA Response:", json.dumps(response.json(), ensure_ascii=False, indent=2))
    assert response.status_code == 200

if __name__ == "__main__":
    print("开始测试...")
    test_root()
    test_health()
    test_qa()
    print("所有测试通过！")
```

---

### 7.2 启动服务并测试

**步骤**:
```bash
# 1. 确保数据库已初始化
python scripts/init_db.py

# 2. 添加示例文档
python scripts/add_sample_docs.py

# 3. 启动服务
python api/main.py

# 4. 在新终端运行测试
python scripts/test_api.py

# 5. 或手动测试
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/v1/qa/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"魔兽世界中战士如何学习技能？","game_id":"wow"}'
```

---

### 7.3 访问API文档

浏览器打开:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 🐛 常见问题与解决方案

### 问题1: ModuleNotFoundError

**错误**: `ModuleNotFoundError: No module named 'xxx'`

**解决**:
```bash
pip install -r requirements.txt
```

---

### 问题2: 数据库连接失败

**错误**: `could not connect to server: Connection refused`

**解决**:
1. 确保PostgreSQL正在运行
2. 检查 DATABASE_URL 配置
3. 检查防火墙设置

---

### 问题3: OpenAI API错误

**错误**: `openai.error.AuthenticationError`

**解决**:
1. 设置正确的 OPENAI_API_KEY
2. 或修改为使用本地模型
3. 或使用模拟返回（开发环境）

**临时方案**:
```python
# core/generator/llm_generator.py
async def _call_llm(self, prompt: str) -> str:
    try:
        # 原有代码
        ...
    except Exception as e:
        # 返回模拟结果（开发环境）
        return f"[模拟回答] 这是对您问题的回答。实际使用需要配置OpenAI API Key。"
```

---

### 问题4: 向量检索返回空结果

**原因**: 知识库中没有文档

**解决**: 运行 `python scripts/add_sample_docs.py`

---

### 问题5: ImportError in multimodal

**错误**: `ImportError: cannot import name 'ASRService'`

**解决**: 
- 方案1: 在 api/main.py 中禁用 multimodal 路由
- 方案2: 创建占位实现（见阶段4）

---

## ✅ 验收标准

完成所有修复后，应该能够:

- [ ] ✅ 成功启动服务 (`python api/main.py`)
- [ ] ✅ 访问API文档 (http://localhost:8000/docs)
- [ ] ✅ 健康检查返回OK (GET /health)
- [ ] ✅ 问答接口返回结果 (POST /api/v1/qa/ask)
- [ ] ✅ 数据库包含示例数据
- [ ] ✅ 无导入错误或警告
- [ ] ✅ 日志正常输出

---

## 📚 参考资料

- **FastAPI文档**: https://fastapi.tiangolo.com/
- **SQLAlchemy文档**: https://docs.sqlalchemy.org/
- **Sentence Transformers**: https://www.sbert.net/
- **OpenAI API**: https://platform.openai.com/docs/

---

## 🎯 优先级总结

### 🔥 立即处理（核心功能）
1. 环境配置 (.env文件)
2. 数据库初始化
3. 修复api/main.py导入
4. 添加示例数据

### ⚠️ 重要但不紧急
5. 创建工具模块
6. 创建测试脚本
7. 完善错误处理

### 💡 可选优化
8. 多模态功能占位
9. 健康管理功能清理
10. 性能优化和监控

---

**祝修复顺利！遇到问题可以随时参考本清单的对应章节。**

