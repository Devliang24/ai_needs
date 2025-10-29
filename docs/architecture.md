# AI Needs 架构设计文档

> 深入理解系统架构、设计决策和可扩展性

## 📋 目录

- [整体架构](#整体架构)
- [技术选型理由](#技术选型理由)
- [核心设计决策](#核心设计决策)
- [数据流与交互](#数据流与交互)
- [可扩展性设计](#可扩展性设计)
- [安全性考虑](#安全性考虑)
- [性能优化策略](#性能优化策略)

---

## 🏗️ 整体架构

### 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                          用户浏览器                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  React 18 + TypeScript + Ant Design + Zustand           │  │
│  │  - 文档上传管理                                          │  │
│  │  - 实时WebSocket通信                                     │  │
│  │  - 多阶段流程可视化                                      │  │
│  │  - 人工确认机制                                          │  │
│  │  - 历史记录管理（localStorage）                         │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────┬───────────────────────────┬────────────────────┘
               │ HTTP/REST                 │ WebSocket
               │                           │
┌──────────────▼───────────────────────────▼────────────────────┐
│                    Nginx 反向代理                              │
│  - 静态文件服务                                               │
│  - API路由转发                                                │
│  - WebSocket连接代理                                          │
└──────────────┬───────────────────────────┬────────────────────┘
               │                           │
┌──────────────▼───────────────────────────▼────────────────────┐
│                FastAPI 后端服务                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  API 路由层                                              │ │
│  │  - 文档上传 (/api/uploads)                              │ │
│  │  - 会话管理 (/api/sessions)                             │ │
│  │  - 结果导出 (/api/exports)                              │ │
│  │  - WebSocket端点 (/ws/sessions/{id})                    │ │
│  └──────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  工作流编排层 (Orchestrator)                            │ │
│  │  - SessionWorkflowExecution: 4阶段智能体协作编排        │ │
│  │  - 文档预处理（文本提取/VL识别）                        │ │
│  │  - 阶段结果处理与WebSocket广播                          │ │
│  │  - 人工确认等待机制                                     │ │
│  └──────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  LLM 客户端层                                           │ │
│  │  - AutoGen Runner: 多智能体工作流运行器                 │ │
│  │  - Multimodal Client: 多模态VL模型客户端                │ │
│  │  - Vision Client: 视觉识别客户端（带缓存）              │ │
│  └──────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  数据访问层 (Repository)                                │ │
│  │  - Session Repository: 会话CRUD                         │ │
│  │  - Document Repository: 文档CRUD                        │ │
│  └──────────────────────────────────────────────────────────┘ │
└────────────┬──────────────────────────┬──────────────────────┘
             │                          │
    ┌────────▼────────┐        ┌───────▼────────┐
    │  SQLAlchemy     │        │  Redis缓存      │
    │  (异步ORM)      │        │  - WebSocket事件│
    │  - Session      │        │  - VL识别缓存   │
    │  - Document     │        │  - 确认状态     │
    │  - AgentRun     │        └─────────────────┘
    │  - SessionResult│
    └────────┬────────┘
             │
    ┌────────▼────────┐
    │  数据库         │
    │  - SQLite (开发)│
    │  - PostgreSQL   │
    │    (生产)       │
    └─────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    外部服务                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  通义千问 API (DashScope)                                │  │
│  │  - qwen3-vl-flash: 快速图片识别                         │  │
│  │  - qwen-vl-ocr-latest: PDF专用OCR                       │  │
│  │  - qwen3-next-80b-a3b-instruct: 文本生成                │  │
│  │  - qwen-plus: 通用对话模型                              │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 技术选型理由

### 后端技术选型

#### 1. FastAPI vs Flask/Django

**选择 FastAPI 的理由**:
- ✅ **原生异步支持**: 基于 ASGI，天然支持 async/await，适合 I/O 密集型任务（LLM调用、数据库查询）
- ✅ **高性能**: 性能接近 Node.js 和 Go
- ✅ **自动API文档**: 基于 OpenAPI 自动生成 Swagger UI
- ✅ **类型安全**: Pydantic 提供强大的数据验证和序列化
- ✅ **现代化**: Python 3.10+ 类型提示友好

#### 2. AutoGen vs LangChain

**选择 AutoGen 的理由**:
- ✅ **多智能体协作**: 原生支持多个智能体之间的对话和协作
- ✅ **灵活的工作流**: 可以轻松实现顺序执行、并行执行、循环执行
- ✅ **人工确认机制**: 支持人工干预和确认
- ✅ **OpenAI兼容**: 支持所有OpenAI兼容的LLM API

#### 3. SQLAlchemy vs Tortoise ORM

**选择 SQLAlchemy 的理由**:
- ✅ **成熟稳定**: 业界最成熟的Python ORM
- ✅ **异步支持**: 2.0版本完整支持 async/await
- ✅ **灵活性**: 支持声明式和命令式两种风格
- ✅ **迁移工具**: Alembic 提供完善的数据库迁移支持

#### 4. Redis vs Memcached

**选择 Redis 的理由**:
- ✅ **数据结构丰富**: 支持字符串、列表、哈希表等多种数据结构
- ✅ **持久化**: 支持RDB和AOF两种持久化方式
- ✅ **发布订阅**: 支持WebSocket事件广播
- ✅ **过期策略**: 自动清理过期数据

### 前端技术选型

#### 1. React vs Vue/Angular

**选择 React 的理由**:
- ✅ **生态丰富**: npm包数量最多，社区最活跃
- ✅ **灵活性**: 渐进式架构，可以按需引入功能
- ✅ **性能优异**: 虚拟DOM + Fiber架构
- ✅ **TypeScript支持**: 类型定义完善

#### 2. Zustand vs Redux/MobX

**选择 Zustand 的理由**:
- ✅ **轻量级**: 仅1KB，无需Provider包裹
- ✅ **简单易用**: API简洁，学习成本低
- ✅ **性能优异**: 基于订阅模式，避免不必要的重渲染
- ✅ **TypeScript友好**: 类型推导完善

#### 3. Ant Design vs Material-UI

**选择 Ant Design 的理由**:
- ✅ **企业级**: 专为后台管理系统设计
- ✅ **组件丰富**: 开箱即用的高质量组件
- ✅ **中文文档**: 中文文档完善，适合国内团队
- ✅ **设计规范**: 提供完整的设计语言

#### 4. Socket.IO vs 原生WebSocket

**选择 Socket.IO 的理由**:
- ✅ **断线重连**: 自动重连机制
- ✅ **心跳检测**: 自动检测连接状态
- ✅ **跨浏览器**: 兼容性好，支持降级到轮询
- ✅ **房间机制**: 支持分组广播

---

## 🔑 核心设计决策

### 1. 为什么采用4阶段工作流？

**设计理念**: 模拟真实的需求分析和测试流程

```
需求分析师 → 测试工程师 → 质量评审专家 → 测试补全工程师
```

**优点**:
- ✅ **职责明确**: 每个智能体专注于一个任务
- ✅ **质量保证**: 多轮评审和补全确保测试用例完整性
- ✅ **可追溯性**: 每个阶段的输出都被记录，便于审计
- ✅ **可扩展性**: 可以轻松添加新的阶段（如安全测试、性能测试）

**缺点与权衡**:
- ❌ **时间较长**: 4个阶段串行执行，总耗时较长
- ⚖️ **权衡**: 可以通过并行执行部分阶段优化（如同时生成功能测试和性能测试用例）

---

### 2. 为什么使用Redis缓存确认状态？

**问题**: 如何实现人工确认机制？

**方案对比**:

| 方案 | 优点 | 缺点 |
|------|------|------|
| 数据库轮询 | 持久化 | 性能差，数据库压力大 |
| WebSocket双向通信 | 实时性强 | 客户端断开连接时无法恢复 |
| **Redis缓存** | **性能好，支持过期** | **需要额外服务** |

**最终选择**: Redis缓存
- ✅ **性能优异**: 内存操作，轮询间隔1秒无压力
- ✅ **自动过期**: 设置5分钟TTL，避免内存泄漏
- ✅ **简单可靠**: 无需复杂的消息队列

**实现代码**:
```python
# 工作流等待确认
for _ in range(300):  # 5分钟超时
    await asyncio.sleep(1)
    confirmation = await session_events.get_confirmation(session_id)
    if confirmation and confirmation.get("confirmed"):
        return True
return False  # 超时
```

---

### 3. 为什么前端历史记录存localStorage而不是后端？

**设计理念**: 降低后端复杂度，提升用户体验

**优点**:
- ✅ **离线可用**: 即使后端挂掉，用户仍能查看历史记录
- ✅ **减轻后端压力**: 不需要额外的历史记录表和查询接口
- ✅ **即时加载**: 无需网络请求，秒开
- ✅ **用户隐私**: 数据存储在本地，不上传服务器

**缺点与权衡**:
- ❌ **无法跨设备**: 换设备或清除浏览器数据后丢失
- ⚖️ **权衡**: 对于需求分析场景，用户通常在同一设备上工作，可以接受
- ⚖️ **未来优化**: 可以添加"导出历史记录"功能，让用户手动备份

---

### 4. 流式输出 vs 非流式输出的权衡

**流式输出优点**:
- ✅ **即时反馈**: 用户看到"打字机"效果，感知到系统在工作
- ✅ **降低等待焦虑**: 长时间LLM调用时，用户不会觉得系统卡住

**流式输出缺点**:
- ❌ **前端复杂度**: 需要处理消息追加逻辑，避免重复
- ❌ **后端复杂度**: 需要使用OpenAI流式API，不能直接用AutoGen

**最终方案**: **混合模式**
- **需求分析、测试生成、质量评审、用例补全**: 使用流式输出（用户等待时间长）
- **确认消息、系统消息**: 非流式输出（内容简短）

---

### 5. 为什么支持多模态分析开关？

**问题**: VL模型直接分析图片 vs 先OCR再分析文本

**方案对比**:

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **文本模式**（OCR预处理） | 成本低，速度快 | 丢失视觉信息（颜色、布局、箭头） | 纯文本文档，简单表格 |
| **多模态模式**（直接分析） | 保留完整视觉信息 | 成本高，速度慢 | 流程图、UI原型、架构图 |

**设计决策**: 提供配置开关，让用户根据文档类型选择

```bash
# 文本模式（默认）：成本低，适合纯文本需求文档
ANALYSIS_MULTIMODAL_ENABLED=false

# 多模态模式：保留视觉信息，适合流程图/UI原型
ANALYSIS_MULTIMODAL_ENABLED=true
```

---

## 🔄 数据流与交互

### 完整数据流图

```
1. 用户上传文档
   ├─> POST /api/uploads
   ├─> 计算SHA256 checksum
   ├─> 检查数据库是否存在（去重）
   ├─> 保存到 /tmp/uploads/
   └─> 创建 Document 记录

2. 用户点击"开始分析"
   ├─> POST /api/sessions {document_ids: [...]}
   ├─> 创建 Session 记录
   ├─> 后台启动工作流 workflow.launch(session_id)
   └─> 返回 session_id

3. 前端建立WebSocket连接
   ├─> WebSocket /ws/sessions/{session_id}
   ├─> 后端发送历史事件（Redis缓存）
   └─> 保持连接

4. 工作流执行（后台线程）
   ├─> 阶段1: 需求分析
   │   ├─> 准备文档数据（提取文本/VL识别）
   │   ├─> 调用 AutoGen 需求分析师
   │   ├─> 提取JSON结果
   │   ├─> 存储到 Redis + 广播WebSocket
   │   └─> 等待人工确认（轮询Redis）
   ├─> 阶段2: 测试用例生成
   │   ├─> 调用 AutoGen 测试工程师
   │   ├─> 解析Markdown为JSON
   │   ├─> 存储到 Redis + 广播WebSocket
   │   └─> 等待人工确认
   ├─> 阶段3: 质量评审
   │   ├─> 调用 AutoGen 质量评审专家
   │   ├─> 解析Markdown为结构化数据
   │   ├─> 存储到 Redis + 广播WebSocket
   │   └─> 等待人工确认
   ├─> 阶段4: 用例补全
   │   ├─> 调用 AutoGen 测试补全工程师
   │   ├─> 解析Markdown为JSON
   │   ├─> 存储到 Redis + 广播WebSocket
   │   └─> 等待人工确认
   └─> 完成
       ├─> 合并测试用例（阶段2 + 阶段4）
       ├─> 保存到 SessionResult 表
       ├─> 广播 completed 事件
       └─> 更新 Session 状态为 completed

5. 前端处理WebSocket消息
   ├─> 接收 agent_message
   ├─> 根据 is_streaming 标志追加或创建结果
   ├─> 更新进度条
   ├─> 自动切换到新阶段
   ├─> 显示确认卡片（如果 needs_confirmation=true）
   └─> 保存到 localStorage（如果 completed）

6. 用户确认
   ├─> 点击"确认"按钮
   ├─> 发送 WebSocket 消息 {type: "confirm_agent", confirmed: true}
   ├─> 后端接收并存储到 Redis
   └─> 工作流继续执行下一阶段

7. 导出结果
   ├─> POST /api/sessions/{session_id}/exports/xmind
   ├─> 从 SessionResult 表读取数据
   ├─> 使用 XMind 导出器生成文件
   └─> 返回二进制文件流
```

---

## 🚀 可扩展性设计

### 1. 如何添加新智能体？

**步骤**:

1. **定义智能体配置**:
```python
# config.py
class Settings(BaseSettings):
    # 新智能体配置
    security_agent_model: str = "qwen3-next-80b-a3b-instruct"
    security_agent_api_key: str | None = None
    security_agent_base_url: str | None = None
```

2. **创建智能体Prompt**:
```python
# llm/autogen_runner.py
SECURITY_SYSTEM_MESSAGE = """你是一位安全测试专家。根据需求分析结果，识别潜在的安全风险并生成安全测试用例。"""

def run_security_testing(analysis_payload: dict) -> tuple[dict, str]:
    agent = _agent(SECURITY_SYSTEM_MESSAGE, agent_type="security")
    prompt = f"请分析以下需求的安全风险：{analysis_payload}"
    content = _generate(agent, prompt)
    payload = _extract_json(content)
    return payload, content
```

3. **集成到工作流**:
```python
# orchestrator/workflow.py
class AgentStage(str, enum.Enum):
    # ...
    security_testing = "security_testing"

async def execute(self) -> None:
    # ... 现有阶段 ...
    
    # 新阶段：安全测试
    security_payload, _ = await asyncio.to_thread(
        run_security_testing, analysis_payload
    )
    await self._handle_stage_result(
        AgentStage.security_testing,
        security_payload,
        progress=0.85,
        needs_confirmation=True,
    )
```

4. **更新前端**:
```typescript
// 添加阶段定义
const STAGES = [
  // ...
  { key: 'security_testing', title: '安全测试' },
];

// 添加视图组件
const SecurityTestingView: React.FC<{ payload }> = ({ payload }) => {
  // 渲染安全测试结果
};
```

---

### 2. 如何支持新LLM模型？

**步骤**:

1. **添加模型配置**（如果需要特殊API）:
```python
# config.py
class Settings(BaseSettings):
    llm_provider: Literal["qwen", "openai", "claude"] = "qwen"
    
    claude_api_key: str | None = None
    claude_base_url: str = "https://api.anthropic.com/v1"
```

2. **创建客户端适配器**（如果API不兼容OpenAI）:
```python
# llm/claude_client.py
class ClaudeClient:
    def chat_completion(self, messages: list[dict]) -> str:
        # 调用Claude API
        pass
```

3. **更新AutoGen配置**:
```python
# llm/autogen_runner.py
def _agent(system_message: str, agent_type: str) -> AssistantAgent:
    if settings.llm_provider == "claude":
        # 使用Claude适配器
        config = {
            "model": "claude-3-opus",
            "api_key": settings.claude_api_key,
            "base_url": settings.claude_base_url,
        }
    else:
        # 使用OpenAI兼容配置
        config = settings.get_agent_config(agent_type)
    
    return AssistantAgent(...)
```

---

### 3. 如何支持新文档类型？

**步骤**:

1. **添加解析器**:
```python
# parsers/text_extractor.py
def extract_text(file_path: str) -> str:
    suffix = Path(file_path).suffix.lower()
    
    if suffix == '.md':
        # Markdown解析
        return parse_markdown(file_path)
    elif suffix == '.xlsx':
        # Excel解析
        return parse_excel(file_path)
    # ...
```

2. **更新前端文件类型限制**:
```typescript
// components/FileUploader.tsx
const { getRootProps, getInputProps } = useDropzone({
  accept: {
    'application/pdf': ['.pdf'],
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    'text/markdown': ['.md'],  // 新增
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],  // 新增
  },
});
```

---

## 🔒 安全性考虑

### 1. 文件上传安全

**威胁**:
- 恶意文件上传（病毒、木马）
- 路径遍历攻击
- 文件名注入

**防护措施**:
```python
# api/uploads.py
async def upload_document(file: UploadFile):
    # 1. 文件大小限制
    if file.size > settings.max_file_size:
        raise HTTPException(400, "文件过大")
    
    # 2. 文件类型白名单
    allowed_types = ['.pdf', '.docx', '.png', '.jpg']
    suffix = Path(file.filename).suffix.lower()
    if suffix not in allowed_types:
        raise HTTPException(400, "不支持的文件类型")
    
    # 3. 文件名清理（防止路径遍历）
    safe_filename = secure_filename(file.filename)
    
    # 4. 使用UUID作为存储文件名（防止冲突和猜测）
    storage_path = settings.resolved_upload_dir / f"{uuid4()}_{safe_filename}"
    
    # 5. 病毒扫描（生产环境推荐）
    # scan_file_for_virus(content)
```

---

### 2. API 认证与授权

**当前状态**: 无认证（适合内部部署）

**生产环境建议**:
```python
# 添加JWT认证
from fastapi.security import HTTPBearer

security = HTTPBearer()

@router.post("/sessions")
async def create_session(
    payload: SessionCreateRequest,
    token: str = Depends(security),
):
    # 验证token
    user = verify_jwt_token(token)
    
    # 创建会话
    session = await session_repository.create(
        db,
        document_ids=payload.document_ids,
        created_by=user.id,  # 记录创建者
    )
```

---

### 3. 敏感信息处理

**威胁**: API Key泄露、用户数据泄露

**防护措施**:
```python
# 1. 不记录敏感信息到日志
logger.info(f"LLM调用成功，模型: {model}")  # ✅
# logger.info(f"API Key: {api_key}")  # ❌

# 2. 环境变量存储API Key
# .env
QWEN_API_KEY=sk-xxxxx

# .gitignore
.env

# 3. 数据库字段加密（如果存储用户敏感数据）
from cryptography.fernet import Fernet

encrypted_data = fernet.encrypt(sensitive_data.encode())
```

---

### 4. CSRF 防护

**当前状态**: 无CSRF防护（因为无Cookie认证）

**如果使用Cookie认证，需要添加**:
```python
from fastapi_csrf_protect import CsrfProtect

app.add_middleware(
    CsrfProtect,
    secret_key="your-secret-key",
)
```

---

## ⚡ 性能优化策略

### 1. 数据库查询优化

**问题**: N+1查询问题

**优化**:
```python
# ❌ 错误：N+1查询
sessions = await session_repository.get_all(db)
for session in sessions:
    documents = await document_repository.get_by_session(db, session.id)  # N次查询

# ✅ 正确：使用selectin加载
class Session(Base):
    documents: Mapped[list[Document]] = relationship(
        "Document",
        secondary=session_documents,
        lazy="selectin",  # 一次性加载所有关联文档
    )
```

---

### 2. Redis缓存策略

**缓存内容**:
- VL模型识别结果（相同checksum不重复识别）
- WebSocket事件（支持断线重连）
- 会话状态（避免频繁查询数据库）

**实现**:
```python
# cache/image_cache.py
async def get_or_compute_vl_result(file_path: Path, checksum: str) -> str:
    # 1. 尝试从缓存读取
    cache_key = f"vl_result:{checksum}"
    cached = await redis_client.get(cache_key)
    if cached:
        return cached
    
    # 2. 缓存未命中，调用VL模型
    result = await analyze_with_multimodal(file_path, ...)
    
    # 3. 存储到缓存（24小时过期）
    await redis_client.setex(cache_key, 86400, result)
    
    return result
```

---

### 3. 并发控制

**问题**: 大量并发工作流导致资源耗尽

**优化**:
```python
# orchestrator/workflow.py
import asyncio

# 全局信号量限制并发数
MAX_CONCURRENT_WORKFLOWS = 5
workflow_semaphore = asyncio.Semaphore(MAX_CONCURRENT_WORKFLOWS)

class AnalysisWorkflow:
    async def launch(self, session_id: str) -> None:
        async with workflow_semaphore:  # 限制并发
            await self._run(session_id)
```

---

### 4. 前端性能优化

**优化点**:

1. **Zustand选择器优化**:
```typescript
// ❌ 错误：每次都重新渲染
const { agentResults, selectedStage } = useAppStore();

// ✅ 正确：只订阅需要的数据
const agentResults = useAppStore(state => state.agentResults);
const selectedStage = useAppStore(state => state.selectedStage);
```

2. **React.memo包装纯组件**:
```typescript
const TestCasesView = React.memo<Props>(({ payload }) => {
  // 只有payload变化时才重新渲染
});
```

3. **虚拟滚动（大量测试用例）**:
```typescript
import { FixedSizeList } from 'react-window';

const VirtualizedTestCases: React.FC<{ cases }> = ({ cases }) => (
  <FixedSizeList
    height={600}
    itemCount={cases.length}
    itemSize={50}
  >
    {({ index, style }) => (
      <div style={style}>{cases[index].title}</div>
    )}
  </FixedSizeList>
);
```

---

## 📊 监控与可观测性

### 建议添加的监控指标

1. **业务指标**:
   - 每天上传文档数量
   - 每天创建会话数量
   - 会话成功率（completed / total）
   - 平均每个阶段耗时

2. **技术指标**:
   - LLM API调用次数和失败率
   - WebSocket连接数
   - Redis缓存命中率
   - 数据库查询耗时

3. **日志聚合**:
   - 使用ELK Stack（Elasticsearch + Logstash + Kibana）
   - 或使用云服务（如阿里云日志服务）

---

**本文档持续更新，欢迎提出改进建议！**
