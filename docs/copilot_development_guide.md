# AI Needs 项目 - Copilot 完整开发指南

> 本文档提供使用 GitHub Copilot、Cursor 或其他 AI 辅助编程工具，从零开始开发 AI Needs 智能需求分析平台的完整提示词指南。

## 📋 目录

1. [项目概述](#项目概述)
2. [开发环境准备](#开发环境准备)
3. [项目初始化](#项目初始化)
4. [后端开发](#后端开发)
5. [前端开发](#前端开发)
6. [部署配置](#部署配置)
7. [测试与优化](#测试与优化)

---

## 项目概述

### 项目定位
构建一个基于多智能体协作的需求文档分析与测试用例自动生成平台。

### 核心功能
- 📄 支持 PDF、DOCX、图片等多格式需求文档上传
- 🤖 多智能体协作：需求分析师、测试工程师、质量评审专家协同工作
- 👁️ 视觉理解能力：基于 VL 模型直接分析图片内容
- 💬 实时交互：WebSocket 实时推送分析进度和结果
- ✅ 人工确认：关键步骤支持人工审核
- 📊 结果导出：支持导出测试用例和分析报告

### 技术栈

**后端技术栈：**
- FastAPI - 异步 Web 框架
- SQLAlchemy - 数据库 ORM
- PostgreSQL / SQLite - 数据库
- Redis - 缓存和会话管理
- AutoGen - 多智能体协作框架
- Qwen API - 大语言模型（包含视觉理解模型）
- PyMuPDF / Pillow - 文档处理

**前端技术栈：**
- React 18 + TypeScript
- Ant Design 5 - UI 组件库
- Zustand - 状态管理
- Socket.IO - WebSocket 实时通信
- Axios - HTTP 客户端
- Vite - 构建工具

---

## 开发环境准备

### 第一步：创建项目目录结构

**Copilot 提示词：**
```
请帮我创建一个项目目录结构，项目名称为 ai_needs，包含以下目录：
- backend/ (后端代码)
- frontend/ (前端代码)
- docs/ (文档)
- README.md (项目说明)
- docker-compose.yml (Docker 编排文件)
- .gitignore (Git 忽略文件)

在 .gitignore 中添加常见的 Python、Node.js、IDE 配置文件的忽略规则。
```

### 第二步：准备开发环境

**所需工具：**
- Python 3.10+
- Node.js 16+
- Docker & Docker Compose
- Git
- VS Code + Copilot / Cursor

---

## 项目初始化

### 创建 README.md

**Copilot 提示词：**
```
为 ai_needs 项目创建一个专业的 README.md 文件，包含以下内容：
- 项目标题：AI Needs - 智能需求分析平台
- 项目简介：基于多智能体协作的需求文档分析与测试用例自动生成平台
- 技术栈：后端使用 FastAPI + AutoGen + Qwen，前端使用 React + TypeScript + Ant Design
- 核心功能列表：多格式支持、多智能体协作、视觉理解、实时交互、人工确认、结果导出
- 快速开始指南：包含本地开发和 Docker 部署两种方式
- 环境变量配置表格：列出主要的配置项
- 项目目录结构说明
- MIT 许可证声明

使用清晰的 Markdown 格式，添加合适的 emoji 图标增强可读性。
```

---

## 后端开发

### Phase 1: 项目基础框架

#### 1.1 初始化 Python 项目

**Copilot 提示词：**
```
在 backend/ 目录下初始化一个 FastAPI 项目：

1. 创建 requirements.txt，包含以下依赖：
   - fastapi==0.109.0
   - uvicorn[standard]==0.27.0
   - python-multipart==0.0.9
   - websockets==12.0
   - SQLAlchemy[asyncio]==2.0.25
   - alembic==1.13.1
   - asyncpg==0.29.0
   - aiosqlite==0.19.0
   - redis==5.0.1
   - fakeredis==2.21.3
   - pyautogen==0.2.0
   - openai==1.10.0
   - dashscope>=1.24.6
   - PyMuPDF==1.20.2
   - pdfplumber==0.10.3
   - python-docx==1.1.0
   - Pillow==10.2.0
   - xmindparser==1.0.9
   - openpyxl==3.1.2
   - pydantic==2.5.0
   - pydantic-settings==2.1.0
   - python-dotenv==1.0.0
   - pytest==7.4.4
   - httpx==0.25.1
   - pytest-asyncio==0.21.1

2. 创建项目目录结构：
   backend/
   ├── app/
   │   ├── __init__.py
   │   ├── main.py           # 应用入口
   │   ├── config.py         # 配置管理
   │   ├── api/              # API 路由
   │   ├── models/           # 数据模型
   │   ├── db/               # 数据库操作
   │   ├── agents/           # 智能体实现
   │   ├── llm/              # LLM 客户端
   │   ├── parsers/          # 文档解析器
   │   ├── orchestrator/     # 工作流编排
   │   ├── websocket/        # WebSocket 管理
   │   ├── exporters/        # 结果导出
   │   ├── cache/            # 缓存管理
   │   ├── services/         # 业务服务
   │   ├── schemas/          # Pydantic 模型
   │   └── utils/            # 工具函数
   ├── tests/                # 测试文件
   ├── storage/              # 文件存储
   ├── requirements.txt
   ├── Dockerfile
   └── .env.example          # 环境变量模板

3. 在每个目录下创建 __init__.py 文件。
```

#### 1.2 创建配置管理模块

**Copilot 提示词：**
```
在 backend/app/config.py 中创建一个配置管理类：

使用 pydantic-settings 的 BaseSettings 类，定义以下配置项：
- app_host: FastAPI 主机地址（默认 0.0.0.0）
- app_port: FastAPI 端口（默认 8000）
- debug: 调试模式开关（默认 False）
- llm_provider: LLM 提供商（默认 "qwen"）
- qwen_api_key: 通义千问 API 密钥
- qwen_base_url: API 基础地址（默认 https://dashscope.aliyuncs.com/compatible-mode/v1）
- qwen_model: 默认模型名称
- vl_enabled: 是否启用视觉语言模型（默认 True）
- vl_model: VL 模型名称（默认 qwen3-vl-flash）
- vl_api_key: VL 模型 API Key
- vl_base_url: VL 模型 base URL
- pdf_ocr_enabled: 是否启用 PDF OCR（默认 True）
- pdf_ocr_model: PDF OCR 模型名称（默认 qwen-vl-ocr-2025-08-28）
- analysis_agent_model: 需求分析模型（默认 qwen3-vl-flash）
- analysis_multimodal_enabled: 是否启用多模态分析（默认 False）
- test_agent_model: 测试用例生成模型（默认 qwen3-next-80b-a3b-instruct）
- review_agent_model: 质量评审模型（默认 qwen3-next-80b-a3b-instruct）
- database_url: 数据库连接字符串（默认 sqlite+aiosqlite:///./ai_requirement.db）
- redis_url: Redis 连接字符串（默认 redis://localhost:6379/0）
- session_ttl_hours: 会话保留时间（默认 72 小时）
- max_file_size: 最大上传文件大小（默认 10MB）
- upload_dir: 上传目录（默认 /tmp/uploads）
- llm_timeout: LLM 超时时间（默认 120 秒）

添加以下辅助方法：
- get_agent_config(agent_type): 获取指定智能体的配置
- get_vl_config(): 获取 VL 模型配置
- get_pdf_ocr_config(): 获取 PDF OCR 配置
- resolved_upload_dir: 确保上传目录存在并返回绝对路径
- session_ttl_seconds: 将小时转换为秒

使用 @lru_cache 装饰器创建单例 get_settings() 函数。
从 .env 文件加载环境变量，支持不区分大小写。
```

#### 1.3 创建环境变量模板

**Copilot 提示词：**
```
创建 backend/.env.example 文件，包含所有必要的环境变量及其说明：

# 通义千问 API 配置（必填）
QWEN_API_KEY=your_qwen_api_key_here
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-plus

# 视觉语言模型配置
VL_ENABLED=true
VL_MODEL=qwen3-vl-flash
# VL_API_KEY=   # 留空则使用 QWEN_API_KEY
# VL_BASE_URL=  # 留空则使用 QWEN_BASE_URL

# PDF OCR 模型配置
PDF_OCR_ENABLED=true
PDF_OCR_MODEL=qwen-vl-ocr-2025-08-28

# 需求分析智能体配置
ANALYSIS_AGENT_MODEL=qwen3-vl-flash
ANALYSIS_MULTIMODAL_ENABLED=false

# 测试用例生成智能体配置
TEST_AGENT_MODEL=qwen3-next-80b-a3b-instruct

# 质量评审智能体配置
REVIEW_AGENT_MODEL=qwen3-next-80b-a3b-instruct

# 数据库配置
DATABASE_URL=sqlite+aiosqlite:///./ai_requirement.db
# DATABASE_URL=postgresql+asyncpg://user:password@localhost/ai_requirement

# Redis 配置
REDIS_URL=redis://localhost:6379/0

# 应用配置
DEBUG=false
MAX_FILE_SIZE=10485760
UPLOAD_DIR=/tmp/uploads
SESSION_TTL_HOURS=72

添加详细的使用说明和注释。
```

#### 1.4 创建应用入口

**Copilot 提示词：**
```
在 backend/app/main.py 中创建 FastAPI 应用入口：

1. 使用 @asynccontextmanager 定义 lifespan 函数：
   - 启动时：配置日志、创建上传目录、初始化数据库表
   - 关闭时：清理资源

2. 创建 create_app() 工厂函数：
   - 创建 FastAPI 实例，标题为"智能分析平台"
   - 注册 API 路由（前缀 /api）
   - 注册 WebSocket 路由
   - 配置 CORS 中间件（允许所有来源）
   - 添加健康检查端点 /healthz

3. 创建全局 app 实例

使用现代的 FastAPI 最佳实践，添加必要的类型注解。
```

---

### Phase 2: 数据模型与数据库

#### 2.1 创建数据库模型

**Copilot 提示词：**
```
在 backend/app/models/ 目录下创建 SQLAlchemy 数据模型：

1. session.py - 会话模型：
   - id: UUID 主键
   - status: 会话状态枚举（pending, processing, completed, failed, awaiting_confirmation）
   - stage: 当前阶段枚举（requirement_analysis, confirmation, test_generation, review, test_completion, completed）
   - progress: 进度（0.0-1.0）
   - created_at: 创建时间
   - updated_at: 更新时间
   - documents: 关联的文档列表（多对多关系）
   - results: 会话结果列表（一对多关系）

2. document.py - 文档模型：
   - id: UUID 主键
   - original_name: 原始文件名
   - storage_path: 存储路径
   - size: 文件大小
   - mime_type: MIME 类型
   - created_at: 创建时间
   - sessions: 关联的会话列表（多对多关系）

3. 使用 SQLAlchemy 2.0 风格的声明式基类
4. 使用 UUID 作为主键类型
5. 使用 Enum 类型定义状态和阶段
6. 添加适当的索引和约束
7. 使用 asyncio 扩展支持异步操作
```

#### 2.2 创建数据库会话管理

**Copilot 提示词：**
```
在 backend/app/db/base.py 中创建数据库会话管理：

1. 从 config 获取 DATABASE_URL
2. 创建异步 SQLAlchemy 引擎（create_async_engine）
3. 创建异步会话工厂（async_sessionmaker）
4. 定义 init_models() 函数：
   - 异步创建所有数据表
   - 支持 SQLite 和 PostgreSQL

5. 定义 Base 基类（DeclarativeBase）

使用 SQLAlchemy 2.0+ 的异步 API。
```

#### 2.3 创建数据仓储层

**Copilot 提示词：**
```
在 backend/app/db/ 目录下创建数据仓储层：

1. session_repository.py：
   - create_session(): 创建新会话
   - get_session(session_id): 获取会话详情（包含关联的文档和结果）
   - update_session_status(): 更新会话状态和阶段
   - add_session_result(): 添加会话结果
   - list_sessions(page, status): 分页查询会话列表
   - delete_expired_sessions(): 删除过期会话

2. document_repository.py：
   - create_document(): 创建文档记录
   - get_document(document_id): 获取文档详情
   - list_documents(session_id): 查询会话的文档列表
   - delete_document(): 删除文档

所有函数使用 async/await 语法，接受 AsyncSession 参数。
添加完善的错误处理和日志记录。
```

---

### Phase 3: API 路由

#### 3.1 创建文档上传 API

**Copilot 提示词：**
```
在 backend/app/api/uploads.py 中创建文档上传 API：

POST /api/uploads
- 接收 multipart/form-data 格式的文件上传
- 验证文件大小（不超过 MAX_FILE_SIZE）
- 验证文件类型（PDF、DOCX、图片格式）
- 生成唯一的文件名（UUID）并保存到 upload_dir
- 创建 Document 记录
- 返回文档信息（id, original_name, size, mime_type）

使用 FastAPI 的 UploadFile 类型，添加详细的错误处理。
```

#### 3.2 创建会话管理 API

**Copilot 提示词：**
```
在 backend/app/api/sessions.py 中创建会话管理 API：

1. POST /api/sessions：创建分析会话
   - 请求体：{ document_ids: [], config: {} }
   - 验证文档是否存在
   - 创建会话并关联文档
   - 触发异步分析流程（workflow.launch）
   - 返回会话信息

2. GET /api/sessions：查询会话列表
   - 查询参数：page, status
   - 返回分页结果

3. GET /api/sessions/{session_id}：获取会话详情
   - 返回会话信息、文档列表、当前状态

4. GET /api/sessions/{session_id}/results：获取会话结果
   - 返回最新的分析结果

使用 Pydantic 模型验证请求和响应数据。
使用 APIRouter 组织路由。
```

#### 3.3 创建 WebSocket 端点

**Copilot 提示词：**
```
在 backend/app/api/websocket.py 中创建 WebSocket 端点：

GET /ws/{session_id}
- 接受客户端连接
- 使用 WebSocketManager 管理连接
- 从 Redis 读取历史事件并发送给新连接
- 接收客户端确认消息（confirmation）并存储到 Redis
- 处理连接断开

在 backend/app/websocket/manager.py 中创建 WebSocketManager 类：
- 管理多个会话的 WebSocket 连接
- 支持广播消息到指定会话的所有客户端
- 处理连接和断开
- 线程安全

使用 FastAPI 的 WebSocket 支持。
```

#### 3.4 创建导出 API

**Copilot 提示词：**
```
在 backend/app/api/exports.py 中创建结果导出 API：

1. POST /api/sessions/{session_id}/exports/xmind：导出为 XMind 文件
   - 获取会话结果
   - 使用 XMindExporter 生成 XMind 文件
   - 返回文件流（application/octet-stream）

2. POST /api/sessions/{session_id}/exports/excel：导出为 Excel 文件
   - 获取会话结果
   - 使用 ExcelExporter 生成 Excel 文件
   - 返回文件流

使用 StreamingResponse 返回文件。
```

#### 3.5 创建路由汇总

**Copilot 提示词：**
```
在 backend/app/api/router.py 中汇总所有 API 路由：

创建 api_router 实例（APIRouter），包含以下子路由：
- uploads.router（上传）
- sessions.router（会话管理）
- exports.router（结果导出）
- images.router（图片服务，如果有）

设置统一的 tags 和前缀。
```

---

### Phase 4: LLM 与智能体集成

#### 4.1 创建 LLM 客户端

**Copilot 提示词：**
```
在 backend/app/llm/ 目录下创建 LLM 客户端模块：

1. vision_client.py - 基础视觉语言模型客户端：
   - extract_requirements(): 从图片中提取需求内容
   - 使用 dashscope 的 MultiModalConversation API
   - 支持自定义提示词模式（requirement, ocr）
   - 添加重试机制（最多 3 次）

2. vision_client_enhanced.py - 增强版客户端：
   - 添加 extract_requirements_with_retry() 函数
   - 支持更详细的错误处理
   - 添加日志记录
   - is_vl_available(): 检查 VL 模型是否可用

3. vision_client_cached.py - 带缓存的客户端：
   - 使用 Redis 缓存识别结果
   - 避免重复识别相同图片

4. multimodal_client.py - 多模态文档处理客户端：
   - 支持直接处理 PDF/图片文件
   - 自动选择合适的模型
   - 支持混合文档处理

使用 OpenAI 兼容的 API 格式。
添加完善的异常处理和重试逻辑。
```

#### 4.2 创建 AutoGen 智能体运行器

**Copilot 提示词：**
```
在 backend/app/llm/autogen_runner.py 中创建 AutoGen 智能体运行器：

1. 定义智能体函数：
   - run_requirement_analysis(document_data, callback): 需求分析
   - run_test_generation(analysis_result, callback): 测试用例生成
   - run_quality_review(test_cases, callback): 质量评审
   - run_test_completion(test_cases, review_result, callback): 用例补全

2. 每个函数：
   - 使用 AutoGen 的 ConversableAgent
   - 配置特定的系统提示词和 LLM 配置
   - 返回结构化结果（payload 和 content）
   - 支持可选的回调函数（用于流式输出）

3. 定义 AutogenOutputs 数据类：
   - analysis_message: 需求分析消息
   - test_message: 测试用例生成消息
   - review_message: 质量评审消息
   - completion_message: 用例补全消息
   - summary: 需求摘要
   - base_test_cases: 基础测试用例
   - completion_cases: 补充测试用例
   - merged_test_cases: 合并后的测试用例
   - metrics: 评审指标

4. 创建 _merge_test_cases() 辅助函数：
   - 合并基础测试用例和补充测试用例
   - 避免重复
   - 返回统一格式的 JSON

使用 pyautogen 库，配置 OpenAI 兼容的 API 格式。
添加详细的日志记录。
```

---

### Phase 5: 工作流编排

#### 5.1 创建工作流执行器

**Copilot 提示词：**
```
在 backend/app/orchestrator/workflow.py 中创建工作流编排器：

1. 定义 StageResult 数据类：
   - stage: AgentStage
   - sender: 智能体名称
   - content: 输出内容
   - payload: 结构化数据
   - progress: 进度
   - duration_seconds: 执行时长

2. 创建 AnalysisWorkflow 类：
   - launch(session_id): 启动异步分析流程
   - 管理后台任务集合

3. 创建 SessionWorkflowExecution 类：
   - execute(): 执行完整的分析流程
   - _handle_stage_result(): 处理每个阶段的结果
   - _wait_for_confirmation(): 等待用户确认（可选）
   - _emit_system_message(): 发送系统消息

4. 执行流程：
   a. 更新会话状态为 processing
   b. 处理上传的文档（提取文本或识别图片）
   c. 依次调用智能体：
      - 需求分析 -> 测试用例生成 -> 质量评审 -> 用例补全
   d. 每个阶段：
      - 调用 AutoGen 运行器
      - 解析 Markdown 为 JSON
      - 发送 WebSocket 消息
      - 等待用户确认（如果需要）
      - 保存结果到数据库
   e. 更新会话状态为 completed
   f. 发送完成消息

5. 支持两种模式：
   - 多模态模式（ANALYSIS_MULTIMODAL_ENABLED=true）：直接传递文件路径给 VL 模型
   - 文本模式：预先提取/OCR 所有文档内容

6. 添加 Markdown 解析函数：
   - _parse_markdown_test_cases(): 解析测试用例 Markdown 为 JSON
   - _parse_review_markdown(): 解析评审报告 Markdown 为结构化数据

使用 asyncio 实现异步执行。
添加完善的错误处理和日志记录。
```

---

### Phase 6: 缓存与会话管理

#### 6.1 创建 Redis 客户端

**Copilot 提示词：**
```
在 backend/app/cache/redis_client.py 中创建 Redis 客户端：

1. 创建全局 Redis 连接实例
2. 支持 Redis 和 FakeRedis（用于测试）
3. 提供基础的 get/set/delete 操作
4. 添加连接测试函数

使用 redis-py 异步客户端。
```

#### 6.2 创建会话事件管理

**Copilot 提示词：**
```
在 backend/app/cache/session_events.py 中创建会话事件管理：

使用 Redis 存储会话事件和状态：

1. append_event(session_id, event): 添加事件到会话
   - 存储到 Redis List（key: session:{session_id}:events）
   - 设置 TTL

2. get_events(session_id): 获取会话的所有事件

3. set_status(session_id, status): 设置会话状态
   - 存储到 Redis Hash（key: session:{session_id}:status）

4. get_status(session_id): 获取会话状态

5. set_confirmation(session_id, confirmation): 存储用户确认
   - 存储到 Redis String（key: session:{session_id}:confirmation）

6. get_confirmation(session_id): 获取用户确认

7. clear_confirmation(session_id): 清除确认数据

所有函数使用 async/await 语法。
```

#### 6.3 创建图片缓存

**Copilot 提示词：**
```
在 backend/app/cache/image_cache.py 中创建图片识别结果缓存：

1. 使用文件哈希作为缓存键
2. calculate_file_hash(): 计算文件 MD5 哈希
3. get_cached_result(): 从 Redis 获取缓存结果
4. set_cached_result(): 存储结果到 Redis
5. 设置合理的 TTL（例如 24 小时）

使用 Redis 存储，支持异步操作。
```

---

### Phase 7: 文档解析器

#### 7.1 创建文本提取器

**Copilot 提示词：**
```
在 backend/app/parsers/text_extractor.py 中创建文档文本提取器：

定义 extract_text(file_path, original_name) 函数：
- 根据文件扩展名选择合适的提取方法
- 支持的格式：
  * PDF：使用 PyMuPDF 或 pdfplumber
  * DOCX：使用 python-docx
  * TXT/MD：直接读取文本
  * 图片：返回空字符串（由 VL 模型处理）
- 返回提取的文本内容
- 添加错误处理和日志记录

处理编码问题和损坏的文件。
```

---

### Phase 8: 导出器

#### 8.1 创建 Excel 导出器

**Copilot 提示词：**
```
在 backend/app/exporters/excel_exporter.py 中创建 Excel 导出器：

定义 export_to_excel(test_cases_json, output_path) 函数：
- 使用 openpyxl 库
- 创建 Excel 工作簿
- 为每个模块创建一个工作表
- 表格列：用例ID、标题、前置条件、测试步骤、预期结果、优先级
- 添加表头样式（加粗、背景色）
- 自动调整列宽
- 保存到指定路径

支持 JSON 格式的测试用例数据：
{ "modules": [{ "name": "模块名", "cases": [...] }] }
```

#### 8.2 创建 XMind 导出器

**Copilot 提示词：**
```
在 backend/app/exporters/xmind_exporter.py 中创建 XMind 导出器：

定义 export_to_xmind(test_cases_json, output_path) 函数：
- 使用 xmindparser 库
- 创建 XMind 思维导图
- 根节点：测试用例
- 一级节点：模块名称
- 二级节点：测试用例标题
- 三级节点：详细步骤（前置条件、步骤、预期结果）
- 保存为 .xmind 文件

使用清晰的层级结构组织测试用例。
```

---

### Phase 9: Pydantic 模型

#### 9.1 创建 API 模型

**Copilot 提示词：**
```
在 backend/app/schemas/ 目录下创建 Pydantic 模型：

1. document.py - 文档相关模型：
   - DocumentUploadResponse: 上传响应
   - DocumentDetail: 文档详情

2. session.py - 会话相关模型：
   - SessionCreateRequest: 创建会话请求
   - SessionCreateResponse: 创建会话响应
   - SessionDetail: 会话详情
   - SessionListResponse: 会话列表响应
   - SessionResultsResponse: 会话结果响应

3. image.py - 图片相关模型（如果需要）

所有模型使用 Pydantic v2 语法。
添加字段验证和描述。
```

---

### Phase 10: 工具函数

#### 10.1 创建日志配置

**Copilot 提示词：**
```
在 backend/app/utils/logger.py 中创建日志配置：

定义 configure_logging(level) 函数：
- 配置 Python logging
- 设置日志格式：时间 - 级别 - 模块 - 消息
- 支持控制台输出
- 支持文件输出（可选）
- 支持不同的日志级别（DEBUG, INFO, WARNING, ERROR）

使用 Python 标准库 logging 模块。
```

---

### Phase 11: Dockerfile 与部署

#### 11.1 创建 Dockerfile

**Copilot 提示词：**
```
为后端创建 backend/Dockerfile：

1. 基于 python:3.10-slim
2. 设置工作目录 /app
3. 复制 requirements.txt 并安装依赖
4. 复制应用代码
5. 暴露 8000 端口
6. 默认命令：uvicorn app.main:app --host 0.0.0.0 --port 8000

使用多阶段构建优化镜像大小。
添加健康检查。
```

---

### Phase 12: 测试

#### 12.1 创建集成测试

**Copilot 提示词：**
```
在 backend/tests/ 目录下创建测试文件：

1. test_health.py - 健康检查测试
2. test_integration.py - API 集成测试
3. test_pdf_workflow.py - PDF 处理流程测试
4. test_vl_integration.py - VL 模型集成测试

使用 pytest 和 httpx 进行异步测试。
使用 pytest-asyncio 支持异步测试。
```

---

## 前端开发

### Phase 1: 项目初始化

#### 1.1 创建 React + TypeScript 项目

**Copilot 提示词：**
```
在 frontend/ 目录下创建一个 React + TypeScript + Vite 项目：

1. 使用 Vite 创建项目模板
2. 修改 package.json，添加以下依赖：
   dependencies:
   - react@^18.2.0
   - react-dom@^18.2.0
   - antd@^5.12.0
   - @ant-design/icons@^5.2.6
   - axios@^1.6.0
   - zustand@^4.4.7
   - socket.io-client@^4.6.1
   - react-markdown@^9.0.1
   - remark-gfm@^4.0.1
   - rehype-highlight@^7.0.2
   - highlight.js@^11.11.1
   - react-dropzone@^14.2.3
   - nanoid@^4.0.0

   devDependencies:
   - @types/react@^18.2.37
   - @types/react-dom@^18.2.15
   - @types/node@^20.11.5
   - @vitejs/plugin-react@^4.2.0
   - typescript@^5.3.0
   - vite@^5.0.0

3. 创建项目目录结构：
   frontend/
   ├── src/
   │   ├── main.tsx          # 应用入口
   │   ├── App.tsx           # 根组件
   │   ├── components/       # UI 组件
   │   ├── pages/            # 页面组件
   │   ├── services/         # API 服务
   │   ├── stores/           # 状态管理
   │   ├── hooks/            # 自定义 Hooks
   │   └── types/            # TypeScript 类型定义
   ├── public/
   ├── index.html
   ├── vite.config.ts
   ├── tsconfig.json
   ├── package.json
   └── .env.example

4. 配置 TypeScript（tsconfig.json）：
   - 启用严格模式
   - 配置路径别名
   - 支持 JSX
```

#### 1.2 配置 Vite

**Copilot 提示词：**
```
创建 frontend/vite.config.ts：

配置 Vite 开发服务器：
- 使用 @vitejs/plugin-react 插件
- 设置开发服务器端口为 3000
- 配置代理（可选）：将 /api 请求代理到后端
- 设置路径别名（@/ 指向 src/）

使用 TypeScript 编写配置文件。
```

#### 1.3 创建环境变量模板

**Copilot 提示词：**
```
创建 frontend/.env.example：

# 后端 API 地址
VITE_API_URL=http://localhost:8000

添加说明：
- VITE_ 前缀是 Vite 要求的
- 生产环境需要修改为实际的后端地址
```

---

### Phase 2: 类型定义

#### 2.1 创建 TypeScript 类型

**Copilot 提示词：**
```
在 frontend/src/types/ 目录下创建类型定义：

1. document.ts - 文档相关类型：
   - Document: 文档信息
   - DocumentUploadResponse: 上传响应

2. session.ts - 会话相关类型：
   - SessionStatus: 会话状态类型
   - AgentStage: 智能体阶段类型
   - SessionCreateRequest: 创建会话请求
   - SessionCreateResponse: 创建会话响应
   - SessionDetail: 会话详情
   - SessionListResponse: 会话列表响应
   - SessionResultsResponse: 会话结果响应
   - AgentResult: 智能体输出结果
   - TestCase: 测试用例
   - TestModule: 测试模块
   - ReviewResult: 评审结果

3. index.ts - 导出所有类型

使用 TypeScript 接口和类型别名。
```

---

### Phase 3: API 服务

#### 3.1 创建 HTTP 客户端

**Copilot 提示词：**
```
在 frontend/src/services/api.ts 中创建 API 服务：

1. 创建 axios 实例（apiClient）：
   - baseURL: 从环境变量读取（VITE_API_URL）
   - 默认 headers: Content-Type: application/json

2. 定义 API 函数：
   - uploadDocument(file): 上传文档
   - createSession(payload): 创建分析会话
   - fetchSessions(page, status): 查询会话列表
   - fetchSessionDetail(sessionId): 获取会话详情
   - fetchSessionResults(sessionId): 获取会话结果
   - exportSessionXmind(sessionId, resultVersion): 导出 XMind

所有函数使用 async/await 语法。
添加类型注解。
```

#### 3.2 创建 WebSocket 客户端

**Copilot 提示词：**
```
在 frontend/src/services/websocket.ts 中创建 WebSocket 客户端：

1. 定义 createSessionSocket(sessionId) 函数：
   - 根据 VITE_API_URL 构建 WebSocket URL
   - 自动处理 http/https 转换为 ws/wss
   - 返回 WebSocket 实例

2. 支持事件监听：
   - onopen: 连接建立
   - onmessage: 接收消息
   - onerror: 连接错误
   - onclose: 连接关闭

使用原生 WebSocket API。
```

---

### Phase 4: 状态管理

#### 4.1 创建 Zustand Store

**Copilot 提示词：**
```
在 frontend/src/stores/chatStore.ts 中创建全局状态管理：

使用 Zustand 创建 useAppStore，包含以下状态和方法：

状态：
- documents: 上传的文档列表
- session: 当前会话信息
- agentResults: 智能体输出结果列表
- currentStage: 当前阶段
- progress: 当前进度（0-1）
- isConnecting: WebSocket 连接状态
- selectedStage: 用户选中的阶段
- analysisRunning: 是否正在分析
- lastActivityTime: 最后活动时间
- documentHistories: 文档历史记录（按文档 ID 索引）
- webSocket: WebSocket 实例

方法：
- addDocument: 添加文档
- removeDocument: 删除文档
- clearDocuments: 清空文档列表
- setSession: 设置会话
- resetAnalysis: 重置分析状态
- addAgentResult: 添加智能体结果
- appendAgentResult: 追加智能体结果（流式更新）
- setAgentResults: 设置智能体结果列表
- clearAnalysisResults: 清空分析结果
- addSystemMessage: 添加系统消息
- setConnecting: 设置连接状态
- setProgress: 设置进度
- setSelectedStage: 设置选中的阶段
- setAnalysisRunning: 设置分析运行状态
- updateActivityTime: 更新活动时间
- setWebSocket: 设置 WebSocket 实例
- addDocumentHistory: 添加文档历史记录
- clearDocumentHistory: 清除文档历史记录

使用 localStorage 持久化上传的文档列表。
使用 TypeScript 类型注解。
```

---

### Phase 5: UI 组件

#### 5.1 创建文件上传组件

**Copilot 提示词：**
```
在 frontend/src/components/FileUploader.tsx 中创建文件上传组件：

使用 react-dropzone 和 Ant Design 的 Upload 组件：
- 支持拖拽上传
- 支持点击选择文件
- 支持多文件上传
- 限制文件类型：PDF、DOCX、图片
- 限制文件大小：10MB
- 显示上传进度
- 上传成功后添加到 store.documents
- 显示错误提示

使用 Ant Design 的 message 组件显示提示。
响应式设计，支持移动端。
```

#### 5.2 创建智能体流程进度组件

**Copilot 提示词：**
```
在 frontend/src/components/AgentFlowProgress.tsx 中创建流程进度组件：

使用 Ant Design 的 Steps 组件：
- 显示 5 个步骤：需求分析、测试用例生成、质量评审、用例补全、完成
- 根据 currentStage 高亮当前步骤
- 显示进度百分比
- 支持点击切换查看不同阶段的结果
- 使用不同的图标表示不同阶段
- 显示加载状态（isConnecting）

响应式设计：
- 桌面端：水平步骤条
- 移动端：垂直步骤条或简化显示

添加完整的 TypeScript 类型注解。
```

#### 5.3 创建智能体时间线组件

**Copilot 提示词：**
```
在 frontend/src/components/AgentTimeline.tsx 中创建智能体时间线组件：

使用 Ant Design 的 Timeline 和 Card 组件：
- 显示智能体输出结果列表（agentResults）
- 根据 selectedStage 过滤结果
- 每个结果显示：
  * 智能体名称和头像
  * 输出内容（支持 Markdown 渲染）
  * 执行时长（如果有）
  * 结构化数据（根据不同阶段）
- 空状态提示：等待智能体输出
- 自动滚动到最新消息

根据阶段渲染不同的内容组件：
- requirement_analysis: RequirementAnalysisView
- test_generation: TestCasesView
- review: QualityReviewView
- test_completion: SupplementalTestCasesView

使用 react-markdown 和 rehype-highlight 渲染 Markdown。
响应式设计，支持移动端。
```

#### 5.4 创建需求分析视图

**Copilot 提示词：**
```
在 frontend/src/components/RequirementAnalysisView.tsx 中创建需求分析视图：

显示需求分析结果：
- 使用 Ant Design 的 Card 组件
- 使用 Descriptions 组件显示结构化信息（如果有）
- 使用 react-markdown 渲染 Markdown 内容
- 添加代码高亮（highlight.js）
- 支持展开/折叠长内容

根据 payload 结构智能渲染：
- 如果有结构化数据，优先显示结构化视图
- 否则显示 Markdown 内容

添加 TypeScript 类型注解。
```

#### 5.5 创建测试用例视图

**Copilot 提示词：**
```
在 frontend/src/components/TestCasesView.tsx 中创建测试用例视图：

显示测试用例列表：
- 使用 Ant Design 的 Collapse 组件按模块分组
- 使用 Table 组件显示测试用例表格
- 表格列：用例ID、标题、前置条件、测试步骤、预期结果、优先级
- 支持展开/折叠详细信息
- 支持搜索和过滤
- 显示统计信息：总用例数、模块数

支持两种数据格式：
- JSON 格式：{ modules: [{ name, cases }] }
- Markdown 格式：自动解析为 JSON

添加导出按钮（导出为 Excel 或 XMind）。
响应式设计，支持移动端。
```

#### 5.6 创建质量评审视图

**Copilot 提示词：**
```
在 frontend/src/components/QualityReviewView.tsx 中创建质量评审视图：

显示质量评审结果：
- 使用 Ant Design 的 Card 和 Alert 组件
- 分为三个部分：
  1. 评审摘要：使用 Alert 组件高亮显示
  2. 发现的缺陷：使用 List 组件显示（红色标记）
  3. 改进建议：使用 List 组件显示（蓝色标记）

支持两种数据格式：
- 结构化 JSON：{ summary, defects, suggestions }
- Markdown 格式：自动解析为 JSON

使用图标增强可读性。
响应式设计。
```

#### 5.7 创建补充用例视图

**Copilot 提示词：**
```
在 frontend/src/components/SupplementalTestCasesView.tsx 中创建补充用例视图：

复用 TestCasesView 组件的逻辑，添加以下区别：
- 标题改为"补充测试用例"
- 添加说明：根据质量评审建议补充的测试用例
- 使用不同的颜色主题（例如绿色）

添加 TypeScript 类型注解。
```

#### 5.8 创建确认卡片组件

**Copilot 提示词：**
```
在 frontend/src/components/ConfirmationCard.tsx 中创建确认卡片组件：

用于显示需要用户确认的内容：
- 使用 Ant Design 的 Card 和 Button 组件
- 显示"确认"和"拒绝"按钮
- 支持编辑内容（可选）
- 点击确认后通过 WebSocket 发送确认消息
- 禁用状态：已确认或已拒绝

Props:
- agentResult: 智能体结果
- onConfirm: 确认回调
- onReject: 拒绝回调

使用 TypeScript 类型注解。
```

#### 5.9 创建状态栏组件

**Copilot 提示词：**
```
在 frontend/src/components/StatusBar.tsx 中创建状态栏组件：

显示实时状态信息：
- WebSocket 连接状态
- 当前阶段
- 进度百分比
- 分析运行状态

使用 Ant Design 的 Badge 和 Progress 组件。
使用不同颜色表示不同状态。
响应式设计。
```

---

### Phase 6: 页面组件

#### 6.1 创建主页

**Copilot 提示词：**
```
在 frontend/src/pages/Home.tsx 中创建主页组件：

布局分为两部分：
1. 左侧/上部（30%宽度）：
   - FileUploader 组件
   - 文档列表（使用 List 组件）
   - 支持单选文档（Radio）
   - 显示文件名和大小
   - 删除按钮
   - "开始分析"按钮

2. 右侧/下部（70%宽度）：
   - AgentFlowProgress 组件
   - AgentTimeline 组件

功能逻辑：
- 点击"开始分析"按钮：
  * 验证是否选中文档
  * 调用 createSession API
  * 建立 WebSocket 连接
  * 清空之前的分析结果
  * 设置 analysisRunning 状态
- WebSocket 消息处理：
  * agent_message: 添加到 agentResults
  * system_message: 添加系统消息
  * 更新进度和阶段
  * 自动切换到新阶段
  * 完成时保存历史记录
- 点击文档：
  * 选中该文档
  * 如果不在分析中，显示历史记录
- "清理会话"按钮：
  * 关闭 WebSocket
  * 清空分析状态
  * 重置进度
- 超时处理：
  * 10分钟无操作自动断开
  * 显示超时提示

响应式设计：
- 桌面端：左右布局
- 移动端：上下布局

使用 useEffect 管理 WebSocket 生命周期。
使用 localStorage 持久化文档列表。
添加完整的 TypeScript 类型注解。
```

---

### Phase 7: 自定义 Hooks

#### 7.1 创建媒体查询 Hook

**Copilot 提示词：**
```
在 frontend/src/hooks/useMediaQuery.ts 中创建媒体查询 Hook：

定义 useMediaQuery(query: string) Hook：
- 接受 CSS 媒体查询字符串
- 返回布尔值（是否匹配）
- 使用 window.matchMedia API
- 监听窗口大小变化
- 清理事件监听器

使用 TypeScript 类型注解。
```

---

### Phase 8: 应用入口

#### 8.1 创建 App 组件

**Copilot 提示词：**
```
在 frontend/src/App.tsx 中创建根组件：

1. 使用 Ant Design 的 ConfigProvider 配置全局主题：
   - 设置中文语言包（zhCN）
   - 自定义主题色（可选）

2. 使用 Layout 组件布局：
   - Content: 显示 HomePage

3. 全局样式：
   - 高度 100vh
   - 无外边距

使用 React 18 的 FC 类型。
```

#### 8.2 创建 main.tsx

**Copilot 提示词：**
```
在 frontend/src/main.tsx 中创建应用入口：

1. 导入 React 和 ReactDOM
2. 导入 App 组件
3. 导入全局样式（Ant Design CSS）
4. 使用 ReactDOM.createRoot 渲染 App

使用 React 18 的 StrictMode。
```

---

### Phase 9: 样式与优化

#### 9.1 创建全局样式

**Copilot 提示词：**
```
创建全局 CSS 样式（如果需要）：

1. 隐藏滚动条样式（.no-scrollbar）
2. 自定义 Markdown 代码高亮样式
3. 响应式布局辅助类
4. 动画效果

使用 CSS 模块或内联样式。
```

#### 9.2 优化性能

**Copilot 提示词：**
```
优化前端性能：

1. 使用 React.memo 包装组件（避免不必要的重渲染）
2. 使用 useMemo 和 useCallback 缓存计算和函数
3. 使用 React.lazy 和 Suspense 实现代码分割（如果需要）
4. 优化 WebSocket 消息处理（避免频繁更新状态）
5. 使用虚拟滚动（如果列表很长）

添加 TypeScript 类型注解。
```

---

## 部署配置

### Docker Compose 配置

**Copilot 提示词：**
```
创建 docker-compose.yml 文件，编排以下服务：

1. backend:
   - build: ./backend
   - ports: 8020:8000
   - env_file: backend/.env
   - volumes: 挂载代码和上传目录
   - depends_on: db, redis
   - command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

2. frontend（可选，注释掉）:
   - build: ./frontend
   - ports: 3004:3000
   - depends_on: backend
   - environment: VITE_API_URL=http://localhost:8020
   - command: npm run dev -- --host

3. db:
   - image: postgres:15-alpine
   - environment: POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
   - volumes: pgdata:/var/lib/postgresql/data

4. redis:
   - image: redis:7-alpine
   - command: redis-server --save '' --appendonly no

定义 volumes:
- uploads: 上传文件存储
- pgdata: PostgreSQL 数据

使用合理的容器名称和网络配置。
```

---

## 测试与优化

### 后端测试

**Copilot 提示词：**
```
为后端创建完整的测试套件：

1. 单元测试：
   - 测试配置管理（test_config.py）
   - 测试数据仓储（test_repositories.py）
   - 测试文档解析器（test_parsers.py）
   - 测试导出器（test_exporters.py）

2. 集成测试：
   - 测试 API 端点（test_api.py）
   - 测试 WebSocket 连接（test_websocket.py）
   - 测试完整工作流（test_workflow.py）

3. 使用 pytest fixtures 准备测试数据
4. 使用 FakeRedis 模拟 Redis
5. 使用 SQLite 内存数据库进行测试
6. 使用 httpx.AsyncClient 测试 API

运行测试：pytest tests/ -v --cov=app
```

### 前端测试

**Copilot 提示词：**
```
为前端创建测试（可选）：

1. 使用 Vitest 或 Jest 进行单元测试
2. 使用 React Testing Library 测试组件
3. 使用 MSW 模拟 API 请求

运行测试：npm run test
```

### 性能优化

**Copilot 提示词：**
```
优化系统性能：

后端优化：
1. 使用 Redis 缓存图片识别结果
2. 使用数据库连接池
3. 使用异步 I/O 操作
4. 优化 LLM 调用（批处理、重试策略）
5. 添加 API 限流（如果需要）

前端优化：
1. 使用 React.memo 和 useMemo
2. 使用虚拟滚动处理长列表
3. 使用 Suspense 和 lazy 实现代码分割
4. 优化 WebSocket 消息处理（防抖、节流）
5. 使用 Service Worker 实现离线功能（可选）
```

---

## 完整开发流程总结

### 开发步骤概览

1. **环境准备**：安装 Python、Node.js、Docker
2. **后端开发**：
   - 创建 FastAPI 项目
   - 配置数据库和 Redis
   - 实现 API 路由
   - 集成 LLM 和 AutoGen
   - 实现工作流编排
   - 添加 WebSocket 支持
3. **前端开发**：
   - 创建 React 项目
   - 实现状态管理
   - 开发 UI 组件
   - 集成 API 和 WebSocket
4. **部署配置**：
   - 创建 Dockerfile
   - 编写 docker-compose.yml
5. **测试与优化**：
   - 编写单元测试和集成测试
   - 性能优化
   - 安全加固

### 关键技术点

- **后端异步编程**：使用 async/await 和 asyncio
- **多智能体协作**：使用 AutoGen 框架
- **实时通信**：使用 WebSocket
- **文档处理**：使用 PyMuPDF、Pillow、python-docx
- **视觉理解**：使用 Qwen VL 模型
- **状态管理**：使用 Zustand
- **类型安全**：使用 TypeScript 和 Pydantic

### 调试技巧

1. 使用 FastAPI 的 `/docs` 端点测试 API
2. 使用浏览器开发者工具调试 WebSocket
3. 查看后端日志排查问题
4. 使用 React DevTools 调试组件状态

---

## 附录：常见问题

### Q1: 如何切换数据库？
修改 `DATABASE_URL` 环境变量，从 SQLite 切换到 PostgreSQL。

### Q2: 如何自定义智能体提示词？
修改 `backend/app/llm/autogen_runner.py` 中的系统提示词。

### Q3: 如何添加新的文档格式支持？
在 `backend/app/parsers/text_extractor.py` 中添加新的提取逻辑。

### Q4: 如何部署到生产环境？
使用 Docker Compose 或 Kubernetes 部署，注意配置环境变量和持久化存储。

### Q5: 如何监控系统运行状态？
添加日志收集（如 ELK）、指标监控（如 Prometheus）、错误追踪（如 Sentry）。

---

## 结语

本文档提供了使用 Copilot 等 AI 辅助工具从零开发 AI Needs 项目的完整指南。每个提示词都经过精心设计，确保 AI 能够理解需求并生成高质量的代码。

**开发建议：**
1. 按照阶段顺序开发，先后端后前端
2. 每完成一个模块，立即测试验证
3. 使用 Git 管理代码版本
4. 编写清晰的注释和文档
5. 遵循最佳实践和编码规范

**进一步优化：**
- 添加用户认证和权限管理
- 支持更多文档格式（Excel、PPT 等）
- 添加历史记录管理
- 实现测试用例执行和管理
- 集成 CI/CD 流水线

祝开发顺利！🚀
