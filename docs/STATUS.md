# 智慧经营 (Cloud Finance) — 项目状态速查表 (STATUS)

> **用途**：压缩上下文后，只读本文件即可完全同步项目状态。每次会话结束前更新「维护记录」。
> **维护规则**：任何代码/数据/配置/进度变更后，同步更新对应小节并刷新底部「维护记录」。

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

### 页面进度：17 完整页 + 17 占位页
- **完整业务页 (17)**：仪表盘(1) + 凭证管理(3) + 基础账簿(6) + 辅助账簿(6) + 科目管理(1)
- **占位页 (17)**：报表(5) + 出纳(3) + 资产(1) + 工资(7) + 发票(5) + 结账(2) + 设置其余(11)
- 视图目录：`dashboard / voucher(凭证) / general-ledger / auxiliary-ledger / settings / reports / cashier / payroll / invoice / closing / assets`

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

> **权威副本声明**：本文件（STATUS.md）的唯一真相源是 **GitHub 代码仓库** `docs/STATUS.md`。T 网盘与项目资产库中的副本均为同步镜像，若三者不一致，**以 GitHub 为准**。

### 三个存储位置（统一命名，以后禁用别称）
| 正式名称 | 简称 | 它是什么 | 角色 |
|---|---|---|---|
| **GitHub 代码仓库** | Git 仓库 | `git@github.com:szlxjqr/mfr-cloud-finance.git` 的 `docs/` | **权威源**：代码 + STATUS + 开发日志 + 全部文档的唯一真相 |
| **T 网盘（tdrive）** | 网盘 | 腾讯网盘/云空间，根目录 `IxkOwRcwRUxu` | **兜底中转**：git 不可达时文件交换区（存 STATUS 副本 / 源码包 / 临时密钥），取走即同步仓库 |
| **项目资产库** | 资产库 | WorkBuddy 项目「资产」标签页文件柜 | **平台展示/引用柜**：在 WorkBuddy UI 直接看、可 @ 引用 |

### 命名纪律（强制）
1. 全文只用以上三个正式名；**tdrive 一律简称"T 网盘"**，禁用"项目网盘根目录""tdrive 源码包""在线文件库"等易混叫法。
2. 新任务接手读源优先级：**GitHub clone → T 网盘副本（git 不通时）→ 资产库（WorkBuddy 内便捷看，滞后以仓库为准）**。
3. `STATUS.md` / `开发日志.md` 改完：**先 push GitHub，再同步 T 网盘 + 资产库**，杜绝三处漂移。
4. T 网盘与资产库的副本，认准 GitHub `docs/` 版本为基准。

---

## 11. 维护记录

- **最后更新**：2026-07-21
- **Git HEAD**：`822dd96`（main；本次更新基线，新增 §10 在此基础上）
- **更新内容**：新增 §10「存储位置与命名规范」（GitHub 代码仓库=权威源 / T 网盘=兜底中转 / 项目资产库=展示柜；命名纪律 + 接手读源优先级）；并**全文统一术语**：tdrive→「T 网盘（tdrive）」、项目网盘根目录→T 网盘，§1/§2/§5/§7/§8 旧称已清理；§9 与 §1~§8 正文逻辑不变。
- **对应提交**：`822dd96`（本次 §10 基线）、本提交（§10 新增 + 术语统一）
