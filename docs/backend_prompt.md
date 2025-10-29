# AI Needs 后端开发完整提示词

> 基于 FastAPI + AutoGen 的多智能体需求分析平台后端开发指南

## 📋 项目概述

**项目名称**: AI Needs - 智能需求分析平台后端  
**核心功能**: 基于多智能体协作的需求文档分析与测试用例自动生成  
**技术架构**: FastAPI异步框架 + AutoGen多智能体 + WebSocket实时通信

---

## 🏗️ 技术栈

### 核心框架
- **Web框架**: FastAPI 0.109.0（异步Web框架）
- **数据库ORM**: SQLAlchemy 2.0.25（支持异步）
- **数据库**: SQLite（开发）/ PostgreSQL（生产）
- **缓存**: Redis 5.0.1
- **WebSocket**: websockets 12.0

### AI与多智能体
- **多智能体框架**: pyautogen 0.2.0
- **LLM SDK**: 
  - openai 1.10.0（OpenAI兼容接口）
  - dashscope 1.24.6+（通义千问官方SDK）
- **支持模型**:
  - qwen3-vl-flash（快速VL模型，图片识别）
  - qwen-vl-ocr-2025-08-28（PDF专用OCR）
  - qwen3-next-80b-a3b-instruct（文本生成）

### 文档处理
- **PDF解析**: PyMuPDF 1.20.2, pdfplumber 0.10.3
- **DOCX解析**: python-docx 1.1.0
- **图片处理**: Pillow 10.2.0

### 结果导出
- **XMind导出**: xmindparser 1.0.9
- **Excel导出**: openpyxl 3.1.2

---

## 📁 项目结构

```
backend/app/
├── api/                 # API路由层
│   ├── uploads.py       # 文档上传API
│   ├── sessions.py      # 会话管理API
│   ├── exports.py       # 结果导出API
│   └── websocket.py     # WebSocket端点
├── cache/               # Redis缓存层
│   ├── redis_client.py  # Redis客户端封装
│   └── session_events.py # 会话事件缓存
├── config.py            # 配置管理（Pydantic Settings）
├── db/                  # 数据库层
│   ├── base.py          # 数据库基础配置
│   ├── session_repository.py      # 会话仓储
│   └── document_repository.py     # 文档仓储
├── exporters/           # 导出功能
│   ├── excel_exporter.py   # Excel导出器
│   └── xmind_exporter.py   # XMind导出器
├── llm/                 # LLM客户端层
│   ├── autogen_runner.py        # AutoGen工作流运行器
│   ├── multimodal_client.py     # 多模态VL客户端
│   └── vision_client_enhanced.py # 视觉识别客户端（增强）
├── main.py              # FastAPI应用入口
├── models/              # ORM数据模型
│   ├── document.py      # 文档模型
│   └── session.py       # 会话/运行/结果模型
├── orchestrator/        # 工作流编排层
│   └── workflow.py      # 多智能体工作流编排
├── parsers/             # 文档解析器
│   └── text_extractor.py # 文本提取器（PDF/DOCX/TXT）
└── websocket/           # WebSocket管理
    └── manager.py       # 连接管理器
```

---

## 🤖 多智能体协作架构

### 工作流4个阶段

1. **requirement_analysis**: 需求分析师分析文档，提取功能模块和业务规则
2. **test_generation**: 测试工程师生成测试用例（Markdown表格格式）
3. **review**: 质量评审专家评审用例完整性
4. **test_completion**: 测试补全工程师补充缺失用例
5. **completed**: 完成并合并所有测试用例

### 智能体 Prompt 设计

#### 1. 需求分析师 (Requirement Analyst)

**System Message**:
```
你是一位资深需求分析师。请仔细阅读需求文档,识别并提取文档中的所有具体功能模块、业务场景和业务规则。
必须基于文档的实际内容进行分析,不要使用泛化的占位符(如'模块1'、'场景1')。
输出JSON格式,包含: modules (name为实际模块名, scenarios为具体场景描述[], rules为具体规则描述[]), risks[]。
```

**输出JSON格式**:
```json
{
  "modules": [
    {
      "name": "用户登录模块",
      "scenarios": [
        {"description": "用户通过手机号+验证码登录系统"}
      ],
      "rules": [
        {"description": "验证码有效期5分钟"}
      ]
    }
  ],
  "risks": [
    {"description": "短信验证码接口可能存在频率限制"}
  ]
}
```

#### 2. 测试工程师 (Test Engineer)

**System Message**:
```
你是一位资深测试工程师。根据需求分析结果,为每个具体功能模块生成详细的测试用例。
请以Markdown格式输出,包含清晰的章节结构和表格。
```

**输出Markdown格式**:
```markdown
## 用户登录模块

| 用例ID | 标题 | 前置条件 | 测试步骤 | 预期结果 | 优先级 |
|--------|------|----------|----------|----------|--------|
| TC-LOGIN-001 | 手机号验证码登录 | 用户未登录 | 1. 输入手机号<br>2. 获取验证码<br>3. 输入验证码<br>4. 点击登录 | 登录成功 | HIGH |
```

#### 3. 质量评审专家 (Quality Reviewer)

**System Message**:
```
你是质量评审专家。仔细评审测试用例的完整性和准确性,以Markdown格式输出评审报告。
```

**输出Markdown格式**:
```markdown
## 评审摘要
测试用例覆盖了主要功能场景，整体质量良好。

## 发现的缺陷
- 缺少密码错误锁定机制的测试用例
- 未覆盖同一账户多设备登录的场景

## 改进建议
- 补充安全相关测试用例
- 增加并发场景测试
```

#### 4. 测试补全工程师 (Test Completion Engineer)

**System Message**:
```
你是一位测试补全工程师。根据质量评审发现的缺口与建议,以Markdown格式补充缺失的测试用例。
```

---

## 🔑 核心配置管理

### 环境变量 (.env.example)

```bash
# 通义千问配置
QWEN_API_KEY=your_api_key_here
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# VL模型配置（图片识别）
VL_ENABLED=true
VL_MODEL=qwen3-vl-flash

# PDF OCR配置
PDF_OCR_ENABLED=true
PDF_OCR_MODEL=qwen-vl-ocr-2025-08-28

# 智能体专用配置（每个智能体可独立配置模型）
ANALYSIS_AGENT_MODEL=qwen3-vl-flash
ANALYSIS_MULTIMODAL_ENABLED=false  # 是否启用多模态分析
TEST_AGENT_MODEL=qwen3-next-80b-a3b-instruct
REVIEW_AGENT_MODEL=qwen3-next-80b-a3b-instruct

# 数据库配置
DATABASE_URL=sqlite+aiosqlite:///./ai_requirement.db
REDIS_URL=redis://redis:6379/0

# 文件上传配置
MAX_FILE_SIZE=10485760
UPLOAD_DIR=/tmp/uploads
LLM_TIMEOUT=120
```

---

## 🗄️ 数据模型设计

### Document 模型
```python
class Document(Base):
    id: str  # UUID
    original_name: str  # 原始文件名
    storage_path: str  # 存储路径
    checksum: str  # SHA256校验和（用于去重）
    size: int  # 文件大小（字节）
    status: DocumentStatus  # uploaded/parsed/expired
    created_at: datetime
```

### Session 模型
```python
class Session(Base):
    id: str  # UUID
    status: SessionStatus  # created/processing/completed/failed
    current_stage: AgentStage  # 当前阶段
    progress: float  # 进度 0.0-1.0
    documents: list[Document]  # 关联文档
    runs: list[AgentRun]  # 执行记录
    results: list[SessionResult]  # 结果快照
    created_at: datetime
```

### AgentRun 模型（审计日志）
```python
class AgentRun(Base):
    id: str
    session_id: str
    stage: AgentStage  # 执行的阶段
    payload: dict  # 执行结果
    started_at: datetime
    finished_at: datetime
    error: str | None  # 错误信息
```

### SessionResult 模型（结果快照）
```python
class SessionResult(Base):
    id: str
    session_id: str
    version: int  # 版本号
    summary: dict  # 需求分析结果
    test_cases: dict  # 合并后的测试用例JSON
    metrics: dict  # 质量指标
    created_at: datetime
```

---

## 🔄 工作流编排核心逻辑

```python
# orchestrator/workflow.py
class SessionWorkflowExecution:
    async def execute(self) -> None:
        # 1. 准备文档数据
        document_data = await self._prepare_documents()
        
        # 2. 阶段1: 需求分析
        analysis_payload, _ = await asyncio.to_thread(
            run_requirement_analysis, document_data, None
        )
        await self._handle_stage_result(
            AgentStage.requirement_analysis,
            analysis_payload,
            progress=0.3,
            needs_confirmation=True
        )
        
        # 3. 阶段2: 测试用例生成
        _, test_content = await asyncio.to_thread(
            run_test_generation, analysis_payload, None
        )
        test_cases_json = _parse_markdown_test_cases(test_content)
        await self._handle_stage_result(
            AgentStage.test_generation,
            test_cases_json,
            progress=0.6,
            needs_confirmation=True
        )
        
        # 4. 阶段3: 质量评审
        _, review_content = await asyncio.to_thread(
            run_quality_review, test_content, None
        )
        review_structured = _parse_review_markdown(review_content)
        await self._handle_stage_result(
            AgentStage.review,
            review_structured,
            progress=0.8,
            needs_confirmation=True
        )
        
        # 5. 阶段4: 用例补全
        _, completion_content = await asyncio.to_thread(
            run_test_completion, test_content, review_content, None
        )
        completion_cases = _parse_markdown_test_cases(completion_content)
        await self._handle_stage_result(
            AgentStage.test_completion,
            completion_cases,
            progress=0.9,
            needs_confirmation=True
        )
        
        # 6. 合并测试用例并保存
        merged = _merge_test_cases(test_cases_json, completion_cases)
        await session_repository.add_session_result(
            self.db_session,
            session_id=self.session_id,
            summary=analysis_payload,
            payload=merged,
            stage=AgentStage.completed,
            progress=1.0,
        )
```

---

## 🌐 API 端点设计

### 1. POST /api/uploads
上传需求文档（支持PDF/DOCX/图片）

**Request**: multipart/form-data
- `file`: 文件（最大10MB）

**Response**:
```json
{
  "document_id": "uuid",
  "original_name": "需求文档.pdf",
  "size": 1234567,
  "checksum": "sha256_hash"
}
```

### 2. POST /api/sessions
创建分析会话并启动工作流

**Request**:
```json
{
  "document_ids": ["doc_uuid_1"],
  "config": {}
}
```

**Response**:
```json
{
  "session_id": "session_uuid",
  "status": "created"
}
```

### 3. WebSocket /ws/sessions/{session_id}
实时推送分析进度和结果

**消息类型**:
- `agent_message`: 智能体输出结果
- `system_message`: 系统提示消息

**agent_message 示例**:
```json
{
  "type": "agent_message",
  "sender": "需求分析师",
  "stage": "requirement_analysis",
  "content": "需求分析完成",
  "payload": {"modules": [...]},
  "progress": 0.3,
  "needs_confirmation": true,
  "timestamp": 1234567890.123
}
```

**客户端发送确认**:
```json
{
  "type": "confirm_agent",
  "stage": "requirement_analysis",
  "confirmed": true,
  "payload": {...}
}
```

### 4. POST /api/sessions/{session_id}/exports/xmind
导出测试用例为XMind格式

**Response**: application/octet-stream（XMind文件）

---

## 🔌 LLM 客户端实现

### AutoGen 智能体创建

```python
# llm/autogen_runner.py
def _agent(system_message: str, agent_type: str) -> AssistantAgent:
    config = settings.get_agent_config(agent_type)
    
    return AssistantAgent(
        name=f"{agent_type}_agent",
        system_message=system_message,
        llm_config={
            "config_list": [config],
            "timeout": settings.llm_timeout,
        },
        human_input_mode="NEVER",
        max_consecutive_auto_reply=1,
        code_execution_config=False,
    )
```

### 流式输出实现

```python
def _generate_streaming(
    system_message: str,
    prompt: str,
    agent_type: str,
    on_chunk: Callable[[str], None] | None = None,
) -> str:
    """流式生成LLM响应"""
    config = settings.get_agent_config(agent_type)
    client = OpenAI(api_key=config["api_key"], base_url=config["base_url"])
    
    stream = client.chat.completions.create(
        model=config["model"],
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ],
        stream=True,
    )
    
    full_content = ""
    for chunk in stream:
        if chunk.choices[0].delta.content:
            full_content += chunk.choices[0].delta.content
            if on_chunk:
                on_chunk(chunk.choices[0].delta.content)
    
    return full_content
```

### 多模态客户端

```python
# llm/multimodal_client.py
async def analyze_with_multimodal(
    file_path: Path,
    api_key: str,
    model: str = "qwen3-vl-flash",
) -> str:
    """使用VL模型直接分析图片/PDF"""
    # 根据文件类型选择模型
    if file_path.suffix.lower() in {'.pdf', '.docx'}:
        model = "qwen-vl-ocr-latest"  # PDF专用OCR
    
    messages = [{
        "role": "user",
        "content": [
            {"image": f"file://{file_path}"},
            {"text": MULTIMODAL_ANALYSIS_PROMPT}
        ]
    }]
    
    response = MultiModalConversation.call(
        model=model,
        messages=messages,
        api_key=api_key,
    )
    
    return response.output.choices[0]["message"]["content"]
```

---

## 📝 关键功能实现

### Markdown解析为JSON

```python
def _parse_markdown_test_cases(markdown_text: str) -> dict:
    """解析Markdown测试用例表格为JSON"""
    modules = []
    module_sections = re.split(r'\n##\s+', markdown_text)
    
    for section in module_sections:
        lines = section.strip().split('\n')
        module_name = lines[0].strip().lstrip('#').strip()
        
        # 查找表格并解析
        cases = []
        for line in lines:
            if line.startswith('|') and not ('用例ID' in line or '---' in line):
                cells = [c.strip() for c in line.split('|') if c.strip()]
                if len(cells) >= 2:
                    cases.append({
                        "id": cells[0],
                        "title": cells[1],
                        "preconditions": cells[2] if len(cells) > 2 else None,
                        "steps": cells[3] if len(cells) > 3 else None,
                        "expected": cells[4] if len(cells) > 4 else None,
                        "priority": cells[5] if len(cells) > 5 else None,
                    })
        
        if cases:
            modules.append({"name": module_name, "cases": cases})
    
    return {"modules": modules}
```

### 测试用例合并（去重）

```python
def _merge_test_cases(base: dict, supplement: dict) -> dict:
    """合并基础和补充测试用例，根据ID去重"""
    merged = {}
    for source in (base, supplement):
        for module in source.get("modules", []):
            name = module.get("name")
            if name not in merged:
                merged[name] = []
            
            existing_ids = {c.get("id") for c in merged[name]}
            for case in module.get("cases", []):
                if case.get("id") not in existing_ids:
                    merged[name].append(case)
    
    return {"modules": [{"name": k, "cases": v} for k, v in merged.items()]}
```

### 人工确认机制（Redis）

```python
# cache/session_events.py
async def set_confirmation(session_id: str, data: dict) -> None:
    """设置用户确认数据"""
    key = f"session:{session_id}:confirmation"
    await redis_client.setex(key, 600, json.dumps(data))

async def get_confirmation(session_id: str) -> dict | None:
    """获取用户确认数据"""
    key = f"session:{session_id}:confirmation"
    data = await redis_client.get(key)
    return json.loads(data) if data else None

# 工作流中等待确认
async def _wait_for_confirmation(stage: AgentStage, timeout: int = 300) -> bool:
    for _ in range(timeout):
        await asyncio.sleep(1)
        confirmation = await session_events.get_confirmation(self.session_id)
        if confirmation and confirmation.get("stage") == stage.value:
            if confirmation.get("confirmed"):
                return True
            elif confirmation.get("rejected"):
                return False
    return False  # 超时
```

---

## ⚡ 性能优化

1. **缓存策略**:
   - Redis缓存VL模型识别结果（相同checksum不重复调用）
   - WebSocket事件缓存支持断线重连

2. **并发控制**:
   - 限制同时运行的工作流数量（使用Semaphore）
   - 异步I/O处理所有数据库和文件操作

3. **流式输出**:
   - 使用OpenAI流式API减少首字节时间
   - WebSocket实时推送chunk提升交互体验

4. **错误处理**:
   - LLM调用失败自动重试（指数退避）
   - 超时机制防止工作流卡死（默认120秒）

---

## 🚀 启动与运行

```bash
# 安装依赖
cd backend
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑.env，配置QWEN_API_KEY

# 运行开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问: http://localhost:8000/docs （Swagger API文档）

---

**本文档基于真实项目代码提取，可直接用于AI辅助开发或团队协作。**
