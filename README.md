# AI Requirement Analysis Platform

智能需求分析平台，支持文档/图片上传、VL模型文本识别、多智能体协作分析，自动生成测试用例。

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

## 核心功能

### 📸 图片识别与文档解析
- **双VL引擎支持**：
  - **PaddleOCR-VL**（推荐）：本地推理、0.9B参数、支持109种语言、专为文档解析优化
  - **Qwen VL**：云端API、快速部署、无需GPU
- **智能文本提取**：支持 PDF、DOCX、图片（PNG/JPG/JPEG/BMP）
- **Redis缓存**：SHA256去重 + 7天TTL，避免重复识别

### 🤖 多智能体协作
- **需求分析师**：解析需求、提取功能点
- **测试工程师**：生成测试用例
- **质量评审员**：评审测试覆盖度
- **测试补全工程师**：补充边界/异常用例

### 📊 结果导出
- **XMind导出**：思维导图格式
- **Excel导出**：表格格式，便于管理
- **实时进度**：WebSocket推送分析进度

### 🎯 技术特性
- ✅ FastAPI + React 18 现代化架构
- ✅ PostgreSQL + Redis 可靠存储
- ✅ Docker Compose 一键部署
- ✅ E2E自动化测试（Playwright）

## VL引擎配置

系统支持两种VL引擎，通过 `VL_ENGINE` 环境变量切换：

### 方案A：PaddleOCR-VL（推荐）

**优势**：
- 🔒 本地推理，数据不上传云端
- 💰 无API调用成本
- 🌍 支持109种语言
- 📊 专为文档解析优化（表格、公式、图表）
- ⚡ 0.9B参数，性能优异

**环境配置**：
```bash
# .env
VL_ENABLED=true
VL_ENGINE=paddleocr
```

**依赖安装**：
```bash
# 根据CUDA版本选择（推荐GPU加速）
# CUDA 12.6
pip install paddlepaddle-gpu==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu126/

# CUDA 12.3
pip install paddlepaddle-gpu==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu123/

# CPU only (较慢)
pip install paddlepaddle==3.2.0

# 安装 PaddleOCR
pip install 'paddleocr[doc-parser]'
```

**测试验证**：
```bash
python test_paddleocr_integration.py
```

### 方案B：Qwen VL

**优势**：
- ☁️ 云端API，无需本地GPU
- 🚀 快速部署，无需安装PaddlePaddle

**环境配置**：
```bash
# .env
VL_ENABLED=true
VL_ENGINE=qwen
VL_MODEL=qwen-vl-plus
QWEN_API_KEY=your_api_key_here
```

## 引擎对比

| 对比项 | PaddleOCR-VL | Qwen VL |
|--------|--------------|---------|
| **部署方式** | 本地模型 | 云端API |
| **成本** | 一次性（GPU） | 按调用次数 |
| **速度** | 快（本地GPU） | 中（网络延迟） |
| **隐私性** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **离线可用** | ✅ | ❌ |
| **语言支持** | 109种 | 多语言 |
| **文档优化** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **适用场景** | 生产环境、敏感数据 | 快速原型、无GPU环境 |
