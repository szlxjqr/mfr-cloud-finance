# 智慧经营 (Cloud Finance) — 项目状态速查表 (STATUS)

> **用途**：压缩上下文后，只读本文件即可完全同步项目状态。每次会话结束前更新「维护记录」。
> **维护规则**：任何代码/数据/配置/进度变更后，同步更新对应小节并刷新底部「维护记录」。

> 📌 **若您是从「项目资产库」读到本文件**：这是 GitHub `docs/STATUS.md` 的**入口副本**，可能滞后。请按 §10.3 引导去 GitHub 拉取【最新版】，并把最新版同步回资产库副本。权威永远以 **GitHub 代码仓库** `docs/STATUS.md` 为准。

---

## 1. 项目概览

- **产品名**：智慧经营（原 "MFR智慧经营" 已全局统一为 "智慧经营"，含 backend/doc/前端）
- **定位**：中小企业智慧经营系统（对标 WP5 智慧经营截图）
- **前端栈**：Vue 3 `<script setup>` + TypeScript + Vite（rolldown 打包）+ Element Plus + ECharts + Pinia + Vue Router(Hash)
- **后端栈**：FastAPI（Python 3.11）+ CORS，目前以 Mock 数据为主
- **绝对路径**：`/workspace/mfr-cloud-finance/`（本地电脑无此路径，跨任务/本地靠 git clone 或 T 网盘（tdrive）获取）

---

## 2. 关键事实速查

| 项 | 值 |
|---|---|
| 项目根目录 | `/workspace/mfr-cloud-finance` |
| **Git 仓库根** | `/workspace`（项目在子目录 `mfr-cloud-finance/`；完整前端依赖 `frontend/node_modules` 已随 git 提交，约 1.4 万文件） |
| Git 远程 | `git@github.com:szlxjqr/mfr-cloud-finance.git`（SSH，公开仓库） |
| 当前分支 | `main`（HEAD: `2821a26`） |
| 预览地址 | `https://webview.e2b.bj9.sandbox.cloudstudio.club/?x-cs-sandbox-id=2a28c3ff07dc470ca7e399c5464b5f7f&x-cs-sandbox-port=8137` |
| 预览服务 | `python3 -m http.server 8137 --bind 0.0.0.0`（服务 `frontend/dist`，Hash 路由刷新安全） |
| SSH 配置 | `~/.ssh/config` → `github.com` 走 `ssh.github.com:443`（沙箱 22 端口被封） |
| 前端源码文件数 | 35（`.vue` + `.ts`） |
| 科目数据 | `frontend/src/views/settings/accountData.ts`（187 科目，前端静态） |
| **本文件 T 网盘位置** | T 网盘（tdrive）根目录 `IxkOwRcwRUxu`，`file_id: IzMjhnpPfZrG`（其他任务可先读此文件再连 git；**权威源仍为 GitHub `docs/STATUS.md`**） |
| **T 网盘源码包（tdrive）** | `mfr-cloud-finance-src.tar.gz`（已排除 node_modules/dist/.git），`file_id: InrDRdZmGnAs`；git 连不上时的兜底获取方式 |
| **SSH 私钥交接** | 临时文件 `T1.md`（在 T 网盘根目录 `IxkOwRcwRUxu`）含 ed25519 私钥；用完即删，**绝不下 git**。新任务取到后存为 `~/.ssh/id_ed25519` + `chmod 600` |

---

## 3. 当前进度

### 页面进度：19 完整页 + 15 占位页
- **完整业务页 (19)**：仪表盘(1) + 凭证管理(3) + 基础账簿(6) + 辅助账簿(6) + 科目管理(1) + **进项发票(1) + 报销单列表(1)**
- **占位页 (15)**：报表(5) + 出纳(3) + 资产(1) + 工资(7) + 发票其余(4) + 结账(2) + 设置其余(11)
- 视图目录：`dashboard / voucher(凭证) / general-ledger / auxiliary-ledger / settings / reports / cashier / payroll / invoice / closing / assets`

### 发票报销模块进度（2026-07-21）
| 功能 | 状态 | 说明 |
|---|---|---|
| 发票后端持久化 | ✅ | `invoices` + `invoice_details` 表；CRUD；按期间/关键字查询 |
| 进项发票录入 | ✅ | `InvoiceInput.vue` 接真实后端；新增/编辑/删除/AI 识别保存 |
| 发票↔报销单打通 | ✅ | `BillList.vue` 显示已挂发票张数/金额；支持弹窗勾选未报销发票批量关联 |
| 发票归档 | ✅ | 支持 PDF/OFD 上传；按 `日期_类型_路线_旅客_金额_票号后4位.pdf` 命名 |
| 凭证草稿 | ✅ | 勾选发票一键生成会计凭证分录草稿（借：入账科目/进项税，贷：银行存款/待认证） |
| 报销状态流 | ✅ | 草稿 → 提交 → 待审批 → 通过/驳回 → 已支付（原逻辑保留） |
| 报销单号规则 | ✅ | 单号 = `BXGL` + 4位年份 + 4位年自增（如 `BXGL20260001`）；新增 `GET /api/reimbursements/next-bill-no` 预占接口，新建弹窗预览单号、保存时以入库值为准 |
| 报销单关联多张发票（录入式） | ✅ | 报销单编辑态「增加发票」按钮 → 弹出发票录入弹窗（类型/日期/销方/结算科目/明细行，税额自动算），保存即关联该报销单；保存后自动按关联发票汇总回填报销金额 |

### 科目数据进度
- **187 个标准科目**已由 Excel (`getExcel.xls`) 初始化到 `accountData.ts`
- 分布：资产 44 / 负债 57 / 权益 14 / 成本 7 / 损益 65
- 三级嵌套：4 位(一级) / 7 位(二级) / 10 位(三级)，前缀匹配父子关系
- 渲染：`Account.vue` 用 `expandedIds`(Set) + `flatten()` 扁平化为 `visibleRows`，支持展开/折叠/搜索/行选中（默认选中 应收账款 1122）

---

## 4. 关键决策与踩坑记录

| 主题 | 结论 / 做法 |
|---|---|
| **刷新 404** | 原 History 模式 + `http.server` 无 SPA fallback 会 404 → 改 `createWebHashHistory()`，URL 形如 `/#/settings/account` |
| **GitHub 22 端口被封** | `ssh -T git@github.com` 超时 → `~/.ssh/config` 配 `Hostname ssh.github.com` + `Port 443` 解决。**注意：此方案仅对"22 封但 443 通"的沙箱有效**；部分沙箱把 github.com 全域透明代理拦截（DNS 解析到 `198.18.x.x`、SSH/HTTPS 全断），那种**直连走不通，必须走中转模式（见第 8 节）** |
| **`git push` HTTP/2 卡死** | 443 实际连通（curl 直连 HTTPS 正常），但 git 默认走 HTTP/2 多路复用（`can multiplex`）卡在 TLS 协商 → 加 `GIT_HTTP_VERSION=1.1 git push` 立即成功。**排查顺序**：先 `python3 -c "socket.create_connection(('github.com',443))"` 验端口，再 `curl -v https://github.com` 验 TLS，最后 `GIT_CURL_VERBOSE=1 git push` 看卡在哪一环；不要一上来就怀疑断网 |
| **认证方式** | 已弃用 PAT token（曾失效），统一走 **SSH over 443**，免密推送。**SSH key 不要删**（删了配对失效，推送断） |
| **品牌统一** | "MFR智慧经营" → "智慧经营"，`git grep` 已验证无残留 |
| **侧边栏分级缩进** | 宽 `200px → 224px`；CSS 变量 `--lv1-pad:6px / --lv2-pad:30px / --lv3-pad:44px` 控制一/二/三级缩进 |
| **科目表树形渲染** | 早期为内联 Mock 平铺 → 改为 `accountData.ts` + 扁平化展开，模板 `v-for="row in visibleRows"` 用 `row.node.xxx` 与 `row.depth` 缩进 |
| **构建命令 cwd** | 必须在 `frontend/` 下执行 `npm run build`（否则报 Missing script: build） |
| **预览 SIGTERM** | `pkill -f "http.server 8137"` 会误杀执行命令自身 → 改用 `fuser -k 8137/tcp` 按端口结束，再用 `setsid ... < /dev/null &` 脱离终端启动 |

---

## 5. 常用命令

```bash
# 构建（务必在 frontend 目录）
cd /workspace/mfr-cloud-finance/frontend && npm run build

# 重启预览（先按端口结束旧进程，避免 pkill 误杀）
fuser -k 8137/tcp
cd /workspace/mfr-cloud-finance/frontend && setsid python3 -m http.server 8137 --bind 0.0.0.0 < /dev/null > /tmp/preview8137.log 2>&1 &

# 提交与推送
cd /workspace/mfr-cloud-finance
git add -A && git commit -m "..." && git push origin main

# 跨任务/本地获取文件
git clone git@github.com:szlxjqr/mfr-cloud-finance.git   # 或用 T 网盘（tdrive）src 包
```

---

## 6. 待办 / 下一步

- [ ] 报表模块 5 页实现（资产负债表/利润表/利润表季报/现金流量表/现金流量表季报）
- [ ] 出纳模块 3 页、资产模块 1 页、工资模块 7 页、发票模块 5 页、结账模块 2 页、设置其余 11 页
- [ ] 凭证录入页会计科目选择器弹窗（当前占位）
- [ ] 复式记账引擎后端化
- [ ] 科目/凭证/账簿真实持久化（当前前端静态 + Mock）
- [ ] 将 `accountData.ts` 科目数据迁移到后端 API

---

## 7. 网络连通性 & 中转模式（重要）

**每个新建任务可能落在不同的网络区域**，git 连通性不能假定。新任务第一步必须**先测连通性**：

```bash
# 1) 配 SSH 443
cat > ~/.ssh/config <<'EOF'
Host github.com
    Hostname ssh.github.com
    Port 443
    User git
EOF
chmod 600 ~/.ssh/config

# 2) 测连通性（关键判定）
ssh -T git@github.com 2>&1 | head -3
# 或测 DNS 是否被劫持
getent hosts github.com        # 若解析到 198.18.x.x 即为透明代理拦截
```

**两种结果，两种路径：**

| 判定 | 现象 | 走哪条路 |
|---|---|---|
| ✅ 连通 | `Hi szlxjqr!` 或能 clone | 直接 git 工作（见第 8 节） |
| ❌ 全封 | DNS→`198.18.x.x` / `Connection closed` / `TLS handshake non-properly terminated` | **走中转模式，不要反复重试** |

**中转模式（git 不可达时）**：
```
[受限任务] ──开发/改文件──→ 上传到 T 网盘（tdrive） ──→ [可连 git 的任务] 拉取并 git commit/push
```
- 受限任务：只负责写代码，把改动文件（或整包）传到 T 网盘（tdrive）根目录 `IxkOwRcwRUxu`
- 可连 git 的任务（当前这个沙箱）：从 T 网盘（tdrive）拉取 → 在本地 `frontend/` 落地 → `git add/commit/push`
- 双方仅通过 **T 网盘文件** 交换，彻底绕开受限沙箱的网络封锁
- 也可用 T 网盘源码包（tdrive） `mfr-cloud-finance-src.tar.gz`（`file_id: InrDRdZmGnAs`）做整包同步

> 注：受限任务若需要 SSH key，可用临时 `T1.md`（T 网盘根目录 `IxkOwRcwRUxu`）取私钥落盘；用完删 `T1.md`。

---

## 8. 新任务接手协议（Bootstrap Checklist）

新建任务**先读本文件**（GitHub 代码仓库 `docs/STATUS.md` 为权威源；git 不通时可从 T 网盘（tdrive）根目录 `IxkOwRcwRUxu` 取副本），然后按序执行：

> **本地环境一致性（重要，别担心要"学配置"）**：新任务的本地环境和本任务**开箱即用、基本一致**——Node/npm/Python 运行时、全局工具（`http-server`/`typescript`/`pnpm` 等，均为 CloudStudio 镜像预装）、所有源码与构建配置（在 git 里）都一致，无需从我这里学任何本地配置窍门。需要说明的本地状态：(a) 依赖：`mfr-cloud-finance/frontend/node_modules`（含 vite/vue-tsc/typescript 的**完整前端依赖，约 1.4 万文件，已提交进 git**，靠 .gitignore 的 `!frontend/node_modules/` 例外放行）；仓库根那份残缺的 `node_modules/` 已移出。**clone 后通常无需 `npm install`，可直接 `npm run build`**（步骤 5）；(b) SSH：`~/.ssh/config`（443 路由）与私钥——仅用于**推送**，本文件已写死做法，照抄即可。
> 最小起步（只看不改、不推送时）：`git clone`(HTTPS 公开库，无需 SSH) → `cd mfr-cloud-finance/frontend && npm run build`（依赖已在仓库内）→ 起预览。如需刷新/升级依赖再 `npm install`（需联网）。SSH/config/key 只在你想 push 时才需要。

1. **读 STATUS.md** —— 已获得项目全貌、git 地址、SSH 配方、当前进度、待办
2. **取代码**（二选一）：
   - git 连通 → `git clone git@github.com:szlxjqr/mfr-cloud-finance.git`
   - git 不可达 → 从 T 网盘（tdrive）下载 `mfr-cloud-finance-src.tar.gz`（`file_id: InrDRdZmGnAs`）解包
3. **配 SSH**（若需推送）：写 `~/.ssh/config`（见第 7 节），如需 key 取 `T1.md` 落盘 `id_ed25519`（`chmod 600`）
4. **测连通性**：`ssh -T git@github.com` —— 通就直连，不通就切**中转模式**（第 7 节）
5. **装依赖 + 构建**（完整前端依赖已随 git 提交在 `frontend/node_modules`，通常无需 `npm install`）：
   ```bash
   cd /workspace/mfr-cloud-finance/frontend
   npm run build        # 产出 frontend/dist，cwd 必须在 frontend，否则报 Missing script
   # 仅在升级/新增依赖时才需要联网重装：
   # npm install        # 需要能访问 npm registry（registry.npmjs.org）
   # 若需跑后端：
   pip install -r ../backend/requirements.txt   # 需要能访问 PyPI
   ```
   > 环境前提（CloudStudio 沙箱预装，各任务一致）：Node v22 / npm 11 / Python 3.11，无需手动装运行时。
   > **风险点**：只有 `npm install`(升级依赖) / `pip install` 需要外网。若所在沙箱对外网络整体受限（参考第 7 节"全封"情形），常规 `npm run build` 仍可离线进行（依赖已在仓库）；仅当要新增依赖或跑后端时才需外网 → 否则只能**改代码 + 中转推送**，本地无法 build/preview；构建与预览交给可联网的任务。
6. **预览**：`setsid python3 -m http.server 8137 --bind 0.0.0.0 < /dev/null &`，访问本任务的预览地址
   > **注意**：STATUS.md 里的「预览地址」是**当前这个沙箱**的（含 `x-cs-sandbox-id=2a28c3ff...`）。**每个新任务有自己的 sandbox-id**，预览 URL 不同——用 CloudStudio 预览功能 / preview 技能获取本任务专属地址，不要直接套用旧 URL。
7. **收尾**：改动同步更新 STATUS.md 对应小节 + 刷新底部维护记录，再 commit/push（中转则交给可连 git 的任务）

---

## 9. 开发日志 vs STATUS 分工

> 核心目标：杜绝"所有历史堆进同一对话 → 上下文爆炸（已发生过 400 崩任务）"。**日志负责记全，STATUS 负责记精**，两者互补、不替代。

### 判断法（写之前问一句）
新信息来了 → 它是「**历史 / 过程 / 技术细节 / 踩坑经过**」还是「**影响当前状态 / 下一步 / 他人接手必知**」？

| 维度 | 开发日志（可无限长） | STATUS（死守精简） |
|---|---|---|
| 记什么 | Session 时间线、做了什么、怎么做的、踩坑经过 | 现状快照、待办、关键决策**结论**、接手速查 |
| 不记什么 | 不要把结论抄成速查卡 | 不抄日志细节，不写过程流水 |
| 谁来读 | 追溯 / 复盘时按需读 | **接手者唯一入口，新任务只读它** |
| 体量策略 | 记全，一直长没关系（反正不进模型） | 目标 <200 行，常新不长胖 |

### MFR 真实示例
- 日志写**过程**："Session 23 用 `xlrd` 解析 `getExcel.xls`，生成 187 科目到 `accountData.ts`"
- STATUS 写**现状**："187 个标准科目已初始化到 `accountData.ts`（资产44/负债57/权益14/成本7/损益65）"
- 日志写**经过**："刷新 404，History 模式 + `http.server` 无 fallback → 改 `createWebHashHistory()`"
- STATUS 写**结论**：第 4 节「刷新 404 → 改 HashRouter」一行带过

### 两条铁律（缺一不可）
1. **接手只读 STATUS，不读日志全文** —— 守住这条，日志写到 1000 行都不会再 400。
2. **每次会话结束刷新 STATUS** —— 把日志里的"现状/待办/关键决策"提炼进对应小节，再 commit/push。

### 完整规范见资产库
`开发日志使用规范.md` / `STATUS使用规范.md` 在项目资产库，含模板与更多示例，本节约简其要义。

---

## 10. 存储位置与命名规范

> **总原则**：**GitHub 代码仓库 = 唯一权威源**。所有项目文件（代码 + STATUS + 开发日志 + 研发成果汇总 + 规范）只写 GitHub `docs/`，不另存"原创"副本。T 网盘与资产库都不是"第二真相"，只是副本或中转。

### 10.1 三处存储的唯一分工
| 正式名称 | 简称 | 角色 | 资料以谁为准 |
|---|---|---|---|
| **GitHub 代码仓库** | Git 仓库 | **唯一权威源**：所有文件唯一真相，均在 `docs/` | ✅ 唯一真相 |
| **项目资产库** | 资产库 | **接手入口柜**：WorkBuddy「资产」标签页；只放 `STATUS.md` 作便捷入口（副本，可能滞后，含引导段） | 同步副本，滞后以 Git 仓库为准 |
| **T 网盘（tdrive）** | 网盘 | **网络兜底中转**：git 不可达时文件交换区（临时，取走即同步仓库） | 临时，取走即同步仓库 |

### 10.2 接手闭环（新任务必读，自动自愈）
```
新任务第一步 → 到「资产库」读 STATUS.md（入口副本，即便略旧也够用）
   │  立刻明白：项目全貌 / git 地址 / SSH 配方 / 进度 / 待办
   ▼
按本文件顶部引导 → 去 GitHub 拉【最新】STATUS.md
   ├─ git 可达 → git clone / pull
   └─ git 不可达 → 从 T 网盘（tdrive）根目录 IxkOwRcwRUxu 取 STATUS.md 副本
   ▼
把最新版同步回资产库副本  ← 闭环：旧副本被自愈为最新
```
> **关键**：资产库副本即使忘记更新，只要它顶部的「引导段」不过时（git 地址 / SSH 443 配方长期有效），新任务就能靠它找到 GitHub 最新版，不会卡死。这就是"入口放资产库、全量放 GitHub"能成立的根本原因。

### 10.3 资产库 STATUS 副本的"永不过时引导段"（模板）
> 本段即本文件**顶部**那段 📌 提醒，复制到资产库后自动生效；GitHub 与资产库用**同一份文件**，无需维护两份不同内容。
> ⚠️ **本文件副本位于 WorkBuddy 资产库，可能滞后。权威以 GitHub `docs/STATUS.md` 为准（当前 HEAD：`<hash>`）。**
> 读到本文后请：① 按本段引导去 GitHub 拉最新版；② 把最新版同步回本资产库副本。
> **如何获取最新版**：`git clone git@github.com:szlxjqr/mfr-cloud-finance.git`（SSH 443 配方见 §2）；若 git 不可达，从 T 网盘（tdrive）根目录 `IxkOwRcwRUxu` 取 `STATUS.md` 副本。

### 10.4 命名纪律（强制）
1. **所有文件只写 GitHub（Git 仓库 `docs/`）**：资产库、T 网盘都不存放"原创"文件，只放副本或中转包。
2. **资产库只放 STATUS.md（入口）**：开发日志 / 研发成果汇总等不放资产库，以 GitHub 为准、按需 git 取（避免副本漂移、也避免资产库臃肿）。
3. **改完文件：先 push GitHub，再同步 T 网盘 + 资产库**（如用到），杜绝三处漂移。
4. **新任务接手只读 STATUS.md**（入口那份足够全明白），绝不读开发日志全文——守此条，日志写到 1000 行也不会 400。

### 10.5 命名禁令（统一术语）
- ❌ "项目网盘根目录""tdrive 源码包""在线文件库""网盘"指资产库 → ✅ 统称**资产库**
- ❌ "tdrive""项目网盘"指 tdrive → ✅ 统称 **T 网盘**
- ❌ 其他指向 Git 仓库的模糊说法 → ✅ 统称 **Git 仓库 / GitHub**

---

## 11. 维护记录

- **最后更新**：2026-07-21
- **Git HEAD**：`5de3faa`（main；已 push 到 GitHub 远程）
- **本机运行（Mac，Plan A 单机）**：后端 `uvicorn app.main:app --port 8521` 同源托管 `frontend/dist/`；前端改动后 `cd frontend && npm run build` 重建（`dist/` 已 gitignore，仅源码入库）。
- **更新内容**：
  1. 新增发票报销模块 P0+P1+P2 闭环（进项发票后端持久化、InvoiceInput.vue 接真实后端、发票↔报销单关联、归档上传、凭证草稿）。
  2. 更新 §3 进度：完整页 17→19，占位页 17→15；新增「发票报销模块进度」表。
  3. §10 存储位置规范不变；本文件为 GitHub 权威副本，已与远程同步。
  4. 本次更新：报销单号规则改为 `BXGL`+4位年+4位年自增（如 BXGL20260001），新增 next-bill-no 预占接口；报销单「增加发票」按钮录入并关联多张发票，保存后自动汇总回填报销金额（改动 BillList.vue / reimburse.ts / reimburse.py）。
  5. 修复 bug：发票录入增加唯一性校验——同一发票号码（纸票叠加发票代码）全局不允许重复录入。后端 `create_invoice` 新增 `_find_duplicate` 命中返回 409「发票已存在（号码 X），请勿重复录入。」；前端三处 `invoiceApi.create` 的 catch 增加 `status===409` 专属告警（改动 invoice.py / BillList.vue / InvoiceInput.vue）。已实测：首建 201、同号再建 409、同号带代码纸票 201 不误伤、测试数据清理回查 404。
  6. 新增 16 位可读「发票编码」`invoice_code` 替代纯整数 id（FP+YYYYMMDD+类型码2位+当日序号4位，如 FP20260721ZP0001）。并抽离**并发安全统一编码生成器** `utils/codegen.py`：序号由 `code_counters` 表「乐观锁」原子分配（`UPDATE...WHERE value=:cur`，并发竞争者读取到旧值已失效→0 行→自动重试），报销单号 `BXGL+year+seq` 也改用它并从历史最大编号继承 seed 防碰撞。连接层加 `busy_timeout=30`（并发写等待而非报 locked）；业务表对编码加 UNIQUE 约束兜底。已压测：同日期+类型并发创建 15 张发票，`invoice_code` 全部唯一无碰撞；库内 9 张旧发票已补生成编码（改动 codegen.py / code_counter.py / database.py / invoice 模型+schema / reimburse.py / main.py / 前端类型与列表列）。
  7. 新增报销单**一级审批流程**：`reimbursement_bills` 表新增 `approver`（审批人）和 `approve_remark`（审批意见）字段；`approve`/`reject` 接口接收 `{approver, remark}`，必填审批人并记录审批日期。前端报销单列表点击「通过/驳回」弹出审批弹窗，填写审批人和意见；审批通过后状态变为「已通过」并生成正式报销单，可点击「提交财务」流转到「已支付」。已实测测试报销单完整流程：待审批 → 审批通过 → 提交财务 → 已支付。
  8. 新增「我的报销」页面（`/reimburse/mine`）：按申请人 + 状态筛选，展示已提交及以上状态的报销单；新增「物品报销单」详情页（A4 打印友好），含基本信息、报销事由、费用明细（发票编码/类型/销方/项目/金额/税率/税金/价税合计）、汇总付款、审批签章区。后端详情接口 `GET /reimbursements/{bid}` 通过 `selectinload` 一次性返回关联发票及明细；`ReimbursementBill` 与 `Invoice` 建立双向 relationship。
  9. 物品报销单详情页版式微调，贴合老板提供的差旅费报销单参考：整体字号 10.5pt→10pt、表格内边距 6/8px→4/6px、费用明细表单独 9.5pt、发票编码列宽 130px→150px（避免 16 位编码 FP2026xxxxZP000x 被挤压换行）。纯视觉，数据结构/接口未变（改动 BillDetail.vue）。
  10. 物品报销单费用明细由「一行一发票明细」改为「一行一发票」汇总式（更贴近参考图简洁感）：按发票聚合，数量求和、不含税/税金/价税合计求和，税率显示有效税率（税金÷不含税，四舍五入整数%），「项目/物品」列展示该发票去重后的物品名（超过 3 项显示「…等」）。汇总与付款的合计逻辑同步改为基于发票级聚合（改动 BillDetail.vue）。
  11. 老板反馈汇总表仍「放不下」，改为**模拟发票票面方框卡片**：费用明细区由表格改为两列网格（flex-wrap，每张发票一个带边框的方框卡片 `invoice-box`，`break-inside:avoid` 保证打印不跨页断裂）；卡片表头显示发票编码（Courier 加粗）+ 类型·日期（小字），卡片体用 2 列 grid 排布销方/项目（整行）/数量/不含税/税率/税金/价税合计（整行高亮，虚线分隔）。更贴合发票存根联观感，A4 上紧凑成片（改动 BillDetail.vue 模板与样式，移除原 detail-table CSS）。
  12. 老板截图反馈「价税合计挡住发票编号/日期、物品字太大、类型可缩写」：发票卡片再优化——类型做缩写映射（增值税专用发票→专票，增值税普通发票→普票，电子普通发票→电子普票等）；右侧价税合计存根区宽度从 31% 缩至 24%，金额字号从 13pt 减至 11pt，不再遮挡左侧；开票日期从表头移到单独小字行，确保 16 位发票编码完整露出；销方字号 9.5pt→9pt、物品字号 8pt→7.5pt，整体更紧凑耐看（改动 BillDetail.vue）。
  13. 老板再次截图：发票类型标签「专票」单独悬在销方名上方，容易被误读为销方标注。调整为**类型标签改为发票号码后缀**（`410305...2018 · 专票`），蓝底白字实心 pill，与发票号码形成同一视觉组；左侧不再单独放类型标签，销方名上方视觉更干净（改动 BillDetail.vue 模板与样式）。
  14. 老板截图反馈左侧号码/日期下方到销方名之间有一大片空白未利用：将发票类型标签**从号码后缀移回左侧空白区**（开票日期下方、销方名上方），做成大号醒目的蓝白渐变徽章（11pt 加粗、圆角阴影），充分利用空间；发票号码恢复单独一行显示（改动 BillDetail.vue）。
- **对应提交**：`a41588f`（发票报销功能）、`aaaae4c`（STATUS 进度更新）、`21f909e`（单号+增加发票）、`e0fd4b8`（STATUS）、`95dd9bc`（重复校验修复）、`df3ce53`（16位发票编码+并发安全生成器）、`3ab900d`（一级审批流程）、`475fda7`（我的报销+物品报销单详情）、`5ad4a7a`（STATUS 记录）、`f4faf53`（详情页版式微调）、`3a5f301`（一行一发票汇总式）、`c55a157`（发票方框卡片）、`bc3ad58`（火车票风卡片）、`a8b461b`（卡片布局优化：编码日期露全/类型缩写/价税区缩小/物品字号调小）、`de17513`（发票号码+开票日期分行）、`83c8d6c`（类型标签改为号码后缀）、`5de3faa`（类型徽章移到左侧空白区并放大美化）
- **坑**：① `npm run build` 的 `vue-tsc -b` 类型校验——`ReimbursementBill.bill_no` 为 `string | null | undefined`，赋给 `form.bill_no`（`string | null`）需 `?? null` 兜底；② 8521 端口若被上次会话遗留的旧后端占用，新进程会 bind 失败（`address already in use`），需先 `lsof -ti tcp:8521 | xargs kill` 再起；③ `git push` 仍走 `GIT_HTTP_VERSION=1.1`（见 §4，HTTPS 远程）。
