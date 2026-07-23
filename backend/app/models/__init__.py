"""模型统一出口，导入即注册到 Base.metadata（供 init_db 建表）。"""
from app.models.company import CompanySettings
from app.models.contract import (
    ContractTemplate,
    HRContract,
    Parties,
    PurchaseContract,
    SalesContract,
)
from app.models.employee import Account, Employee
from app.models.fixed_asset import DepRecord, FixedAsset
from app.models.invoice import Invoice, InvoiceDetail
from app.models.reimburse import ReimbursementBill
from app.models.subject import AccountSubject
from app.models.voucher import Voucher, VoucherEntry

__all__ = [
    "Parties",
    "HRContract",
    "SalesContract",
    "PurchaseContract",
    "ContractTemplate",
    "CompanySettings",
    "Employee",
    "Account",
    "ReimbursementBill",
    "Invoice",
    "InvoiceDetail",
    "AccountSubject",
    "Voucher",
    "VoucherEntry",
    "FixedAsset",
    "DepRecord",
]
