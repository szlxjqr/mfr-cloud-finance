"""模型统一出口，导入即注册到 Base.metadata（供 init_db 建表）。"""
from app.models.contract import (
    ContractTemplate,
    HRContract,
    Parties,
    PurchaseContract,
    SalesContract,
)

__all__ = [
    "Parties",
    "HRContract",
    "SalesContract",
    "PurchaseContract",
    "ContractTemplate",
]
