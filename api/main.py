# 主API入口
from fastapi import FastAPI
from api.routes import qa_routes, multimodal_routes, analytics_routes, health_routes

app = FastAPI(
    title="RAG Game QA System",
    description="基于RAG的游戏问答系统",
    version="1.0.0"
)

# 注册路由
app.include_router(qa_routes.router, prefix="/api/v1/qa", tags=["问答"])
app.include_router(multimodal_routes.router, prefix="/api/v1/multimodal", tags=["多模态"])
app.include_router(analytics_routes.router, prefix="/api/v1/analytics", tags=["分析"])
app.include_router(health_routes.router, prefix="/api/v1/health", tags=["健康"])

@app.get("/")
async def root():
    return {"message": "RAG Game QA System API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
