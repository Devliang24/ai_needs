# AI Needs - 智能需求分析平台

基于多智能体协作的需求文档分析与测试用例自动生成平台。

## 技术栈

**后端**
- FastAPI - 异步 Web 框架
- SQLAlchemy - 数据库 ORM
- AutoGen - 多智能体协作框架
- Qwen - 大语言模型（支持视觉理解）

**前端**
- React 18 + TypeScript
- Ant Design - UI 组件库
- Zustand - 状态管理
- Socket.IO - 实时通信

## 功能特性

- 📄 **多格式支持** - 支持 PDF、DOCX、图片等格式的需求文档上传
- 🤖 **多智能体协作** - 需求分析师、测试工程师、质量评审专家协同工作
- 👁️ **视觉理解** - 基于 VL 模型直接分析图片内容，无需 OCR 预处理
- 💬 **实时交互** - WebSocket 实时推送分析进度和结果
- ✅ **人工确认** - 关键步骤支持人工审核和确认
- 📊 **结果导出** - 支持导出测试用例和分析报告

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 16+
- Docker & Docker Compose（可选）

### 本地开发

**1. 配置环境变量**

```bash
# 后端配置
cp backend/.env.example backend/.env
# 编辑 backend/.env，配置 QWEN_API_KEY

# 前端配置
cp frontend/.env.example frontend/.env
```

**2. 启动后端**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**3. 启动前端**

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:3000

### Docker 部署

```bash
docker compose up -d
```

服务默认运行在 8020 端口。

## 环境变量配置

### 后端核心配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `QWEN_API_KEY` | 通义千问 API 密钥 | - |
| `QWEN_BASE_URL` | API 基础地址 | https://dashscope.aliyuncs.com/compatible-mode/v1 |
| `ANALYSIS_AGENT_MODEL` | 需求分析模型 | qwen3-vl-flash |
| `TEST_AGENT_MODEL` | 测试用例生成模型 | qwen3-next-80b-a3b-instruct |
| `REVIEW_AGENT_MODEL` | 质量评审模型 | qwen3-next-80b-a3b-instruct |
| `DATABASE_URL` | 数据库连接 | sqlite+aiosqlite:///./ai_requirement.db |
| `REDIS_URL` | Redis 连接 | redis://redis:6379/0 |

### 前端配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `VITE_API_URL` | 后端 API 地址 | http://localhost:8000 |

## 项目结构

```
.
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── agents/            # 多智能体实现
│   │   ├── api/               # API 路由
│   │   ├── db/                # 数据库模型
│   │   └── llm/               # LLM 客户端
│   ├── requirements.txt
│   └── .env.example
├── frontend/                   # React 前端
│   ├── src/
│   │   ├── components/        # UI 组件
│   │   ├── services/          # API 服务
│   │   └── stores/            # 状态管理
│   ├── package.json
│   └── .env.example
└── docker-compose.yml
```

## 许可证

MIT
