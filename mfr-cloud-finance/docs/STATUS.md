# 云财务 (Cloud Finance) — 项目状态速查表 (STATUS)

> **用途**：压缩上下文后，只读本文件即可完全同步项目状态。每次会话结束前更新「维护记录」。
> **维护规则**：任何代码/数据/配置/进度变更后，同步更新对应小节并刷新底部「维护记录」。

---

## 1. 项目概览

- **产品名**：云财务（原 "MFR云财务" 已全局统一为 "云财务"，含 backend/doc/前端）
- **定位**：中小企业云会计系统（对标 WP5 云会计截图）
- **前端栈**：Vue 3 `<script setup>` + TypeScript + Vite（rolldown 打包）+ Element Plus + ECharts + Pinia + Vue Router(Hash)
- **后端栈**：FastAPI（Python 3.11）+ CORS，目前以 Mock 数据为主
- **绝对路径**：`/workspace/mfr-cloud-finance/`（本地电脑无此路径，跨任务/本地靠 git clone 或 tdrive 网盘获取）

---

## 2. 关键事实速查

| 项 | 值 |
|---|---|
| 项目根目录 | `/workspace/mfr-cloud-finance` |
| Git 远程 | `git@github.com:szlxjqr/mfr-cloud-finance.git`（SSH，公开仓库） |
| 当前分支 | `main`（HEAD: `607d5b6`） |
| 预览地址 | `https://webview.e2b.bj9.sandbox.cloudstudio.club/?x-cs-sandbox-id=2a28c3ff07dc470ca7e399c5464b5f7f&x-cs-sandbox-port=8137` |
| 预览服务 | `python3 -m http.server 8137 --bind 0.0.0.0`（服务 `frontend/dist`，Hash 路由刷新安全） |
| SSH 配置 | `~/.ssh/config` → `github.com` 走 `ssh.github.com:443`（沙箱 22 端口被封） |
| 前端源码文件数 | 35（`.vue` + `.ts`） |
| 科目数据 | `frontend/src/views/settings/accountData.ts`（187 科目，前端静态） |

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
| **GitHub 22 端口被封** | `ssh -T git@github.com` 超时 → `~/.ssh/config` 配 `Hostname ssh.github.com` + `Port 443` 解决 |
| **认证方式** | 已弃用 PAT token（曾失效），统一走 **SSH over 443**，免密推送。**SSH key 不要删**（删了配对失效，推送断） |
| **品牌统一** | "MFR云财务" → "云财务"，`git grep` 已验证无残留 |
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
git clone git@github.com:szlxjqr/mfr-cloud-finance.git   # 或用 tdrive 网盘 src 包
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

## 7. 维护记录

- **最后更新**：2026-07-19
- **Git HEAD**：`607d5b6`（main）
- **更新内容**：新建 STATUS.md 作为上下文压缩后的单一速查表；汇总项目概览/速查事实/进度/关键决策/常用命令/待办
- **对应提交**：`607d5b6` 之后新增 `docs/STATUS.md`（待提交）
