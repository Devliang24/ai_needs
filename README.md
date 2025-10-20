# AI Requirement Analysis Platform (MVP)

基于《AI_REQUIREMENT_ANALYSIS_PLATFORM_MVP.md》方案的基础实现，包含 FastAPI 后端与 React 前端的最小可运行骨架。

## 目录结构

```
.
├── backend/                  # FastAPI 后端
│   ├── app/                  # 源码
│   ├── tests/                # Pytest 测试
│   ├── requirements.txt      # Python 依赖
│   └── .env.example          # 环境变量模板
├── frontend/                 # React/Vite 前端
│   ├── src/
│   ├── package.json
│   └── .env.example
├── docker-compose.yml        # 本地编排（含 PostgreSQL/Redis）
└── AI_REQUIREMENT_ANALYSIS_PLATFORM_MVP.md
```

## 快速开始

### 后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows 使用 .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # 如需自定义配置可在此修改
uvicorn app.main:app --reload
```

运行测试：

```bash
pytest
```

默认使用 `sqlite+aiosqlite`，若需 Postgres/Redis 请修改 `.env` 中的 `DATABASE_URL` 与 `REDIS_URL` 并启动对应服务（本地快速运行可将 `REDIS_URL` 设为 `fakeredis://` 使用内存模拟）。

系统默认使用真实的多智能体分析流程，请在 `.env` 中配置 `QWEN_API_KEY`（以及可选的各角色专用模型配置）以保证 AutoGen 调用成功。

### 前端

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

浏览器访问 `http://localhost:3000`。

### Docker Compose（可选）

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
docker compose up -d
```

## 已实现能力

- 📄 文档上传：支持存储文件至本地并记录元数据，重复文件通过 SHA256 去重。
- 🧠 会话管理：可创建需求分析会话，查询会话列表、详情及占位的确认/结果接口。
- 🔌 WebSocket：提供最小的 echo 端点与前端占位 UI，方便后续接入多智能体编排结果。
- 🖥️ 前端骨架：上传、会话信息、Agent 对话面板、确认卡片与导出入口均已落地，便于快速扩展。
- ✅ 健康检查测试：`/healthz` 接口通过 Pytest 校验。

## 后续建议

- 接入真实的多智能体流程与 Redis 进度缓存，替换当前的占位逻辑。
- 补充导出功能（XMind/Excel）并完善自动化测试覆盖。
- 针对生产环境区分开发/生产配置，完善日志与权限控制。
