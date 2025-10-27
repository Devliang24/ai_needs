# 需求分析智能体平台 MVP 方案

---

## 📋 文档信息

| 项目名称 | AI Requirement Analysis Platform |
|---------|----------------------------------|
| 文档版本 | v1.0.0 |
| 创建日期 | 2025-10-19 |
| 最后更新 | 2025-10-19 |
| 文档作者 | AI Team |
| 文档状态 | ✅ 已定稿 |

---

## 📝 版本历史

| 版本号 | 日期 | 修改内容 | 作者 |
|--------|------|----------|------|
| v1.0.0 | 2025-10-19 | 初始版本，完成MVP方案设计 | AI Team |

**版本规范说明：**
- 采用 [语义化版本](https://semver.org/lang/zh-CN/) 规范 (Semantic Versioning)
- 版本格式：`v主版本号.次版本号.修订号`
  - **主版本号**：重大架构变更或不兼容的API修改
  - **次版本号**：向下兼容的功能新增
  - **修订号**：向下兼容的问题修复

---

## 📖 目录

- [1. 项目概述](#1-项目概述)
- [2. 系统架构设计](#2-系统架构设计)
- [3. UI设计方案](#3-ui设计方案)
- [4. 功能模块详细设计](#4-功能模块详细设计)
- [5. 技术实现要点](#5-技术实现要点)
- [6. 开发路线图](#6-开发路线图)
- [7. 部署和运维](#7-部署和运维)
- [8. 附录](#8-附录)

---

## 1. 项目概述

### 1.1 项目背景

在软件开发过程中，需求分析和测试用例编写是耗时且容易出错的环节。本项目旨在开发一个基于**多智能体协作**的需求分析平台，利用AI自动化完成需求文档解析、测试用例生成等工作，提升团队效率。

### 1.2 核心价值

| 痛点 | 解决方案 |
|------|----------|
| 📄 需求文档格式多样（PDF/DOCX/图片） | 集成多种文档解析引擎和OCR技术 |
| 🧠 需求理解依赖人工经验 | 多智能体协作，模拟专业团队分析流程 |
| ⏱️ 测试用例编写耗时长 | AI自动生成，覆盖正常/异常/边界场景 |
| 🔄 人工与AI配合困难 | Human-in-the-loop设计，关键节点人工确认 |
| 📊 输出格式不统一 | 标准化导出XMind/Excel格式 |

### 1.3 技术栈选型

#### 后端技术栈
```
FastAPI          - 现代Python Web框架，支持异步和WebSocket
PyAutoGen        - 微软开源多智能体框架
通义千问/DeepSeek  - 大语言模型API服务
PyMuPDF          - PDF解析
python-docx      - DOCX解析
PaddleOCR        - 图片OCR识别
xmindparser      - XMind文件生成
openpyxl         - Excel文件生成
```

#### 前端技术栈
```
React 18         - UI框架
TypeScript       - 类型安全
Ant Design 5     - 企业级UI组件库
Zustand          - 轻量级状态管理
Socket.io        - WebSocket实时通信
```

---

## 2. 系统架构设计

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────┐
│                  React 前端（单页应用）              │
│  ┌──────────────────────────────────────────┐      │
│  │  对话式界面（类ChatGPT）                  │      │
│  │  - 文件上传                               │      │
│  │  - 实时消息流                             │      │
│  │  - 人工确认交互                           │      │
│  │  - 结果预览与导出                         │      │
│  └──────────────────────────────────────────┘      │
└───────────────────┬─────────────────────────────────┘
                    │ WebSocket + REST API
┌───────────────────▼─────────────────────────────────┐
│              FastAPI 后端服务                        │
│                                                     │
│  ┌──────────────────────────────────────┐          │
│  │  API 路由层                           │          │
│  │  /upload  /analyze  /export  /ws     │          │
│  └──────────────────────────────────────┘          │
│                      ▼                              │
│  ┌──────────────────────────────────────┐          │
│  │  文档解析引擎                         │          │
│  │  PDF → PyMuPDF/pdfplumber            │          │
│  │  DOCX → python-docx                  │          │
│  │  图片 → PaddleOCR                     │          │
│  │  文本 → 直接提取                      │          │
│  └──────────────────────────────────────┘          │
│                      ▼                              │
│  ┌──────────────────────────────────────┐          │
│  │  AutoGen 多智能体编排                 │          │
│  │  ┌────────────────────────────────┐  │          │
│  │  │ 需求分析师 Agent                │  │          │
│  │  │ - 提取功能模块                  │  │          │
│  │  │ - 识别业务规则                  │  │          │
│  │  │ - 梳理用户故事                  │  │          │
│  │  └────────────────────────────────┘  │          │
│  │            ▼                          │          │
│  │  ┌────────────────────────────────┐  │          │
│  │  │ Human Proxy (人工确认节点)      │  │          │
│  │  │ - 需求理解确认                  │  │          │
│  │  │ - 测试用例评审                  │  │          │
│  │  └────────────────────────────────┘  │          │
│  │            ▼                          │          │
│  │  ┌────────────────────────────────┐  │          │
│  │  │ 测试工程师 Agent                │  │          │
│  │  │ - 设计测试场景                  │  │          │
│  │  │ - 生成测试用例                  │  │          │
│  │  │ - 覆盖边界条件                  │  │          │
│  │  └────────────────────────────────┘  │          │
│  │            ▼                          │          │
│  │  ┌────────────────────────────────┐  │          │
│  │  │ 质量评审员 Agent                │  │          │
│  │  │ - 检查用例完整性                │  │          │
│  │  │ - 评估覆盖率                    │  │          │
│  │  │ - 提出改进建议                  │  │          │
│  │  └────────────────────────────────┘  │          │
│  └──────────────────────────────────────┘          │
│                      ▼                              │
│  ┌──────────────────────────────────────┐          │
│  │  结果生成模块                         │          │
│  │  XMind导出 → xmindparser             │          │
│  │  Excel导出 → openpyxl                │          │
│  └──────────────────────────────────────┘          │
│                      ▼                              │
│  ┌──────────────────────────────────────┐          │
│  │  持久化存储层                         │          │
│  │  PostgreSQL → 会话/文档数据           │          │
│  │  Redis → 运行态与TTL缓存             │          │
│  └──────────────────────────────────────┘          │
└─────────────────────────────────────────────────────┘
                      ▲
                      │ API 调用
┌─────────────────────▼─────────────────────────────┐
│    通义千问 / DeepSeek API（兼容OpenAI格式）       │
└───────────────────────────────────────────────────┘
```

### 2.2 智能体角色设计

#### Agent 1: 需求分析师 (Requirement Analyzer)
**职责：**
- 阅读并理解需求文档内容
- 提取核心功能模块和业务规则
- 梳理用户故事和使用场景
- 识别隐含需求和潜在风险

**输出示例：**
```
📦 核心功能模块（5个）
  1. 👤 用户注册登录
  2. 🛍️ 商品浏览搜索
  3. 🛒 购物车管理
  4. 💳 订单支付
  5. 🚚 物流跟踪

📋 业务场景（15个）
📌 关键业务规则（8条）
```

#### Agent 2: 测试工程师 (Test Engineer)
**职责：**
- 基于需求分析结果设计测试场景
- 生成详细的测试用例（包含前置条件、操作步骤、预期结果）
- 覆盖正常流程、异常处理、边界条件
- 分配测试优先级（P0/P1/P2）

**输出示例：**
```
TC001: 有效手机号注册成功
├ 前置条件: 手机号未被注册
├ 操作步骤:
│   1. 输入11位有效手机号
│   2. 点击"获取验证码"
│   3. 输入6位验证码
│   4. 点击"注册"
├ 预期结果: 注册成功，跳转至首页
└ 优先级: P0
```

#### Agent 3: 质量评审员 (Quality Reviewer)
**职责：**
- 检查测试用例的完整性和合理性
- 评估测试覆盖率
- 识别遗漏的测试场景
- 提出改进建议

**输出示例：**
```
✅ 质量评估结果
- 用例总数: 47条
- 场景覆盖: 126个
- 覆盖率: 95%
- 优先级分布: P0(12) P1(25) P2(10)

💡 改进建议:
1. 建议补充"忘记密码"场景的性能测试
2. "支付"模块建议增加并发测试用例
```

#### Human Proxy: 人工确认节点
**触发时机：**
1. 需求分析完成后 → 确认需求理解是否准确
2. 测试用例生成完成后 → 确认用例是否需要调整

**交互方式：**
- 前端弹出确认卡片
- 用户选择："✓ 准确，继续" 或 "✏️ 需要补充..."
- 补充信息回传给Agent继续工作

---

## 3. UI设计方案

### 3.1 设计理念

**极简对话式设计（类ChatGPT）**
- ✅ 零学习成本，符合用户聊天习惯
- ✅ 单一时间线，流程清晰可追溯
- ✅ 所有交互在一个页面完成
- ✅ 移动端友好，自适应布局

### 3.2 页面布局

```
┌─────────────────────────────────────────────────────────────┐
│  🤖 需求分析Agent    [历史▼] [设置]  Model: 通义千问 🟢      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                    对话区域（可滚动）                         │
│                                                             │
│  - Agent消息（左对齐，灰色气泡）                             │
│  - 用户消息（右对齐，蓝色气泡）                              │
│  - 系统消息（居中，卡片样式）                                │
│  - 确认节点（高亮卡片，带操作按钮）                          │
│                                                             │
│                                                             │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  📎 [上传文件] 输入需求文本或上传文档...       [发送]        │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 完整交互流程

#### 步骤1: 初始欢迎界面
```
┌─────────────────────────────────────────────────────────────┐
│  🤖 需求分析Agent    [历史▼] [设置]  Model: 通义千问 🟢      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│              🤖 你好！我是需求分析助手                        │
│                                                             │
│              请上传需求文档，我将为你：                       │
│              ✓ 自动提取核心需求                              │
│              ✓ 生成完整测试用例                              │
│              ✓ 导出XMind/Excel格式                          │
│                                                             │
│              支持格式: PDF | DOCX | 图片 | 纯文本            │
│                                                             │
│              💡 提示：也可以直接粘贴需求文本                  │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  📎 [上传文件] 或输入需求文本...          [发送]             │
└─────────────────────────────────────────────────────────────┘
```

#### 步骤2: 用户上传文件
```
                                                      ┌──────┐
                                            👤 你     │      │
                              ┌─────────────────────┐│      │
                              │ 📄 电商平台需求.pdf  ││      │
                              │ 📄 原型图.png        ││      │
                              │ 2个文件, 3.8MB       ││      │
                              └─────────────────────┘│      │
                                                      └──────┘

┌──────┐
│ 🤖 系统
│ ┌─────────────────────────────────────────────────────┐
│ │ ✓ 已接收2个文件                                      │
│ │ 📄 电商平台需求.pdf - 解析中...                       │
│ │ ━━━━━━━━━━━━━━━━━━━━ 100%                          │
│ │ 提取文本: 1250字 | 图片: 3张 | 表格: 2个             │
│ │                                                      │
│ │ 📄 原型图.png - OCR识别中...                         │
│ │ ━━━━━━━━━━━━━━━━━━━━ 100%                          │
│ │ 识别字段: 85个                                        │
│ └─────────────────────────────────────────────────────┘
└──────┘
```

#### 步骤3: Agent分析过程
```
┌──────┐
│ 🤖 需求分析师                          10:23
│ ┌─────────────────────────────────────────────────────┐
│ │ 我已完成需求分析，识别到以下内容：                    │
│ │                                                      │
│ │ 📦 核心功能模块（5个）                                │
│ │  1. 👤 用户注册登录                                  │
│ │  2. 🛍️ 商品浏览搜索                                  │
│ │  3. 🛒 购物车管理                                    │
│ │  4. 💳 订单支付                                      │
│ │  5. 🚚 物流跟踪                                      │
│ │                                                      │
│ │ 📋 业务场景（15个）                                   │
│ │ 📌 关键业务规则（8条）                                │
│ │                                                      │
│ │ [查看详细分析报告]                                    │
│ └─────────────────────────────────────────────────────┘
└──────┘

┌──────────────────────────────────────────────────────┐
│ ⏸️ 请确认                                              │
│ 以上需求理解是否准确？                                  │
│ [✓ 准确，继续] [✏️ 需要补充...]                        │
└──────────────────────────────────────────────────────┘

                                                      ┌──────┐
                                            👤 你     │      │
                              ┌─────────────────────┐│      │
                              │ ✓ 准确，继续         ││      │
                              └─────────────────────┘│      │
                                                      └──────┘

┌──────┐
│ 🤖 测试工程师                          10:24
│ ┌─────────────────────────────────────────────────────┐
│ │ 开始设计测试用例...                                   │
│ │                                                      │
│ │ ✓ 用户注册模块 - 已生成12条用例                       │
│ │ ✓ 商品浏览模块 - 已生成15条用例                       │
│ │ 🔄 购物车模块 - 正在生成...                           │
│ │                                                      │
│ │ 当前进度: 27/47 用例                                  │
│ └─────────────────────────────────────────────────────┘
└──────┘
```

#### 步骤4: 完成并导出
```
┌──────┐
│ 🤖 质量评审员                          10:26
│ ┌─────────────────────────────────────────────────────┐
│ │ ✅ 测试用例评审完成                                   │
│ │                                                      │
│ │ 📊 质量指标：                                         │
│ │  • 用例总数: 47条                                    │
│ │  • 场景覆盖: 126个                                   │
│ │  • 覆盖率: 95%                                       │
│ │  • 优先级分布: P0(12) P1(25) P2(10)                 │
│ │                                                      │
│ │ ✅ 建议：测试用例设计合理，可以使用                   │
│ └─────────────────────────────────────────────────────┘
└──────┘

┌──────┐
│ 🤖 系统
│ ┌─────────────────────────────────────────────────────┐
│ │ 📋 测试用例已生成完成！                               │
│ │                                                      │
│ │ [📜 预览全部用例]  [✏️ 在线编辑]                      │
│ │                                                      │
│ │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━     │
│ │                                                      │
│ │ 📥 选择导出格式：                                     │
│ │                                                      │
│ │ ┌────────────────┐  ┌────────────────┐             │
│ │ │ 🌳 XMind        │  │ 📊 Excel        │             │
│ │ │ 思维导图格式     │  │ 表格格式         │             │
│ │ │ [⬇️ 下载]       │  │ [⬇️ 下载]       │             │
│ │ └────────────────┘  └────────────────┘             │
│ │                                                      │
│ │ [💾 保存到历史记录]  [🔄 重新分析]                    │
│ └─────────────────────────────────────────────────────┘
└──────┘
```

### 3.4 响应式适配

**PC端（>1024px）：**
- 对话区域宽度：800px（居中显示）
- 消息气泡最大宽度：600px

**平板端（768px-1024px）：**
- 对话区域宽度：100%（带左右padding）
- 消息气泡最大宽度：80%

**移动端（<768px）：**
- 全屏显示
- 顶栏可折叠
- 消息气泡宽度：90%

---

## 4. 功能模块详细设计

### 4.1 文档解析模块

#### 支持的文件格式

| 格式 | 解析库 | 功能 |
|------|--------|------|
| PDF | PyMuPDF / pdfplumber | 文本提取、表格识别、图片提取 |
| DOCX | python-docx | 文本提取、表格提取、样式保留 |
| 图片 | PaddleOCR | 文字识别（支持中英文） |
| TXT | 标准库 | 直接读取 |

#### 解析流程

```python
async def parse_document(file: UploadFile) -> ParsedContent:
    """
    文档解析统一接口
    """
    file_ext = file.filename.split('.')[-1].lower()

    if file_ext == 'pdf':
        return await parse_pdf(file)
    elif file_ext == 'docx':
        return await parse_docx(file)
    elif file_ext in ['png', 'jpg', 'jpeg']:
        return await parse_image_ocr(file)
    elif file_ext == 'txt':
        return await parse_text(file)
    else:
        raise ValueError(f"不支持的文件格式: {file_ext}")
```

#### 输出数据结构

```python
from pydantic import BaseModel
from typing import List, Optional

class ParsedContent(BaseModel):
    text: str                    # 提取的文本内容
    images: List[str] = []       # 图片Base64列表
    tables: List[dict] = []      # 表格数据
    metadata: dict = {}          # 元信息（页数、作者等）
    word_count: int              # 字数统计
```

### 4.2 AutoGen 多智能体编排

#### Agent 配置示例

```python
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager

# LLM 配置（兼容通义千问）
config_list = [{
    "model": "qwen-plus",
    "api_key": os.getenv("QWEN_API_KEY"),
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"
}]

llm_config = {
    "config_list": config_list,
    "temperature": 0.7,
    "max_tokens": 2000
}

# 需求分析师 Agent
requirement_analyzer = AssistantAgent(
    name="需求分析师",
    system_message="""
    你是一位资深需求分析师，擅长：
    1. 从需求文档中提取核心功能模块
    2. 识别业务规则和约束条件
    3. 梳理用户故事和使用场景
    4. 发现隐含需求和潜在风险

    请以结构化的方式输出分析结果。
    """,
    llm_config=llm_config
)

# 测试工程师 Agent
test_engineer = AssistantAgent(
    name="测试工程师",
    system_message="""
    你是一位资深测试工程师，擅长：
    1. 基于需求设计测试场景
    2. 编写详细的测试用例（包含前置条件、操作步骤、预期结果）
    3. 覆盖正常流程、异常处理、边界条件
    4. 分配测试优先级（P0/P1/P2）

    测试用例格式：
    TC{编号}: {用例标题}
    ├ 前置条件: ...
    ├ 操作步骤: 1. ... 2. ... 3. ...
    ├ 预期结果: ...
    └ 优先级: P0/P1/P2
    """,
    llm_config=llm_config
)

# 质量评审员 Agent
quality_reviewer = AssistantAgent(
    name="质量评审员",
    system_message="""
    你是一位质量评审专家，负责：
    1. 检查测试用例的完整性和合理性
    2. 评估测试覆盖率
    3. 识别遗漏的测试场景
    4. 提出改进建议

    输出格式：
    - 用例总数
    - 覆盖率评估
    - 遗漏场景（如有）
    - 改进建议
    """,
    llm_config=llm_config
)

# 人工确认节点
human_proxy = UserProxyAgent(
    name="产品经理",
    human_input_mode="ALWAYS",  # 关键步骤需要确认
    max_consecutive_auto_reply=0,
    code_execution_config=False
)

# 编排 GroupChat
groupchat = GroupChat(
    agents=[requirement_analyzer, human_proxy, test_engineer, human_proxy, quality_reviewer],
    messages=[],
    max_round=10
)

manager = GroupChatManager(groupchat=groupchat, llm_config=llm_config)
```

#### 工作流程

```
1. requirement_analyzer 分析需求
        ↓
2. human_proxy 人工确认需求理解
        ↓
3. test_engineer 生成测试用例
        ↓
4. human_proxy 人工确认用例质量
        ↓
5. quality_reviewer 质量评审
        ↓
6. 生成最终报告
```

### 4.3 实时流式输出（WebSocket）

#### WebSocket 消息格式

```python
from pydantic import BaseModel
from typing import Literal

class WSMessage(BaseModel):
    type: Literal["agent_message", "system_message", "confirmation_request", "progress_update"]
    sender: str                # Agent名称或"system"
    content: str               # 消息内容
    timestamp: float           # 时间戳
    metadata: dict = {}        # 额外信息
```

#### 后端推送示例

```python
from fastapi import WebSocket

async def stream_agent_chat(websocket: WebSocket, chat_result):
    """
    将Agent对话实时推送到前端
    """
    for message in chat_result.chat_history:
        await websocket.send_json({
            "type": "agent_message",
            "sender": message["name"],
            "content": message["content"],
            "timestamp": time.time()
        })

        # 模拟流式输出效果
        await asyncio.sleep(0.5)
```

#### 前端接收示例

```typescript
const socket = io('ws://localhost:8000');

socket.on('message', (data: WSMessage) => {
  setMessages(prev => [...prev, data]);

  // 自动滚动到底部
  scrollToBottom();
});
```

### 4.4 结果导出模块

#### XMind 导出

```python
import xmind
from xmind.core.topic import TopicElement

def export_to_xmind(test_cases: List[TestCase], output_path: str):
    """
    将测试用例导出为XMind思维导图
    """
    workbook = xmind.load("template.xmind")
    sheet = workbook.getPrimarySheet()
    root_topic = sheet.getRootTopic()
    root_topic.setTitle("测试用例汇总")

    for module in test_cases:
        # 一级分支：功能模块
        module_topic = root_topic.addSubTopic()
        module_topic.setTitle(f"{module.name} ({len(module.cases)}条)")

        for scenario in module.scenarios:
            # 二级分支：测试场景
            scenario_topic = module_topic.addSubTopic()
            scenario_topic.setTitle(scenario.name)

            for case in scenario.cases:
                # 三级分支：具体用例
                case_topic = scenario_topic.addSubTopic()
                case_topic.setTitle(f"{case.id}: {case.title}")

                # 添加备注（详细信息）
                case_topic.setPlainNotes(
                    f"前置条件: {case.precondition}\n"
                    f"操作步骤: {case.steps}\n"
                    f"预期结果: {case.expected}\n"
                    f"优先级: {case.priority}"
                )

    xmind.save(workbook, output_path)
    return output_path
```

#### Excel 导出

```python
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill

def export_to_excel(test_cases: List[TestCase], output_path: str):
    """
    将测试用例导出为Excel表格
    """
    wb = Workbook()

    # Sheet1: 测试用例汇总
    ws1 = wb.active
    ws1.title = "测试用例汇总"

    # 表头
    headers = ["用例ID", "模块", "场景", "用例标题", "前置条件", "操作步骤", "预期结果", "优先级"]
    ws1.append(headers)

    # 设置表头样式
    for cell in ws1[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")

    # 填充数据
    for module in test_cases:
        for scenario in module.scenarios:
            for case in scenario.cases:
                ws1.append([
                    case.id,
                    module.name,
                    scenario.name,
                    case.title,
                    case.precondition,
                    case.steps,
                    case.expected,
                    case.priority
                ])

    # Sheet2: 需求追溯矩阵
    ws2 = wb.create_sheet("需求追溯矩阵")
    ws2.append(["需求ID", "需求描述", "关联测试用例", "覆盖状态"])

    for requirement in requirements:
        related_cases = ", ".join([c.id for c in requirement.test_cases])
        coverage = "✓" if len(requirement.test_cases) > 0 else "✗"
        ws2.append([requirement.id, requirement.description, related_cases, coverage])

    wb.save(output_path)
    return output_path
```

---

## 5. 技术实现要点

### 5.1 项目目录结构

```
ai-requirement-platform/
├── backend/                          # FastAPI后端
│   ├── app/
│   │   ├── main.py                  # 应用入口
│   │   ├── config.py                # 配置管理
│   │   ├── api/                     # API路由
│   │   │   ├── __init__.py
│   │   │   ├── upload.py            # 文件上传接口
│   │   │   ├── analyze.py           # 分析接口
│   │   │   ├── export.py            # 导出接口
│   │   │   └── websocket.py         # WebSocket接口
│   │   ├── agents/                  # AutoGen智能体
│   │   │   ├── __init__.py
│   │   │   ├── requirement_analyzer.py
│   │   │   ├── test_engineer.py
│   │   │   ├── quality_reviewer.py
│   │   │   └── orchestrator.py      # 编排逻辑
│   │   ├── db/                      # 数据访问与会话存储
│   │   │   ├── __init__.py
│   │   │   ├── base.py              # SQLAlchemy引擎/SessionLocal
│   │   │   ├── document_repository.py
│   │   │   └── session_repository.py
│   │   ├── parsers/                 # 文档解析器
│   │   │   ├── __init__.py
│   │   │   ├── pdf_parser.py
│   │   │   ├── docx_parser.py
│   │   │   ├── image_parser.py
│   │   │   └── text_parser.py
│   │   ├── exporters/               # 导出模块
│   │   │   ├── __init__.py
│   │   │   ├── xmind_exporter.py
│   │   │   └── excel_exporter.py
│   │   ├── models/                  # 数据模型
│   │   │   ├── __init__.py
│   │   │   ├── document.py
│   │   │   ├── session.py
│   │   │   ├── test_case.py
│   │   │   └── message.py
│   │   └── utils/                   # 工具函数
│   │       ├── __init__.py
│   │       └── logger.py
│   ├── tests/                       # 单元测试
│   │   ├── test_parsers.py
│   │   ├── test_agents.py
│   │   └── test_exporters.py
│   ├── requirements.txt             # Python依赖
│   ├── .env.example                 # 环境变量示例
│   └── Dockerfile
│
├── frontend/                         # React前端
│   ├── src/
│   │   ├── App.tsx                  # 应用入口
│   │   ├── components/              # UI组件
│   │   │   ├── ChatContainer.tsx    # 对话容器
│   │   │   ├── MessageBubble.tsx    # 消息气泡
│   │   │   ├── InputBar.tsx         # 输入栏
│   │   │   ├── FileUploader.tsx     # 文件上传
│   │   │   ├── ConfirmationCard.tsx # 确认卡片
│   │   │   └── ExportPanel.tsx      # 导出面板
│   │   ├── pages/
│   │   │   └── Home.tsx             # 主页面
│   │   ├── stores/                  # Zustand状态管理
│   │   │   └── chatStore.ts
│   │   ├── services/                # API服务
│   │   │   ├── api.ts
│   │   │   └── websocket.ts
│   │   ├── types/                   # TypeScript类型
│   │   │   ├── message.ts
│   │   │   └── testcase.ts
│   │   └── styles/                  # 样式文件
│   │       └── global.css
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── docker-compose.yml                # Docker编排
├── README.md                         # 项目说明
├── .gitignore
└── docs/                             # 文档
    ├── API.md                        # API文档
    ├── DEPLOYMENT.md                 # 部署文档
    └── DEVELOPMENT.md                # 开发文档
```

### 5.2 核心依赖清单

#### 后端 (requirements.txt)

```txt
# Web框架
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.9
websockets==12.0

# 多智能体框架
pyautogen==0.2.0

# LLM SDK
openai==1.10.0
dashscope==1.14.0

# 数据存储
SQLAlchemy[asyncio]==2.0.25
alembic==1.13.1
asyncpg==0.29.0
redis==5.0.1

# 文档解析
PyMuPDF==1.23.8
pdfplumber==0.10.3
python-docx==1.1.0
Pillow==10.2.0
paddleocr==2.7.0

# 结果导出
xmindparser==1.0.9
openpyxl==3.1.2

# 工具库
pydantic==2.5.0
python-dotenv==1.0.0
```

#### 前端 (package.json)

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "typescript": "^5.3.0",
    "antd": "^5.12.0",
    "zustand": "^4.4.7",
    "socket.io-client": "^4.6.1",
    "axios": "^1.6.0",
    "react-dropzone": "^14.2.3",
    "react-markdown": "^9.0.1"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.0",
    "vite": "^5.0.0"
  }
}
```

### 5.3 API 接口设计

#### REST API

| 方法 | 路径 | 说明 | 请求体 | 响应体 |
|------|------|------|--------|--------|
| POST | `/api/uploads` | 上传文件并登记文档 | FormData | `{document_id, original_name, checksum}` |
| POST | `/api/sessions` | 创建分析会话 | `{document_ids, config}` | `{session_id, status, expires_at}` |
| GET | `/api/sessions` | 分页查询历史会话 | `?page=1&page_size=20&status=completed` | `{items, pagination}` |
| GET | `/api/sessions/{session_id}` | 查询会话状态与进度 | - | `{status, progress, current_stage, expires_at}` |
| POST | `/api/sessions/{session_id}/confirm` | 提交人工确认结果 | `{stage, decision, comment}` | `{status, next_stage}` |
| GET | `/api/sessions/{session_id}/results` | 获取分析结果快照 | - | `{analysis, test_cases, statistics, version}` |
| POST | `/api/sessions/{session_id}/exports/xmind` | 导出XMind | `{result_version}` | File Download |
| POST | `/api/sessions/{session_id}/exports/excel` | 导出Excel | `{result_version}` | File Download |
| DELETE | `/api/sessions/{session_id}` | 手动归档并触发清理 | - | `{status: 'archived'}` |

#### WebSocket

**连接地址**: `ws://localhost:8000/ws/{session_id}`

**消息类型**:
```typescript
// 客户端 → 服务端
{
  "type": "user_confirmation",
  "content": "准确，继续",
  "timestamp": 1234567890
}

// 服务端 → 客户端
{
  "type": "agent_message",
  "sender": "需求分析师",
  "content": "我已完成需求分析...",
  "timestamp": 1234567890
}
```

### 5.4 状态管理（Zustand）

```typescript
// stores/chatStore.ts
import create from 'zustand';

interface Message {
  id: string;
  sender: string;
  type: 'text' | 'file' | 'confirmation' | 'result';
  content: any;
  timestamp: number;
}

interface ChatState {
  // 状态
  messages: Message[];
  isAnalyzing: boolean;
  sessionId: string | null;

  // 操作
  addMessage: (message: Message) => void;
  clearMessages: () => void;
  setAnalyzing: (status: boolean) => void;
  setSessionId: (id: string) => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  isAnalyzing: false,
  sessionId: null,

  addMessage: (message) => set((state) => ({
    messages: [...state.messages, message]
  })),

  clearMessages: () => set({ messages: [] }),

  setAnalyzing: (status) => set({ isAnalyzing: status }),

  setSessionId: (id) => set({ sessionId: id })
}));
```

### 5.5 会话存储与生命周期

#### 持久化层选型
- PostgreSQL：存储会话、文档、Agent运行记录与最终结果，保证多用户并发与可追溯性。
- Redis：缓存实时进度、WebSocket会话、短期确认令牌（TTL 5 分钟），降低数据库写入压力。

#### 核心数据模型
| 表名 | 关键字段 | 说明 |
|------|----------|------|
| `documents` | `id`, `original_name`, `storage_path`, `checksum`, `size`, `status`, `expires_at` | 记录上传文件与在对象存储/本地磁盘中的位置，`status` 标识 `uploaded/parsed/expired`。|
| `sessions` | `id`, `status`, `config`, `created_by`, `created_at`, `expires_at`, `last_activity_at` | 每次分析流程的主记录，`status` 取值 `created/processing/awaiting_confirmation/awaiting_review/completed/archived/expired`。|
| `agent_runs` | `id`, `session_id`, `stage`, `payload`, `started_at`, `finished_at`, `error` | 记录每个 Agent 的执行快照，`payload` 为 JSON，便于排查问题与重放。|
| `session_results` | `id`, `session_id`, `version`, `summary`, `test_cases`, `metrics`, `created_at` | 保存结构化分析结果，`test_cases` 列为 JSONB，用于导出或历史对比。|

#### 生命周期流程
1. **上传阶段**：`POST /api/uploads` 写入 `documents` 表，生成 `document_id`，文件落地到 `UPLOAD_DIR/{checksum}` 并记录 `expires_at = now + SESSION_TTL`。
2. **建会话**：`POST /api/sessions` 创建 `sessions` 记录，默认状态 `created`，同时在 Redis 写入 `{session_id}:status`、`progress` 等键。
3. **解析与编排**：后端工作流消费待处理队列，将状态推进为 `processing`；阶段性进度（文档解析完成、Agent 输出等）写入 `agent_runs` 与 Redis，以支持断点续跑与实时推送。
4. **人工确认**：当需要 Human-in-the-loop 时，状态切换为 `awaiting_confirmation`，前端调用确认 API 后记录决策（审批人、意见、时间），并推进到下一阶段。
5. **结果固化**：Agent 完成后写入 `session_results`（版本号自增），会话状态标记为 `completed`，同时刷新 `last_activity_at`。
6. **归档与清理**：定时任务（每 1 小时）扫描 `expires_at` 或 `archived` 会话，删除本地文件、清理 Redis key，将会话状态置为 `archived` 或 `expired`。

#### 并发与幂等
- 所有状态迁移通过仓储层封装的 `transition(session_id, from_status, to_status)` 方法完成，保证状态机合法性。
- `POST /api/uploads` 按 `checksum` 去重，重复上传直接复用历史记录，避免大文件占用。
- Redis 进度键采用 `SETEX` 保持 2 倍 `SESSION_TTL`，保障 WebSocket 断线重连后仍能恢复上下文。

#### 数据保留策略
- 默认 `SESSION_TTL` 为 72 小时，可通过环境变量调整，合规场景可配置强制立即归档。
- 导出文件均为即时生成并通过一次性签名 URL 下载，不在服务器上持久化。
- 后端日志仅记录 `session_id` 与脱敏后的文件名/决策信息，避免原始文档泄漏。

---

## 6. 开发路线图

### 6.1 开发阶段划分

#### Phase 1: 基础框架搭建 (Week 1-2)

**后端任务：**
- [ ] FastAPI项目初始化
- [ ] 基础路由结构搭建
- [ ] 环境配置管理（.env）
- [ ] 日志系统集成
- [ ] WebSocket基础实现
- [ ] PostgreSQL/Redis连接封装与健康检查

**前端任务：**
- [ ] React + TypeScript项目初始化
- [ ] Ant Design集成
- [ ] 对话式界面基础布局
- [ ] Zustand状态管理搭建
- [ ] WebSocket客户端连接

**交付物：**
- ✅ 前后端可以通过WebSocket双向通信
- ✅ 基础UI界面可正常显示

---

#### Phase 2: 文档解析模块 (Week 2-3)

**任务清单：**
- [ ] PDF解析实现（PyMuPDF）
- [ ] DOCX解析实现（python-docx）
- [ ] 图片OCR实现（PaddleOCR）
- [ ] 纯文本解析
- [ ] 文件上传接口（支持多文件）
- [ ] 前端拖拽上传组件
- [ ] 解析进度实时反馈

**交付物：**
- ✅ 支持上传PDF/DOCX/图片/文本
- ✅ 能正确提取文本内容
- ✅ 前端显示解析结果预览

---

#### Phase 3: 多智能体核心 (Week 3-5)

**任务清单：**
- [ ] 通义千问API集成与测试
- [ ] AutoGen基础配置
- [ ] 需求分析师Agent实现
- [ ] 测试工程师Agent实现
- [ ] 质量评审员Agent实现
- [ ] GroupChat编排逻辑
- [ ] Human-in-the-loop交互实现
- [ ] 会话状态机与持久化流程跑通
- [ ] 实时流式输出到前端
- [ ] 前端确认卡片组件

**交付物：**
- ✅ 三个Agent能协作完成需求分析
- ✅ 人工确认节点能正常交互
- ✅ 前端实时显示Agent对话过程

---

#### Phase 4: 结果生成与导出 (Week 5-6)

**任务清单：**
- [ ] 测试用例数据模型设计
- [ ] XMind导出逻辑实现
- [ ] Excel导出逻辑实现
- [ ] 前端结果预览组件
- [ ] 树形列表视图
- [ ] 在线编辑功能（可选）
- [ ] 下载接口实现

**交付物：**
- ✅ 能生成XMind思维导图文件
- ✅ 能生成Excel表格文件
- ✅ 前端能预览和下载结果

---

#### Phase 5: 历史记录与优化 (Week 6-7)

**任务清单：**
- [ ] LocalStorage历史记录实现
- [ ] 历史记录列表UI
- [ ] 重新加载历史项目
- [ ] 错误处理优化
- [ ] 性能优化（大文件处理）
- [ ] UI/UX细节优化
- [ ] 移动端适配测试

**交付物：**
- ✅ 支持保存和查看历史记录
- ✅ 错误提示友好清晰
- ✅ 移动端体验良好

---

#### Phase 6: 测试与文档 (Week 7)

**任务清单：**
- [ ] 单元测试编写
- [ ] 集成测试
- [ ] API文档编写
- [ ] 用户使用文档
- [ ] 部署文档
- [ ] Docker镜像构建

**交付物：**
- ✅ 测试覆盖率 > 80%
- ✅ 完整的部署文档
- ✅ Docker一键启动

---

### 6.2 里程碑

| 里程碑 | 时间点 | 验收标准 |
|--------|--------|----------|
| M1: 框架完成 | Week 2 | 前后端通信正常，基础UI可用 |
| M2: 文档解析完成 | Week 3 | 能上传并解析所有格式文件 |
| M3: Agent核心完成 | Week 5 | 能完整走通分析流程 |
| M4: 导出功能完成 | Week 6 | 能导出XMind和Excel |
| M5: MVP交付 | Week 7 | 全功能可用，文档齐全 |

---

## 7. 部署和运维

### 7.1 环境配置

#### 环境变量配置 (.env)

```bash
# LLM API配置
LLM_PROVIDER=qwen              # qwen | deepseek | openai
QWEN_API_KEY=your_api_key_here
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-plus

# 应用配置
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=false

# 数据库配置
DATABASE_URL=postgresql+asyncpg://ai_requirement:change_me@db:5432/ai_requirement
REDIS_URL=redis://redis:6379/0
SESSION_TTL_HOURS=72
SESSION_CLEANUP_INTERVAL=3600

# 文件上传配置
MAX_FILE_SIZE=10485760         # 10MB
UPLOAD_DIR=/tmp/uploads

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=/var/log/app.log
```

### 7.2 Docker部署

#### docker-compose.yml

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    container_name: ai_requirement_backend
    ports:
      - "8000:8000"
    environment:
      - QWEN_API_KEY=${QWEN_API_KEY}
      - QWEN_MODEL=${QWEN_MODEL}
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SESSION_TTL_HOURS=${SESSION_TTL_HOURS}
    volumes:
      - ./backend:/app
      - uploads:/tmp/uploads
    depends_on:
      - db
      - redis
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build: ./frontend
    container_name: ai_requirement_frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
    environment:
      - VITE_API_URL=http://localhost:8000
    command: npm run dev -- --host

  db:
    image: postgres:15-alpine
    container_name: ai_requirement_db
    environment:
      - POSTGRES_DB=ai_requirement
      - POSTGRES_USER=ai_requirement
      - POSTGRES_PASSWORD=change_me
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    container_name: ai_requirement_redis
    command: redis-server --save '' --appendonly no

volumes:
  uploads:
  pgdata:
```

#### 后端 Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 前端 Dockerfile

```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--host"]
```

### 7.3 快速启动指南

#### 本地开发模式

```bash
# 1. 克隆项目
git clone https://github.com/your-org/ai-requirement-platform.git
cd ai-requirement-platform

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入API密钥

# 3. 启动数据库与缓存（可选：亦可使用本地PostgreSQL/Redis）
docker compose up -d db redis

# 4. 启动后端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# 5. 启动前端（新终端）
cd frontend
npm install
npm run dev

# 6. 访问应用
# 浏览器打开 http://localhost:3000
```

#### Docker部署模式

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 2. 启动所有服务
docker-compose up -d

# 3. 查看日志
docker-compose logs -f

# 4. 停止服务
docker-compose down
```

### 7.4 常见问题解决

#### Q1: PaddleOCR安装失败
```bash
# 方案1: 使用国内镜像
pip install paddleocr -i https://pypi.tuna.tsinghua.edu.cn/simple

# 方案2: 如果GPU不可用，安装CPU版本
pip install paddlepaddle -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### Q2: API调用超时
```python
# 在config.py中增加超时设置
llm_config = {
    "config_list": config_list,
    "timeout": 120  # 增加到120秒
}
```

#### Q3: 前端无法连接WebSocket
```typescript
// 检查CORS配置（backend/app/main.py）
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 8. 附录

### 8.1 API详细文档

详见 `docs/API.md`

### 8.2 Agent Prompt模板

#### 需求分析师Prompt

```
你是一位资深需求分析师，拥有10年以上的产品需求分析经验。

你的任务是分析用户提供的需求文档，提取关键信息：

1. 核心功能模块
   - 列出所有主要功能模块
   - 使用emoji图标标识（如 👤 用户模块、🛍️ 商品模块）

2. 业务场景
   - 识别各模块下的具体业务场景
   - 描述场景的触发条件和流程

3. 业务规则
   - 提取文档中的约束条件
   - 识别隐含的业务规则

4. 非功能性需求
   - 性能要求
   - 安全要求
   - 兼容性要求

请以结构化的Markdown格式输出，方便后续处理。
```

#### 测试工程师Prompt

```
你是一位资深测试工程师，擅长设计全面的测试用例。

基于需求分析师提供的需求分析结果，为每个功能模块设计测试用例。

测试用例格式：
TC{编号}: {用例标题}
├ 前置条件: {必要的前置条件}
├ 操作步骤:
│   1. {步骤1}
│   2. {步骤2}
│   3. {步骤3}
├ 预期结果: {期望的系统响应}
└ 优先级: P0/P1/P2

测试覆盖要求：
1. 正常流程（Happy Path）
2. 异常处理（错误输入、网络异常等）
3. 边界条件（最大值、最小值、空值等）

优先级定义：
- P0: 核心功能，必须通过
- P1: 重要功能，建议通过
- P2: 次要功能，优化项

请为每个功能模块生成完整的测试用例。
```

### 8.3 XMind模板结构

```
电商平台测试用例
├── 用户注册登录
│   ├── 手机号注册
│   │   ├── TC001: 有效手机号注册成功
│   │   ├── TC002: 已注册手机号提示
│   │   └── TC003: 无效手机号格式校验
│   ├── 邮箱注册
│   │   └── ...
│   └── 第三方登录
│       └── ...
├── 商品浏览搜索
│   └── ...
└── ...
```

### 8.4 参考资源

- [AutoGen官方文档](https://microsoft.github.io/autogen/)
- [FastAPI官方文档](https://fastapi.tiangolo.com/)
- [通义千问API文档](https://help.aliyun.com/zh/dashscope/)
- [PaddleOCR文档](https://github.com/PaddlePaddle/PaddleOCR)
- [XMind文件格式](https://github.com/xmindltd/xmind-sdk-python)

---

## 📞 联系方式

如有问题或建议，请联系：
- Email: team@example.com
- GitHub Issues: https://github.com/your-org/ai-requirement-platform/issues

---

**文档结束**

*最后更新时间: 2025-10-19*
*文档版本: v1.0.0*
