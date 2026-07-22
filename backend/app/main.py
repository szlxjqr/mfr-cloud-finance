"""FastAPI 应用入口：智慧经营 API"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import contracts
from app.api import dashboard
from app.api import invoice
from app.api import reimburse
from app.api import purchase
from app.api import travel
from app.api import auth
from app.api import employees
from app.api import subjects
from app.api import vouchers
from app.db import init_db
from app.models import contract  # 导入即注册 ORM 模型，供 init_db 建表
from app.models import employee as employee_model  # noqa: F401 注册员工/账号模型
from app.models import invoice as invoice_model  # noqa: F401 注册发票模型
from app.models import reimburse as reimburse_model  # noqa: F401 注册报销单模型
from app.models import purchase as purchase_model  # noqa: F401 注册采购申请模型
from app.models import travel as travel_model  # noqa: F401 注册差旅申请模型
from app.models import subject as subject_model  # noqa: F401 注册会计科目模型
from app.models import voucher as voucher_model  # noqa: F401 注册凭证模型
from app.models import code_counter as code_counter_model  # noqa: F401 注册编码计数器模型


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
# 注册报销管理路由（报销单 CRUD + 状态流转）
app.include_router(reimburse.router, prefix="/api")
# 注册采购管理路由（采购申请单 CRUD + 状态流转）
app.include_router(purchase.router, prefix="/api")
# 注册差旅管理路由（差旅申请单 CRUD + 状态流转）
app.include_router(travel.router, prefix="/api")
# 注册发票管理路由（进项发票 CRUD + 关联报销单 + 归档 + 凭证草稿）
app.include_router(invoice.router, prefix="/api")
# 注册登录鉴权路由（登录 / 当前用户）
app.include_router(auth.router, prefix="/api")
# 注册人员管理路由（员工档案 CRUD + 自动建账号）
app.include_router(employees.router, prefix="/api")
# 注册会计核算路由（科目 / 凭证 / 余额汇总 / 一键联动）
app.include_router(subjects.router, prefix="/api")
app.include_router(vouchers.router, prefix="/api")


@app.get("/health")
def health_check():
    return {"message": "智慧经营 API", "status": "ok"}


# 前端构建产物托管：若 frontend/dist 存在，则由后端同源托管（Plan A 单机运行）
# 前端用 hash 路由（createWebHashHistory），浏览器只请求 "/"，StaticFiles 直接返回 index.html，无需 history fallback
_FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if _FRONTEND_DIST.is_dir():
    from fastapi.staticfiles import StaticFiles

    app.mount("/", StaticFiles(directory=str(_FRONTEND_DIST), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", reload=True, port=8521)
