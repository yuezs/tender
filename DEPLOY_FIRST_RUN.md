# DEPLOY_FIRST_RUN.md

# 首次部署 / 本地首次启动说明

本文档用于说明当前仓库在**首次部署**或**本地首次启动**时的推荐配置顺序、验证方法、常见故障排查与当前实现限制。

---

## 1. 适用范围

适用于以下场景：

- 本地开发环境首次启动
- 测试环境首次部署
- 正式环境首次部署前的准备与自检

---

## 2. 前置条件

在开始前，请先确认以下基础依赖已准备完成。

### 2.1 系统依赖

建议具备：

- Python 3.10+（建议与项目当前依赖兼容版本保持一致）
- Node.js 18+（建议使用较新的 LTS 版本）
- npm
- MySQL 8.x
- OpenClaw（若需要完整 Agent 链路）

### 2.2 需要提前确认的服务

如果你要跑完整链路，请先确认：

- MySQL 可正常连接
- OpenClaw Gateway 已可用
- 具备有效的 Gateway Token / Password

---

## 3. 推荐启动顺序

建议严格按以下顺序执行：

1. 配置后端环境变量
2. 配置前端环境变量
3. 初始化 MySQL
4. （完整链路）准备 OpenClaw Agents
5. 启动后端
6. 启动前端
7. 按顺序做首次验证

这个顺序的目的是：**先把依赖和配置补齐，再启动服务，避免服务起来后逐项排错。**

---

## 4. 配置后端环境变量

先将：

- `backend/.env.example`

复制为：

- `E:\tender\backend\.env`

重点检查并修改以下配置项：

- `MYSQL_HOST`
- `MYSQL_PORT`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DATABASE`
- `AGENT_USE_REAL_LLM`
- `OPENCLAW_GATEWAY_URL`
- `OPENCLAW_GATEWAY_TOKEN` 或 `OPENCLAW_GATEWAY_PASSWORD`
- `OPENCLAW_STATE_DIR`（如果你的 OpenClaw 身份目录不在默认位置）

额外注意：

- `backend/.env.example` 只应保留占位值或空值，不能写入真实 Gateway Token。
- 本地调试时请把真实 token 只放到 `backend/.env`，不要回写到示例文件。

### 4.1 建议这样理解 `AGENT_USE_REAL_LLM`

- 如果你要跑**完整链路**，请设置：

```env
AGENT_USE_REAL_LLM=true
```

- 如果你只是想先把前后端页面和部分基础接口跑起来，可以临时设置：

```env
AGENT_USE_REAL_LLM=false
```

但需要特别注意：

> 当前代码里 `collect / extract / judge / generate` 没有真正的 mock 降级实现。关闭真实 LLM 后，这些接口会直接报错，因此只能先看基础页面和知识库部分。

### 4.2 后端配置来源

后端配置定义位置：

- `backend/core/config.py`

### 4.3 OpenClaw 身份缓存说明

当前 Gateway 接入除了读取 `OPENCLAW_GATEWAY_TOKEN / OPENCLAW_GATEWAY_PASSWORD` 外，还会维护本地 device 身份与 device token 缓存。

- 默认缓存目录受 `OPENCLAW_STATE_DIR` 控制。
- device token 典型落地位置为：
  - `OPENCLAW_STATE_DIR/identity/device-auth.json`
- 首次握手成功后，后端会保存新的 device token。
- 如果缓存 token 与网关状态不匹配，后端会自动清理该缓存并重试 1 次连接。

如果你碰到“之前能连，现在突然鉴权失败”的情况，可优先检查：

- `backend/.env` 中的 `OPENCLAW_GATEWAY_TOKEN / OPENCLAW_GATEWAY_PASSWORD` 是否仍有效
- `OPENCLAW_STATE_DIR` 是否指向了正确身份目录
- `identity/device-auth.json` 是否是旧环境遗留缓存

---

## 5. 配置前端环境变量

将：

- `frontend/.env.local.example`

复制为：

- `E:\tender\frontend\.env.local`

修改：

- `NEXT_PUBLIC_API_BASE_URL=http://你的后端地址`

本地开发通常填写：

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

前端实际读取位置：

- `frontend/lib/api.ts`

---

## 6. 初始化 MySQL

### 6.1 创建数据库

先在 MySQL 中执行：

```sql
CREATE DATABASE IF NOT EXISTS tender CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 6.2 安装后端依赖并初始化表

执行：

```powershell
cd E:\tender\backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python init_db.py
```

表初始化脚本位置：

- `backend/init_db.py`

另外，后端启动时也会自动执行一次 `init_tables()`，位置：

- `backend/main.py`

但建议**首次部署仍手动执行一次 `python init_db.py`**，这样问题更容易提前暴露。

---

## 7. 准备 OpenClaw（完整链路必需）

如果你要跑完整链路，请先准备 OpenClaw Gateway。

当前完整链路依赖 OpenClaw 的 Agent 调用，主要包括：

- 项目发现：`collect_agent`
- 招标抽取：`extract_agent`
- 是否建议投标：`judge_agent`
- 标书初稿：`generate_agent`

建议先执行：

```powershell
cd E:\tender\backend
python scripts\setup_openclaw_agents.py
```

该脚本会注册仓库内已有的 4 个 agent。

脚本位置：

- `backend/scripts/setup_openclaw_agents.py`

如果这一步没有完成，后续 `/discovery` 和 `/tender` 主链路通常无法正常工作。

如果 Gateway 已重置、重新初始化，或切换了不同身份目录，建议在首次联调前确认本地 `device-auth.json` 是否需要清理，避免旧 token 干扰连接。

---

## 8. 启动后端

执行：

```powershell
cd E:\tender\backend
.venv\Scripts\activate
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

默认本地访问地址：

- `http://127.0.0.1:8000`

---

## 9. 启动前端

执行：

```powershell
cd E:\tender\frontend
npm install
npm run dev
```

默认本地访问地址：

- `http://127.0.0.1:3000`

---

## 10. 首次启动后的验证顺序

建议按下面的顺序验证，而不是一上来就测完整链路。

### 10.1 健康检查

先检查基础服务是否正常：

- 后端健康检查：`http://127.0.0.1:8000/api/health`
- 前端首页：`http://127.0.0.1:3000`

### 10.2 先验证基础功能

优先测试：

- `/knowledge`

建议上传一个：

- `txt`
- `docx`

文档进行处理，确认知识库基础链路可用。

### 10.3 再验证完整链路

如果 OpenClaw 已就绪，再继续测试：

- `/discovery`
- `/tender`

这样可以快速区分：

- 是基础服务问题
- 还是 OpenClaw / Agent 注册问题

---

## 11. 两种运行目标：最小可运行 vs 完整可运行

为避免混淆，可以把当前仓库分成两种目标来看。

### 11.1 最小可运行

适用于：先确认前后端、数据库、基础页面和知识库是否可用。

需要：

- 后端 `.env`
- 前端 `.env.local`
- MySQL
- 后端依赖安装
- 前端依赖安装

可验证内容：

- `/api/health`
- 前端首页
- `/knowledge`

限制：

- `collect / extract / judge / generate` 相关功能不能正常工作

### 11.2 完整可运行

适用于：需要验证项目发现、招标分析、投标判断、标书初稿全链路。

额外需要：

- OpenClaw Gateway
- 有效的 Gateway Token / Password
- 已注册的 4 个 Agents
- `AGENT_USE_REAL_LLM=true`

可验证内容：

- `/discovery`
- `/tender`
- Agent 驱动链路

---

## 12. 测试 / 正式环境额外需要修改的地方

如果不是本地环境，而是测试或正式部署，还需要额外处理以下内容。

### 12.1 前端 API 地址

前端 `.env.local` 或部署平台环境变量中的：

- `NEXT_PUBLIC_API_BASE_URL`

必须改成**公网后端地址**或实际可访问地址。

否则前端仍会请求本地地址，导致接口不可用。

### 12.2 后端 CORS

当前后端 CORS 写死在：

- `backend/main.py`

只允许：

- `localhost:3000`
- `127.0.0.1:3000`

如果前后端分域部署，必须修改这里，否则浏览器会出现跨域失败。

建议后续将 CORS 来源改造成环境变量配置，而不是写死在代码中。

### 12.3 本地存储目录

- `storage/`

当前用于本地文件存储。部署时需要保证：

- 目录可写
- 目录可持久化
- 容器或服务器重启后数据不会丢失（如果业务要求保留）

---

## 13. 常见故障排查

### 13.1 `/api/health` 不通

优先检查：

- 后端是否已启动
- 端口是否为 `8000`
- 是否绑定在 `127.0.0.1`
- Python 虚拟环境是否正确激活
- `.env` 是否缺失或配置错误

### 13.2 前端页面能打开，但接口全报错

优先检查：

- `NEXT_PUBLIC_API_BASE_URL` 是否配置正确
- 后端服务是否实际可达
- 前端是否仍指向错误地址

### 13.3 浏览器报跨域错误（CORS）

优先检查：

- `backend/main.py` 中 CORS 白名单是否放行当前前端域名
- 前后端是否使用了不同域名 / 端口

### 13.4 `collect / extract / judge / generate` 报错

优先检查：

- `AGENT_USE_REAL_LLM` 是否为 `true`
- OpenClaw Gateway 是否可用
- `OPENCLAW_GATEWAY_URL` 是否正确
- `OPENCLAW_GATEWAY_TOKEN` / `OPENCLAW_GATEWAY_PASSWORD` 是否正确
- `setup_openclaw_agents.py` 是否已执行
- 4 个 agent 是否已成功注册

### 13.5 知识库功能正常，但 `/discovery` 或 `/tender` 不正常

这通常说明：

- 基础前后端链路已正常
- 问题集中在 OpenClaw / Agent 配置链路

建议优先检查 Agent 注册与 Gateway 配置，而不是先怀疑前端。

### 13.6 数据库初始化异常

优先检查：

- 数据库是否已创建
- MySQL 账号密码是否正确
- 目标用户是否有建表权限
- `MYSQL_DATABASE` 是否与实际数据库一致

---

## 14. 当前实现限制 / 已知边界

下面这些点建议在首次部署时就明确知道，避免对当前实现有错误预期。

### 14.1 主链路没有真正 mock 降级

虽然文档可能提到 mock / 规则版路径，但按当前代码实现：

- `collect`
- `extract`
- `judge`
- `generate`

并没有真正可用的 mock 降级方案。

也就是说，**主链路当前实际依赖真实 OpenClaw**。

### 14.2 PDF 真实解析未完成

当前 PDF 处理能力仍不完整，相关能力不能按“生产可用”假设处理。

### 14.3 招标主记录仍保存在本地 JSON

当前招标主记录并不是完整落在 MySQL 中，而仍保存在本地 JSON。

这意味着：

- 数据一致性能力有限
- 并发与部署方式要更谨慎
- 持久化策略需要额外关注

### 14.4 知识库仍是简易检索版

当前知识库能力更接近基础版，而不是完整成熟的检索系统。

### 14.5 CORS 尚未环境变量化

当前 CORS 配置仍是代码写死，不利于多环境部署。

---

## 15. 建议的首次部署验收清单

可以按下面清单逐项打勾：

### 15.1 基础配置

- [ ] 已复制并填写 `backend/.env`
- [ ] 已复制并填写 `frontend/.env.local`
- [ ] MySQL 数据库已创建
- [ ] `storage/` 目录可写

### 15.2 后端

- [ ] Python 虚拟环境已创建
- [ ] 后端依赖已安装
- [ ] `python init_db.py` 已执行成功
- [ ] `uvicorn main:app --reload --host 127.0.0.1 --port 8000` 启动成功
- [ ] `/api/health` 可访问

### 15.3 前端

- [ ] 前端依赖已安装
- [ ] `npm run dev` 启动成功
- [ ] 首页可访问
- [ ] 前端能正常请求后端 API

### 15.4 OpenClaw（完整链路）

- [ ] OpenClaw Gateway 可用
- [ ] Gateway Token / Password 配置正确
- [ ] 已执行 `python scripts\setup_openclaw_agents.py`
- [ ] 4 个 agent 注册完成
- [ ] `/discovery` 可正常测试
- [ ] `/tender` 可正常测试

---

## 16. 相关文件位置索引

- 后端环境变量模板：`backend/.env.example`
- 前端环境变量模板：`frontend/.env.local.example`
- 后端配置：`backend/core/config.py`
- 前端 API 配置：`frontend/lib/api.ts`
- 数据库初始化脚本：`backend/init_db.py`
- 后端入口：`backend/main.py`
- OpenClaw Agent 注册脚本：`backend/scripts/setup_openclaw_agents.py`

---

## 17. 一句话总结

如果只想先跑起来，请优先完成：

- 后端 `.env`
- 前端 `.env.local`
- MySQL 初始化
- 前后端启动
- `/api/health` 与 `/knowledge` 验证

如果要跑完整业务链路，则必须进一步完成：

- OpenClaw Gateway 配置
- Agent 注册
- `AGENT_USE_REAL_LLM=true`

否则 `/discovery` 和 `/tender` 这类主链路功能无法正常工作。
