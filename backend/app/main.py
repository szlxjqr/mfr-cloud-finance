"""FastAPI 应用入口：智慧经营 API"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import contracts
from app.api import dashboard
from app.db import init_db
from app.models import contract  # 导入即注册 ORM 模型，供 init_db 建表


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化数据库表（业务模型就绪后自动生效）
    init_db()
    yield


app = FastAPI(title="智慧经营 API", version="1.0.0", lifespan=lifespan)

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
# 注册合同管理路由（往来单位 / 人事·销售·采购合同 / 合同模板）
app.include_router(contracts.router, prefix="/api")


@app.get("/")
def read_root():
    return {"message": "智慧经营 API"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", reload=True, port=8000)
