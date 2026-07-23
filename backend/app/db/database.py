"""数据库基础设置：引擎 / 会话 / 基类 / 依赖注入。

设计要点：
- 开发默认 SQLite（本地文件库 smart_finance.db），零配置即可跑起来。
- 生产部署通过环境变量 DATABASE_URL 切换为云 PostgreSQL（如云厂商 RDS），
  满足「可连数据库、可上云」的硬性要求，且连接串不硬编码。
- 业务模块模型统一继承 Base；应用启动时调用 init_db() 自动建表。
"""
import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# 生产环境示例：DATABASE_URL=postgresql://user:pass@host:5432/smart_finance
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./smart_finance.db")

# SQLite 单文件库需关闭同线程检查；云端数据库无需该参数。
# busy_timeout：并发写时等待（毫秒）而非立即报 "database is locked"，
# 这是并发安全编码生成器（乐观锁）能成立的底层前提。
_connect_args = (
    {"check_same_thread": False, "timeout": 30}
    if DATABASE_URL.startswith("sqlite")
    else {}
)

engine = create_engine(DATABASE_URL, connect_args=_connect_args, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    """所有 ORM 模型的声明基类。"""


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖：每个请求一个独立 Session，结束时自动关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """初始化数据库表。

    业务模型统一继承 Base 并在此导入注册，create_all 自动建表；
    对「已存在的旧库」额外处理：补加新列 / 唯一索引 / 计数器表。
    """
    # 导入模型以注册到 Base.metadata（create_all 才能建出对应表）
    from app.models import company as _company  # noqa: F401 公司设置单例
    from app.models import contract  # noqa: F401
    from app.models import employee as _employee  # noqa: F401
    from app.models import invoice as _invoice  # noqa: F401
    from app.models import reimburse as _reimburse  # noqa: F401
    from app.models import purchase as _purchase  # noqa: F401
    from app.models import travel as _travel  # noqa: F401
    from app.models import subject as _subject  # noqa: F401
    from app.models import voucher as _voucher  # noqa: F401
    from app.models import salary as _salary  # noqa: F401
    from app.models import salary_setting as _salary_setting  # noqa: F401
    from app.models import fixed_asset as _fixed_asset  # noqa: F401
    from app.models import code_counter as _code_counter  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _ensure_invoice_code_column(engine)
    _ensure_reimbursement_bills_columns(engine)
    _ensure_purchase_columns(engine)
    _ensure_employees_columns(engine)
    _ensure_hr_contract_columns(engine)
    _seed_admin(engine)
    _seed_subjects(engine)
    _ensure_accum_dep_subject(engine)
    _seed_company_settings(engine)
    _seed_hr_contract_template(engine)


def _ensure_invoice_code_column(engine) -> None:
    """为已存在的 invoices 表补加 invoice_code 列 + 唯一索引。

    SQLite 的 create_all 只会建缺失的表、不会给已存在的表加列，
    故单独处理；新库由模型 unique 约束建好，跳过即可。
    """
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    cols = [c["name"] for c in inspector.get_columns("invoices")]
    if "invoice_code" in cols:
        return
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE invoices ADD COLUMN invoice_code VARCHAR(16)"))
        conn.execute(
            text("CREATE UNIQUE INDEX IF NOT EXISTS uq_invoice_code ON invoices(invoice_code)")
        )


def _ensure_reimbursement_bills_columns(engine) -> None:
    """为已存在的 reimbursement_bills 表补加审批相关字段与报销类型/差旅字段。

    - bill_type：报销类型（采购报销 / 差旅报销），旧行回填 '采购报销'
    - traveler / travel_destination / travel_start / travel_end：差旅报销专属字段
    """
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    cols = [c["name"] for c in inspector.get_columns("reimbursement_bills")]
    with engine.begin() as conn:
        if "approver" not in cols:
            conn.execute(text("ALTER TABLE reimbursement_bills ADD COLUMN approver VARCHAR(100)"))
        if "approve_remark" not in cols:
            conn.execute(text("ALTER TABLE reimbursement_bills ADD COLUMN approve_remark TEXT"))
        # 报销类型与差旅专属字段
        if "bill_type" not in cols:
            conn.execute(text("ALTER TABLE reimbursement_bills ADD COLUMN bill_type VARCHAR(20)"))
            conn.execute(text("UPDATE reimbursement_bills SET bill_type = '采购报销' WHERE bill_type IS NULL"))
        if "traveler" not in cols:
            conn.execute(text("ALTER TABLE reimbursement_bills ADD COLUMN traveler VARCHAR(100)"))
        if "travel_destination" not in cols:
            conn.execute(text("ALTER TABLE reimbursement_bills ADD COLUMN travel_destination VARCHAR(200)"))
        if "travel_start" not in cols:
            conn.execute(text("ALTER TABLE reimbursement_bills ADD COLUMN travel_start DATE"))
        if "travel_end" not in cols:
            conn.execute(text("ALTER TABLE reimbursement_bills ADD COLUMN travel_end DATE"))


def _ensure_purchase_columns(engine) -> None:
    """为已存在的 purchase_requisitions 表补加「研发项目」相关字段。"""
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    cols = [c["name"] for c in inspector.get_columns("purchase_requisitions")]
    with engine.begin() as conn:
        if "is_rd_project" not in cols:
            conn.execute(text("ALTER TABLE purchase_requisitions ADD COLUMN is_rd_project VARCHAR(10)"))
            conn.execute(text("UPDATE purchase_requisitions SET is_rd_project = '否' WHERE is_rd_project IS NULL"))
        if "rd_project_code" not in cols:
            conn.execute(text("ALTER TABLE purchase_requisitions ADD COLUMN rd_project_code VARCHAR(100)"))


def _ensure_employees_columns(engine) -> None:
    """为已存在的 employees 表补加身份证 / 性别 / 生日字段。

    SQLite 的 create_all 只会建缺失的表、不会给已存在的表加列，故单独处理。
    """
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    cols = [c["name"] for c in inspector.get_columns("employees")]
    with engine.begin() as conn:
        if "id_card" not in cols:
            conn.execute(text("ALTER TABLE employees ADD COLUMN id_card VARCHAR(18)"))
        if "gender" not in cols:
            conn.execute(text("ALTER TABLE employees ADD COLUMN gender VARCHAR(4)"))
        if "birthday" not in cols:
            conn.execute(text("ALTER TABLE employees ADD COLUMN birthday DATE"))


def _seed_admin(engine) -> None:
    """初始化管理员：固定员工编号 00000000 + 账号 admin（密码 admin123，role=admin）。

    仅在 accounts 表为空时执行，避免重复写入覆盖线上数据。
    账号 admin / 密码 admin123 仅为初始凭据，上线前应通过环境变量或后台修改。
    """
    from sqlalchemy import select, text

    from app.models import employee as _models
    from app.utils import security

    with SessionLocal() as db:
        exists = db.scalar(select(_models.Account).limit(1))
        if exists:
            return

        # 管理员员工档案
        admin_emp = _models.Employee(
            employee_no="00000000",
            name="管理员",
            department="管理层",
            position="系统管理员",
            status="在职",
        )
        db.add(admin_emp)
        db.flush()

        admin_acc = _models.Account(
            username="admin",
            password_hash=security.hash_password("admin123"),
            employee_no="00000000",
            role="admin",
        )
        db.add(admin_acc)
        db.commit()


# 标准会计科目（小企业会计准则风格）。code 即层级表达；direction 为正常余额方向。
# voucher_service 的科目映射全部引用这里的 code，新增/调整科目在此维护。
_SUBJECT_SEED: list[dict] = [
    # ── 资产类（借）──
    {"code": "1001", "name": "库存现金", "category": "资产", "direction": "借"},
    {"code": "1002", "name": "银行存款", "category": "资产", "direction": "借"},
    {"code": "1122", "name": "应收账款", "category": "资产", "direction": "借"},
    {"code": "1123", "name": "预付账款", "category": "资产", "direction": "借"},
    {"code": "1403", "name": "原材料", "category": "资产", "direction": "借"},
    {"code": "1405", "name": "库存商品", "category": "资产", "direction": "借"},
    {"code": "1601", "name": "固定资产", "category": "资产", "direction": "借"},
    {"code": "1602", "name": "累计折旧", "category": "资产", "direction": "贷", "is_leaf": False},
    # ── 负债类（贷）──
    {"code": "2202", "name": "应付账款", "category": "负债", "direction": "贷"},
    {"code": "2211", "name": "应付职工薪酬", "category": "负债", "direction": "贷"},
    {"code": "2221", "name": "应交税费", "category": "负债", "direction": "贷", "level": 1},
    {"code": "2221.01", "name": "应交增值税", "category": "负债", "direction": "贷", "level": 2, "parent_code": "2221"},
    {"code": "2221.01.01", "name": "进项税额", "category": "负债", "direction": "贷", "level": 3, "parent_code": "2221.01"},
    {"code": "2221.01.02", "name": "销项税额", "category": "负债", "direction": "贷", "level": 3, "parent_code": "2221.01"},
    {"code": "2241", "name": "其他应付款", "category": "负债", "direction": "贷"},
    # ── 权益类（贷）──
    {"code": "3001", "name": "实收资本", "category": "权益", "direction": "贷"},
    {"code": "3103", "name": "本年利润", "category": "权益", "direction": "贷"},
    {"code": "3104", "name": "利润分配", "category": "权益", "direction": "贷"},
    # ── 成本类（借）──
    {"code": "4001", "name": "生产成本", "category": "成本", "direction": "借"},
    {"code": "4101", "name": "制造费用", "category": "成本", "direction": "借"},
    {"code": "4301", "name": "研发支出", "category": "成本", "direction": "借"},
    # ── 损益类 ──
    {"code": "5001", "name": "主营业务收入", "category": "损益", "direction": "贷"},
    {"code": "5051", "name": "其他业务收入", "category": "损益", "direction": "贷"},
    {"code": "5401", "name": "主营业务成本", "category": "损益", "direction": "借"},
    {"code": "5601", "name": "销售费用", "category": "损益", "direction": "借"},
    {"code": "5602", "name": "管理费用", "category": "损益", "direction": "借"},
    {"code": "5603", "name": "财务费用", "category": "损益", "direction": "借"},
    {"code": "5801", "name": "所得税费用", "category": "损益", "direction": "借"},
]


def _seed_subjects(engine) -> None:
    """初始化标准会计科目：account_subjects 为空时写入（不清空已有数据）。"""
    from sqlalchemy import select, text

    from app.models import subject as _models

    with SessionLocal() as db:
        exists = db.scalar(select(_models.AccountSubject).limit(1))
        if exists:
            return
        for item in _SUBJECT_SEED:
            db.add(
                _models.AccountSubject(
                    code=item["code"],
                    name=item["name"],
                    category=item["category"],
                    direction=item["direction"],
                    level=item.get("level", 1),
                    parent_code=item.get("parent_code"),
                    is_leaf=item.get("is_leaf", True),
                    status=item.get("status", "启用"),
                )
            )
        db.commit()


def _ensure_accum_dep_subject(engine) -> None:
    """为已存在（科目表非空）的库补加「1602 累计折旧」。

    _seed_subjects 仅在科目表完全为空时写入，故老库（已有一套科目）
    不会自动获得 1602。新增固定资产折旧联动依赖该科目，故单独补种。
    """
    from sqlalchemy import select

    from app.models import subject as _models

    with SessionLocal() as db:
        exists = db.scalar(
            select(_models.AccountSubject).where(_models.AccountSubject.code == "1602")
        )
        if exists:
            return
        db.add(
            _models.AccountSubject(
                code="1602",
                name="累计折旧",
                category="资产",
                direction="贷",
                level=1,
                is_leaf=False,
                status="启用",
            )
        )
        db.commit()


def _ensure_hr_contract_columns(engine) -> None:
    """为已存在的 hr_contracts 表补加劳动合同标准范本所需字段。

    新建表由 ORM create_all 自动建好，此处仅处理老库的「加列」工作。
    """
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    if "hr_contracts" not in inspector.get_table_names():
        return
    cols = [c["name"] for c in inspector.get_columns("hr_contracts")]
    additions = [
        ("employee_id", "INTEGER"),
        ("employee_no", "VARCHAR(8)"),
        ("department", "VARCHAR(50)"),
        ("position", "VARCHAR(50)"),
        ("phone", "VARCHAR(20)"),
        ("contract_term", "VARCHAR(20)"),
        ("sign_date", "DATE"),
        ("probation_months", "INTEGER"),
        ("probation_start", "DATE"),
        ("probation_end", "DATE"),
        ("probation_salary", "NUMERIC(18,2)"),
        ("work_content", "VARCHAR(200)"),
        ("work_location", "VARCHAR(200)"),
        ("work_hours_type", "VARCHAR(30)"),
        ("pay_method", "VARCHAR(20)"),
        ("pay_day", "INTEGER"),
        ("social_insurance", "VARCHAR(255)"),
        ("benefits", "TEXT"),
        ("approver", "VARCHAR(50)"),
        ("approve_date", "DATE"),
        ("approve_remark", "TEXT"),
        ("template_id", "INTEGER"),
    ]
    with engine.begin() as conn:
        for col_name, col_type in additions:
            if col_name not in cols:
                conn.execute(text(f"ALTER TABLE hr_contracts ADD COLUMN {col_name} {col_type}"))


def _seed_company_settings(engine) -> None:
    """种入公司设置默认值（首次启动或老库无公司设置时）。

    仅在 company_settings 表为空时写入一条 id=1 的占位记录，
    老板可在「公司设置」页 PUT 修改。
    """
    from sqlalchemy import select

    from app.models import company as _models

    with SessionLocal() as db:
        exists = db.scalar(select(_models.CompanySettings).limit(1))
        if exists:
            return
        db.add(
            _models.CompanySettings(
                id=1,
                company_name="深圳市流形机器人科技有限公司",
            )
        )
        db.commit()


def _seed_hr_contract_template(engine) -> None:
    """种入深圳市官方劳动合同标准范本（深圳市人力资源和社会保障局编制）。

    当用户新签「劳动合同」且未指定 template_id 时，print 接口自动用此模板渲染。
    仅在 ctype=hr 且 name 含「深圳市劳动合同」时跳过（避免重复）。
    """
    from sqlalchemy import select

    from app.models import contract as _models

    template_text = """深圳市劳动合同（适用全日制用工）
（深圳市人力资源和社会保障局编制）

甲方（用人单位）：____
法定代表人（主要负责人）或委托代理人：____
注册地址：____
联系电话：____

乙方（劳动者）：____
身份证号码：____
住址：____
联系电话：____

根据《中华人民共和国劳动法》、《中华人民共和国劳动合同法》及国家、省、市有关规定，甲乙双方遵循合法、公平、平等自愿、协商一致、诚实信用的原则，订立本劳动合同。

一、合同期限
（一）甲乙双方同意按以下第____种方式确定本合同期限：
1.有固定期限：从____年____月____日起至____年____月____日止。
2.无固定期限：从____年____月____日起至法定终止条件出现时止。
3.以完成一定工作任务为期限：从____年____月____日起至____工作任务完成时止。
（二）试用期：____个月，从____年____月____日起至____年____月____日止。
（试用期最长不得超过6个月，且不得单独约定试用期。）

二、工作内容和工作地点
（一）乙方的工作岗位（工种）为____。
（二）乙方的工作地点为____。
（三）甲方因生产经营需要调整乙方工作岗位或工作地点的，应协商一致，并变更劳动合同。

三、工作时间和休息休假
（一）甲乙双方同意按以下第____种方式确定乙方的工作时间：
1.标准工时制：每日工作不超过8小时，每周工作不超过40小时。
2.综合计算工时工作制：经人力资源行政部门批准，以____（周/月/季/年）为周期综合计算工作时间。
3.不定时工作制：经人力资源行政部门批准，实行不定时工作制。
（二）甲方因生产（工作）需要，经与工会和乙方协商后可以延长工作时间。
（三）乙方依法享有法定节假日、年休假、婚假、产假、丧假等假期。

四、劳动报酬
（一）乙方正常工作时间的工资按下列第____种形式执行，并不得低于深圳市最低工资标准：
1.计时工资：乙方试用期工资为____元/月（日）；试用期满后，基本工资为____元/月（日）。
2.计件工资：甲方应当科学合理确定劳动定额和计件单价，并予以公布。
（二）甲方每月____日前发放工资。甲方至少每月以货币形式支付乙方工资，不得克扣或者无故拖欠。
（三）甲方安排乙方延长工作时间的，应按《劳动法》第四十四条的规定支付加班工资。

五、社会保险和福利待遇
（一）甲乙双方按照国家和省、市有关规定，参加社会保险，缴纳社会保险费。
（二）乙方患病或非因工负伤，甲方应按国家和省、市的有关规定给予医疗期和医疗期待遇。
（三）乙方患职业病、因工负伤的，甲方按《职业病防治法》、《工伤保险条例》等有关法律法规的规定执行。
（四）甲方为乙方提供以下福利待遇：____。

六、劳动保护、劳动条件和职业危害防护
（一）甲方按国家和省、市有关劳动保护规定，提供符合国家安全卫生标准的劳动作业场所和必要的劳动防护用品。
（二）甲方按国家和省、市有关规定，做好女员工和未成年工的特殊劳动保护工作。
（三）乙方从事接触职业病危害作业的，甲方应按国家有关规定组织职业健康检查。

七、规章制度的告知与遵守
甲方应依法建立和完善劳动规章制度，并将规章制度告知乙方。乙方应遵守甲方的劳动规章制度。

八、劳动合同的变更
甲乙双方协商一致，可以变更本合同约定的内容，并采用书面形式确定。

九、劳动合同的解除、终止和经济补偿
（一）甲乙双方解除、终止本合同，应当按照《劳动合同法》第三十六条至第四十五条、第四十六条、第四十七条的规定执行。
（二）甲方应当在解除或者终止本合同时，为乙方出具解除或者终止劳动合同的证明，并在十五日内为乙方办理档案和社会保险关系转移手续。
（三）乙方应当按照双方约定，办理工作交接。

十、违约责任
（一）甲方违法解除或终止本合同，应向乙方支付赔偿金。
（二）乙方违反服务期约定的，应当按照约定向甲方支付违约金。违约金的数额不得超过甲方提供的培训费用。
（三）乙方违反竞业限制约定的，应当按照约定向甲方支付违约金。

十一、争议处理
甲乙双方因履行本合同发生劳动争议，可以协商解决；不愿协商或者协商不成的，可以向劳动争议仲裁委员会申请仲裁。对仲裁裁决不服的，可以向人民法院提起诉讼。

十二、其他
（一）本合同未尽事宜，按国家和省、市有关法律法规规定执行。
（二）本合同一式两份，甲乙双方各执一份，具有同等法律效力。

甲方（盖章）：____________________
法定代表人（主要负责人）或委托代理人（签名）：____________________
签订日期：____年____月____日

乙方（签名）：____________________
签订日期：____年____月____日"""

    with SessionLocal() as db:
        exists = db.scalar(
            select(_models.ContractTemplate).where(
                _models.ContractTemplate.ctype == "hr",
                _models.ContractTemplate.name == "深圳市劳动合同（适用全日制用工）",
            )
        )
        if exists:
            return
        db.add(
            _models.ContractTemplate(
                name="深圳市劳动合同（适用全日制用工）",
                ctype="hr",
                content=template_text,
                remark="深圳市人力资源和社会保障局编制，来源 szhr.com.cn 标准范本",
            )
        )
        db.commit()
