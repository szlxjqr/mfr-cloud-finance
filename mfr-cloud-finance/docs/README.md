# 云财务 (Cloud Finance)

> 企业级云财务管理系统 — 基于 WP5云会计 参考布局开发

## 一、技术栈

| 层级 | 技术 |
|------|------|
| 前端框架 | Vue 3 + TypeScript + Vite |
| UI 组件库 | Element Plus |
| 图表库 | ECharts (vue-echarts) |
| 状态管理 | Pinia |
| 路由 | Vue Router 4 |
| HTTP 客户端 | Axios |
| 后端框架 | Python FastAPI |
| 数据校验 | Pydantic v2 |

## 二、目录结构

```
mfr-cloud-finance/
├── frontend/                          # Vue3 前端
│   ├── src/
│   │   ├── api/dashboard.ts           # API 接口层
│   │   ├── layouts/                   # 布局组件
│   │   │   ├── MainLayout.vue          # 主布局容器
│   │   │   └── components/
│   │   │       ├── TopBar.vue          # 顶部导航栏
│   │   │       └── SideNav.vue         # 左侧菜单（总账三级子菜单）
│   │   ├── views/
│   │   │   ├── dashboard/              # 首页仪表盘
│   │   │   │   ├── Dashboard.vue        # 仪表盘主页
│   │   │   │   └── components/         # 四大区块组件
│   │   │   │       ├── QuickActions.vue
│   │   │   │       ├── VoucherCard.vue
│   │   │   │       ├── FundOverview.vue
│   │   │   │       ├── BusinessChart.vue
│   │   │   │       └── TaxChart.vue
│   │   │   └── general-ledger/        # 总账模块
│   │   │       ├── Voucher.vue         # 凭证录入
│   │   │       └── VoucherList.vue     # 查看凭证
│   │   ├── router/index.ts            # 路由配置
│   │   ├── stores/app.ts              # Pinia 状态
│   │   ├── types/dashboard.ts         # TS 类型
│   │   ├── utils/format.ts            # 格式化工具
│   │   ├── plugins/echarts.ts         # ECharts 封装
│   │   ├── style.css                  # 全局样式
│   │   ├── App.vue / main.ts
│   │   └── components/HelloWorld.vue  # 脚手架残留（可删）
│   ├── package.json
│   └── vite.config.ts
├── backend/                           # FastAPI 后端
│   └── app/
│       ├── main.py                    # 应用入口（CORS已配）
│       ├── api/dashboard.py           # 仪表盘 API（4个接口）
│       └── schemas/dashboard.py       # Pydantic 模型
├── docs/                              # 文档
│   ├── README.md                      # 本文件
│   └── 开发日志.md                    # 开发记录（DevLog）
└── .gitignore
```

## 三、已实现功能

### ✅ 整体框架
- 顶部导航栏：Logo / 公司切换 / 全局按钮 / 用户信息
- 左侧导航栏：11 个一级菜单（可折叠）+ 总账三级子菜单
- 主内容区：路由视图 + 全屏布局

### ✅ 首页仪表盘（四大区块）
1. **常用功能**：12 个快捷图标入口
2. **凭证中心**：月份选择、凭证统计、查看/新增操作
3. **资金情况**：6 大资金指标（现金/银行存款/应收应付/收入/费用）
4. **经营数据**：月度趋势折线图（12 个月）
5. **应交税费**：环形图展示 4 类税额占比

### ✅ 总账模块
- **凭证管理** → 凭证（录入）、查看凭证（列表）、原始凭证
- **账簿** → 总账/明细账/余额表/序时账/多栏账/科目汇总表
- **辅助账簿** → 科目辅助明细账/余额表、数量外币明细账/余额表、核算项目明细账/余额表

### ✅ 凭证录入页 (`Voucher.vue`)
- 顶部工具栏：搜索、保存(Ctrl+S)、保存并新增(F5)、保存并打印、清除、更多、导航
- 凭证头：凭证字(记/收/付/转)、凭证号、日期、会计期间、附单据数
- 分录表格：序号/摘要/会计科目/借方(14位)/贷方(14位)
- 合计行自动计算 + 借贷平衡校验

### ✅ 查看凭证页 (`VoucherList.vue`)
- 工具栏：日期/期间切换、日期范围、搜索、筛选、刷新、展开分录、取消分页、新增、导入、电子账簿、整理编号
- 批量栏：已选 N 条、审核/打印/导出下拉、删除
- 表格：选择框、展开箭头、摘要、科目、借/贷金额
- 展开明细：分录明细表 + 制单人/审核人/附单据/备注
- 分页栏

### ✅ 后端 API
| 接口 | 说明 |
|------|------|
| `GET /api/dashboard/summary` | 凭证汇总 |
| `GET /api/dashboard/funds` | 资金情况（6指标） |
| `GET /api/dashboard/revenue` | 经营趋势（12月） |
| `GET /api/dashboard/taxes` | 应交税费（4类） |

## 四、本地运行

```bash
# 后端（端口 8000）
cd backend
PYTHONPATH=. uvicorn app.main:app --host 0.0.0.0 --port 8000

# 前端（端口 5173 开发 / 8137 预览用静态构建）
cd frontend
npm install
npm run dev          # 开发模式
npm run build && python3 -m http.server 8137 --directory dist  # 静态预览
```

前端 API baseURL：`http://localhost:8000/api`

## 五、开发计划

| 阶段 | 模块 | 状态 |
|------|------|------|
| 1 | 整体框架 + 首页仪表盘 | ✅ 完成 |
| 1 | 总账三级菜单 | ✅ 完成 |
| 1 | 凭证录入页 | ✅ 完成 |
| 1 | 查看凭证页 | ✅ 完成 |
| 2 | 总账/凭证（会计科目树、复式记账引擎、借贷校验） | ⏳ 待开发 |
| 3 | 财务报表（资产负债表/利润表/现金流量表） | ⏳ 待开发 |
| 4 | 发票管理（进项/销项、增值税计算） | ⏳ 待开发 |
| 5 | 扩展模块（出纳/资产/工资/结账） | ⏳ 待开发 |

## 六、已加载的财务技能（accounting skills）

- **accountant-expert**：GAAP/IFRS、复式记账、三大财务报表、税务计算、财务比率
- **accountant**（CFO视角）：税务规划、VAT合规、财务预测、会计软件逻辑设计
- **financial-reporting-dashboard**：P&L/资产负债表仪表盘、按产品/渠道/周期下钻

详见 `docs/开发日志.md`。
