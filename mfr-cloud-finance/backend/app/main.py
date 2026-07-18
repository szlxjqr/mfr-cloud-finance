"""FastAPI 应用入口：云财务 API"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import dashboard

app = FastAPI(title="云财务 API", version="1.0.0")

# 配置 CORS 中间件，允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册仪表盘路由
app.include_router(dashboard.router, prefix="/api")


@app.get("/")
def read_root():
    return {"message": "云财务 API"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", reload=True, port=8000)
