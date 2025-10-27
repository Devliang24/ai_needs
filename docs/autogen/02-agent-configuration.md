# 智能体配置详解

## 前言

智能体的配置是 AutoGen 开发中最核心的环节。一个配置良好的智能体能够准确理解任务、高效完成工作；配置不当则可能导致输出质量差、成本高昂、甚至完全无法工作。

本章将深入讲解 AssistantAgent 的每个配置参数，并结合项目实战代码，展示如何为不同角色的智能体选择最佳配置。

## AssistantAgent 核心参数全解析

### 1. name（智能体名称）

#### 作用

`name` 是智能体的唯一标识符，主要用于：
- **日志记录**：在日志中区分不同智能体的输出
- **调试追踪**：快速定位问题出在哪个智能体
- **多智能体对话**：当多个智能体互动时，通过名称识别发言者

#### 命名规范

```python
# ✅ 推荐：描述性命名，使用小写字母和下划线
agent = AssistantAgent(name="requirement_analyst")
agent = AssistantAgent(name="test_engineer")
agent = AssistantAgent(name="quality_reviewer")

# ❌ 不推荐：无意义的命名
agent = AssistantAgent(name="agent1")
agent = AssistantAgent(name="a")
agent = AssistantAgent(name="temp")
```

#### 最佳实践

1. **使用英文**：避免中文名称可能导致的编码问题
2. **体现角色**：名称应该清楚表达智能体的职责
3. **保持一致**：整个项目使用统一的命名风格

#### 项目实战示例

在 `backend/app/llm/autogen_runner.py` 中：

```python
def _agent(system_message: str, agent_type: str = "default") -> AssistantAgent:
    return AssistantAgent(
        name=f"{agent_type}_agent",  # 动态生成名称：analysis_agent, test_agent 等
        # ...
    )
```

这种做法的好处是：
- 名称与类型保持一致，便于追踪
- 避免硬编码，提高代码复用性

### 2. system_message（系统提示词）

#### 为什么 system_message 如此重要？

`system_message` 是智能体的"人格定义"和"工作指南"，它决定了：
- **智能体的角色**：它是谁，有什么专长
- **任务理解**：它应该做什么，不应该做什么
- **输出格式**：结果应该以什么形式呈现
- **行为约束**：哪些操作是被允许的，哪些是被禁止的

一个精心设计的 system_message 可以让智能体的输出质量提升 50% 以上。

#### 编写 system_message 的黄金法则

##### 法则 1：明确角色定位

第一句话就应该清楚说明智能体的身份。

```python
# ✅ 好的示例
system_message = "你是一位资深需求分析师，拥有 10 年以上的软件行业经验。"

# ❌ 不好的示例
system_message = "你是一个助手。"  # 太泛泛，没有专业性
```

**为什么这很重要**？大语言模型会根据角色定位调整输出风格和深度。"资深需求分析师"会比"助手"产生更专业、更深入的分析。

##### 法则 2：具体描述任务

告诉智能体要做什么，越具体越好。

```python
# ✅ 好的示例（项目真实代码）
system_message = (
    "你是一位资深需求分析师。请仔细阅读需求文档，"
    "识别并提取文档中的所有具体功能模块、业务场景和业务规则。"
    "必须基于文档的实际内容进行分析，不要使用泛化的占位符（如'模块1'、'场景1'）。"
)

# ❌ 不好的示例
system_message = "请分析需求。"  # 太模糊，智能体不知道分析什么、怎么分析
```

**关键点**：
- "仔细阅读需求文档" → 强调输入来源
- "识别并提取" → 明确动作
- "功能模块、业务场景、业务规则" → 指定输出内容
- "不要使用占位符" → 约束行为，避免低质量输出

##### 法则 3：指定输出格式

明确告诉智能体以什么格式返回结果。

```python
# ✅ JSON 格式示例（需求分析师）
system_message = (
    "你是一位资深需求分析师。..."
    "输出JSON格式，包含: modules (name为实际模块名, scenarios为具体场景描述[], "
    "rules为具体规则描述[]), risks[]。"
)

# ✅ Markdown 格式示例（测试工程师）
system_message = (
    "你是一位资深测试工程师。..."
    "请以Markdown格式输出，包含清晰的章节结构和表格。"
)
```

**为什么要指定格式**？
- 结构化输出便于程序解析（JSON）
- 可读性更好，便于人工review（Markdown）
- 避免智能体自由发挥，产生不可预测的格式

##### 法则 4：添加约束条件

明确告诉智能体什么不能做，避免常见错误。

```python
system_message = (
    "你是一位资深需求分析师。..."
    "必须基于文档的实际内容进行分析，不要使用泛化的占位符（如'模块1'、'场景1'）。"
    "不要进行猜测或推断文档中未明确提及的内容。"
    "如果某个部分信息不足，明确指出而不是编造细节。"
)
```

**常见的约束**：
- 禁止使用占位符（"模块1"、"功能A"）
- 禁止猜测或推断
- 禁止输出不相关内容
- 禁止违反格式要求

#### 项目实战：四个智能体的 system_message

##### 需求分析师

从 `backend/app/llm/autogen_runner.py` 的 `_run_text_based_analysis` 函数：

```python
system_message = (
    "你是一位资深需求分析师。请仔细阅读需求文档，"
    "识别并提取文档中的所有具体功能模块、业务场景和业务规则。"
    "必须基于文档的实际内容进行分析，不要使用泛化的占位符（如'模块1'、'场景1'）。"
    "输出JSON格式，包含: modules (name为实际模块名, scenarios为具体场景描述[], "
    "rules为具体规则描述[]), risks[]。"
)
```

**设计思路**：
- **角色定位**："资深需求分析师" → 专业、经验丰富
- **任务描述**："识别并提取功能模块、业务场景、业务规则" → 明确输出内容
- **约束条件**："不要使用占位符"、"基于实际内容" → 避免低质量输出
- **输出格式**："JSON格式，包含 modules, scenarios, rules, risks" → 结构化输出

**为什么这样设计**？
1. 需求分析的结果需要被测试工程师使用，必须结构化（JSON）
2. 占位符（如"模块1"）对后续工作毫无价值，必须明确禁止
3. risks 字段可以帮助发现潜在问题，提前规避风险

##### 测试工程师

从 `backend/app/llm/autogen_runner.py` 的 `run_test_generation` 函数：

```python
system_message = (
    "你是一位资深测试工程师。根据需求分析结果，"
    "为每个具体功能模块生成详细的测试用例。"
    "请以Markdown格式输出，包含清晰的章节结构和表格。"
)
```

**对应的 prompt**（用户输入）：

```python
test_prompt = (
    "以下是需求分析结果，请以Markdown格式生成测试用例。要求:\n"
    "1. 按功能模块组织，每个模块使用 ## 标题\n"
    "2. 使用表格展示测试用例，包含列: 用例ID | 标题 | 前置条件 | 测试步骤 | 预期结果 | 优先级\n"
    "3. 测试步骤和前置条件使用简洁的文本描述或编号列表\n"
    "4. 覆盖正常流程、异常处理、边界条件等场景\n"
    "5. 专注于功能行为和业务逻辑的验证\n\n"
    f"需求分析结果:\n{json.dumps(analysis_payload, ensure_ascii=False)}"
)
```

**设计思路**：
- **system_message** 简洁明了，定义角色和输出格式
- **prompt** 中包含详细的要求和输入数据
- 这种分离让代码更清晰：角色定义和任务描述分开

**为什么用 Markdown 表格**？
1. 测试用例需要包含多个字段（ID、标题、步骤、预期结果等），表格最适合
2. Markdown 格式可读性好，前端可以直接渲染
3. 便于人工review和修改

##### 质量评审专家

从 `backend/app/llm/autogen_runner.py` 的 `run_quality_review` 函数：

```python
system_message = (
    "你是质量评审专家。仔细评审测试用例的完整性和准确性，"
    "以Markdown格式输出评审报告。"
)
```

**对应的 prompt**：

```python
review_prompt = (
    "请评审以下测试用例，以Markdown格式输出评审报告。要求:\n"
    "1. 使用 ## 评审摘要 章节，说明覆盖率评估和整体评价\n"
    "2. 使用 ## 发现的缺陷 章节，列出具体缺陷和遗漏的功能点\n"
    "3. 使用 ## 改进建议 章节，提供针对性的改进建议\n"
    "4. 重点关注功能行为的完整性（主流程、异常流程、边界条件等）\n\n"
    f"测试用例:\n{test_content}"
)
```

**设计思路**：
- 评审专家的职责是"找问题"，所以 prompt 中强调"缺陷"、"遗漏"、"改进"
- 输出分三个章节，结构清晰
- "重点关注功能行为的完整性" → 引导评审方向

##### 测试补全工程师

从 `backend/app/llm/autogen_runner.py` 的 `run_test_completion` 函数：

```python
system_message = (
    "你是一位测试补全工程师。根据质量评审发现的缺口与建议，"
    "以Markdown格式补充缺失的测试用例。"
)
```

**对应的 prompt**：

```python
completion_prompt = (
    "请根据质量评审的缺陷和建议，以Markdown格式补充测试用例。要求:\n"
    "1. 使用与原测试用例相同的Markdown表格格式\n"
    "2. 只补充缺失的用例，不重复已有内容\n"
    "3. 按功能模块组织，每个模块使用 ## 标题\n"
    "4. 每条测试用例包含明确的步骤和可验证的预期结果\n\n"
    f"原始测试用例:\n{test_content}\n\n"
    f"质量评审报告:\n{review_content}"
)
```

**设计思路**：
- 补全工程师需要同时看到"原始用例"和"评审报告"
- "只补充缺失的用例，不重复已有内容" → 避免冗余
- "使用相同的表格格式" → 保持一致性，便于后续合并

#### system_message 编写检查清单

在编写 system_message 时，问自己这些问题：

- [ ] 是否明确定义了智能体的角色？
- [ ] 是否清楚说明了要做什么？
- [ ] 是否指定了输出格式？
- [ ] 是否添加了必要的约束条件？
- [ ] 是否避免了模糊或二义性的描述？
- [ ] 是否足够具体，让智能体理解任务细节？

### 3. llm_config（模型配置）

#### llm_config 的结构

```python
llm_config = {
    "config_list": [  # 模型配置列表（支持多个备选）
        {
            "model": "qwen-plus",          # 模型名称
            "api_key": "sk-xxx",           # API 密钥
            "base_url": "https://...",     # API 地址
            "api_type": "openai",          # 可选：API 类型
            "api_version": "2024-02-01",   # 可选：API 版本（Azure 需要）
        }
    ],
    "timeout": 120,            # 超时时间（秒）
    "temperature": 0.7,        # 可选：创造性程度（0-2）
    "max_tokens": 4096,        # 可选：最大输出 token 数
    "top_p": 0.9,              # 可选：采样参数
}
```

#### config_list 详解

`config_list` 是一个列表，包含一个或多个模型配置。AutoGen 会按顺序尝试，如果第一个失败则使用第二个（failover 机制）。

##### 单模型配置（最常见）

```python
"config_list": [{
    "model": "qwen-plus",
    "api_key": "sk-your-api-key",
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"
}]
```

##### 多模型备选配置（高可用）

```python
"config_list": [
    {
        "model": "qwen3-next-80b",  # 主模型：性能强，但可能限流
        "api_key": "sk-xxx",
    },
    {
        "model": "qwen-plus",  # 备选模型：性能稍弱，但稳定
        "api_key": "sk-xxx",
    }
]
```

**使用场景**：
- 主模型遇到限流或故障时，自动切换到备选模型
- 适合生产环境，提高系统可用性

##### 跨提供商配置（极致高可用）

```python
"config_list": [
    {
        "model": "qwen-plus",
        "api_key": "sk-qwen-xxx",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"
    },
    {
        "model": "gpt-4",
        "api_key": "sk-openai-xxx",
        "base_url": "https://api.openai.com/v1"
    }
]
```

**使用场景**：
- 需要极高可用性的关键业务
- 一个提供商完全不可用时，切换到另一个

#### timeout（超时时间）

`timeout` 指定单次 API 调用的最大等待时间（秒）。超过这个时间，AutoGen 会抛出 TimeoutError。

##### 如何选择合适的 timeout？

```python
# 简单任务（文本分类、实体提取）
"timeout": 30  # 30 秒足够

# 中等任务（需求分析、摘要生成）
"timeout": 120  # 2 分钟（项目默认值）

# 复杂任务（代码生成、测试用例生成）
"timeout": 300  # 5 分钟

# 超复杂任务（大规模推理、长文本生成）
"timeout": 600  # 10 分钟
```

**最佳实践**：
- 根据任务复杂度动态调整，不要一刀切
- 太短：容易超时，用户体验差
- 太长：挂起时间太久，资源浪费

##### 项目实战：不同智能体的 timeout 设置

从 `backend/app/llm/autogen_runner.py`：

```python
def _agent(system_message: str, agent_type: str = "default") -> AssistantAgent:
    return AssistantAgent(
        # ...
        llm_config={
            "config_list": [config],
            "timeout": settings.llm_timeout,  # 默认 120 秒
        },
    )
```

项目使用统一的 120 秒超时，这是一个平衡的选择：
- 需求分析：处理图片文档可能较慢，120 秒通常够用
- 测试生成：生成多个测试用例，120 秒可能有点紧张，但可接受
- 质量评审和补全：相对简单，120 秒绰绰有余

**改进建议**：可以为不同智能体设置不同的 timeout：

```python
TIMEOUT_CONFIG = {
    "analysis": 180,     # 需求分析：3 分钟（处理图片）
    "test": 240,         # 测试生成：4 分钟（生成大量用例）
    "review": 120,       # 质量评审：2 分钟
    "completion": 180,   # 用例补全：3 分钟
}

def _agent(system_message: str, agent_type: str = "default") -> AssistantAgent:
    timeout = TIMEOUT_CONFIG.get(agent_type, 120)
    return AssistantAgent(
        llm_config={"timeout": timeout, ...},
    )
```

#### temperature（创造性程度）

`temperature` 控制模型输出的随机性和创造性，范围通常是 0-2：
- **0**：完全确定性，每次输出几乎相同
- **0.1-0.3**：低随机性，适合精确任务
- **0.7-1.0**：中等随机性，平衡创造性和准确性
- **1.5-2.0**：高随机性，适合创意任务

##### 如何选择 temperature？

```python
# 精确任务（数据提取、分类、格式转换）
"temperature": 0.1

# 分析任务（需求分析、代码审查）
"temperature": 0.5

# 平衡任务（大多数场景）
"temperature": 0.7  # 推荐默认值

# 生成任务（测试用例生成、文案撰写）
"temperature": 0.9

# 创意任务（头脑风暴、故事创作）
"temperature": 1.2
```

**项目中的选择**：

项目代码中没有显式设置 temperature，意味着使用模型默认值（通常是 1.0）。

**改进建议**：

```python
TEMPERATURE_CONFIG = {
    "analysis": 0.3,    # 需求分析：需要准确提取，不要发挥
    "test": 0.8,        # 测试生成：需要创造性，覆盖多种场景
    "review": 0.5,      # 质量评审：需要严谨，但不能太死板
    "completion": 0.8,  # 用例补全：需要创造性，补充新场景
}
```

#### max_tokens（最大输出长度）

`max_tokens` 限制模型单次输出的最大 token 数。1 token ≈ 0.75 个英文单词，≈ 0.5 个中文字。

##### 如何估算 max_tokens？

```python
# 简短回答（100-200 字）
"max_tokens": 300

# 中等回答（500-1000 字）
"max_tokens": 1500

# 长回答（2000-3000 字）
"max_tokens": 4096  # 通常是上限

# 超长回答（5000+ 字）
"max_tokens": 8192  # 部分模型支持
```

**项目中的选择**：

项目没有显式设置 max_tokens，意味着使用模型默认值（qwen-plus 是 2048）。

**潜在问题**：
- 测试用例生成可能需要很长的输出（多个模块、每个模块多个用例）
- 如果超过 2048 tokens，输出会被截断

**改进建议**：

```python
MAX_TOKENS_CONFIG = {
    "analysis": 2048,     # 需求分析：JSON 输出，通常不会太长
    "test": 8192,         # 测试生成：Markdown 表格，可能很长
    "review": 2048,       # 质量评审：报告通常中等长度
    "completion": 4096,   # 用例补全：补充用例，可能较长
}
```

### 4. human_input_mode（人工介入模式）

#### 三种模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| `NEVER` | 完全自动化，不需要人工输入 | 后台批处理、自动化任务 |
| `TERMINATE` | 对话结束时请求确认 | 需要最终审核的任务 |
| `ALWAYS` | 每次回复前都询问人工 | 交互式助手、高风险操作 |

#### 项目中的选择

项目使用 `NEVER`：

```python
AssistantAgent(
    # ...
    human_input_mode="NEVER",  # 不在智能体层面等待人工输入
)
```

**为什么选择 NEVER**？

因为项目在**工作流层面**实现了自定义的人工确认机制（见 `backend/app/orchestrator/workflow.py` 的 `_wait_for_confirmation` 函数）：

```python
async def _wait_for_confirmation(self, stage: AgentStage, timeout: int = 300) -> bool:
    """等待用户确认当前阶段的结果."""
    # 轮询等待用户确认...
    for _ in range(timeout):
        await asyncio.sleep(1)
        confirmation = await session_events.get_confirmation(self.session_id)
        if confirmation and confirmation.get("confirmed"):
            return True
        elif confirmation and confirmation.get("rejected"):
            return False
    return False  # 超时
```

这种设计的优势：
- **更灵活**：可以在任意步骤之间插入确认点
- **更可控**：可以自定义确认逻辑（超时、拒绝处理等）
- **更友好**：通过 WebSocket 实时推送，用户体验更好

#### 何时使用 TERMINATE 或 ALWAYS？

```python
# 使用 TERMINATE：需要最终审核
chatbot = AssistantAgent(
    name="chatbot",
    system_message="你是一位客服助手",
    human_input_mode="TERMINATE",  # 回答完成后，等待用户确认是否满意
)

# 使用 ALWAYS：高风险操作
database_admin = AssistantAgent(
    name="database_admin",
    system_message="你是数据库管理员，可以执行SQL语句",
    human_input_mode="ALWAYS",  # 每次执行SQL前都要人工确认
    code_execution_config={"work_dir": "./db_workspace"},
)
```

### 5. max_consecutive_auto_reply（最大自动回复次数）

#### 作用

限制智能体连续自动回复的次数，防止无限循环。

#### 项目中的选择

```python
AssistantAgent(
    # ...
    max_consecutive_auto_reply=1,  # 只自动回复一次
)
```

**为什么设置为 1**？

因为项目的工作流是**线性的、单向的**：

```
需求分析师 → 测试工程师 → 质量评审专家 → 测试补全工程师
```

每个智能体只需要回复一次，不需要多轮对话。

#### 何时需要更大的值？

```python
# 简单多轮对话
chatbot = AssistantAgent(
    name="chatbot",
    max_consecutive_auto_reply=3,  # 最多自动回复 3 次
)

# 复杂协作任务（两个智能体互相讨论）
analyst = AssistantAgent(
    name="analyst",
    max_consecutive_auto_reply=5,  # 与开发讨论需求，最多 5 轮
)

developer = AssistantAgent(
    name="developer",
    max_consecutive_auto_reply=5,
)
```

### 6. code_execution_config（代码执行配置）

#### 作用

控制智能体是否可以执行代码（Python、Shell 等）。

#### 项目中的选择

```python
AssistantAgent(
    # ...
    code_execution_config=False,  # 禁用代码执行
)
```

**为什么禁用**？

因为项目的智能体只需要进行**文本分析和生成**，不需要执行代码。禁用代码执行有两个好处：
1. **安全性**：避免恶意代码注入风险
2. **性能**：不需要启动代码执行环境

#### 何时启用代码执行？

```python
# 数据分析助手
data_analyst = AssistantAgent(
    name="data_analyst",
    system_message="你是数据分析师，可以编写 Python 代码分析数据",
    code_execution_config={
        "work_dir": "./workspace",  # 代码执行目录
        "use_docker": True,          # 使用 Docker 隔离（推荐）
        "timeout": 60,               # 代码执行超时时间
    },
)
```

**安全提示**：如果启用代码执行，强烈建议：
1. 使用 Docker 隔离（`use_docker=True`）
2. 限制文件系统访问
3. 设置资源限制（CPU、内存）
4. 启用人工审核（`human_input_mode="ALWAYS"`）

## 完整配置示例

### 示例 1：需求分析师（项目真实配置）

```python
from autogen import AssistantAgent
from app.config import settings

requirement_analyst = AssistantAgent(
    name="requirement_analyst",
    system_message=(
        "你是一位资深需求分析师。请仔细阅读需求文档，"
        "识别并提取文档中的所有具体功能模块、业务场景和业务规则。"
        "必须基于文档的实际内容进行分析，不要使用泛化的占位符。"
        "输出JSON格式，包含: modules (name为实际模块名, scenarios为具体场景描述[], "
        "rules为具体规则描述[]), risks[]。"
    ),
    llm_config={
        "config_list": [{
            "model": "qwen3-vl-flash",  # 多模态视觉模型，支持图片
            "api_key": settings.qwen_api_key,
            "base_url": settings.qwen_base_url,
        }],
        "timeout": 180,  # 3 分钟（处理图片需要更多时间）
        "temperature": 0.3,  # 低随机性，确保提取准确
        "max_tokens": 2048,
    },
    human_input_mode="NEVER",
    max_consecutive_auto_reply=1,
    code_execution_config=False,
)
```

### 示例 2：测试工程师（改进版）

```python
test_engineer = AssistantAgent(
    name="test_engineer",
    system_message=(
        "你是一位资深测试工程师。根据需求分析结果，"
        "为每个具体功能模块生成详细的测试用例。"
        "请以Markdown格式输出，包含清晰的章节结构和表格。"
    ),
    llm_config={
        "config_list": [{
            "model": "qwen3-next-80b-a3b-instruct",  # 强推理模型
            "api_key": settings.qwen_api_key,
            "base_url": settings.qwen_base_url,
        }],
        "timeout": 240,  # 4 分钟（生成大量用例）
        "temperature": 0.8,  # 中高随机性，鼓励创造性
        "max_tokens": 8192,  # 大输出空间，支持长表格
    },
    human_input_mode="NEVER",
    max_consecutive_auto_reply=1,
    code_execution_config=False,
)
```

## 配置最佳实践

### 1. 环境变量管理

❌ **不要硬编码 API 密钥**：

```python
llm_config = {
    "config_list": [{
        "api_key": "sk-123456789",  # 危险！可能泄露到代码仓库
    }]
}
```

✅ **使用环境变量**：

```python
from app.config import settings

llm_config = {
    "config_list": [{
        "api_key": settings.qwen_api_key,  # 从环境变量读取
        "base_url": settings.qwen_base_url,
    }]
}
```

### 2. 根据任务调整参数

```python
# 精确任务（数据提取）
precise_config = {
    "timeout": 60,
    "temperature": 0.1,
    "max_tokens": 1024,
}

# 创造任务（测试生成）
creative_config = {
    "timeout": 240,
    "temperature": 0.9,
    "max_tokens": 8192,
}
```

### 3. 使用配置工厂函数

```python
def create_llm_config(
    model: str,
    timeout: int = 120,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> dict:
    return {
        "config_list": [{
            "model": model,
            "api_key": settings.qwen_api_key,
            "base_url": settings.qwen_base_url,
        }],
        "timeout": timeout,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

# 使用
analyst_config = create_llm_config(
    model="qwen3-vl-flash",
    timeout=180,
    temperature=0.3,
)
```

### 4. 记录和监控

```python
import logging

logger = logging.getLogger(__name__)

def create_agent(name, system_message, llm_config):
    logger.info(f"创建智能体: {name}")
    logger.info(f"模型: {llm_config['config_list'][0]['model']}")
    logger.info(f"超时: {llm_config['timeout']}s")
    
    return AssistantAgent(
        name=name,
        system_message=system_message,
        llm_config=llm_config,
    )
```

## 调试技巧

### 1. 打印完整配置

```python
import json

agent = create_agent(...)
print("智能体配置:")
print(json.dumps({
    "name": agent.name,
    "system_message": agent.system_message,
    "llm_config": agent.llm_config,
}, indent=2, ensure_ascii=False))
```

### 2. 启用详细日志

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 3. 测试不同配置的效果

```python
test_configs = [
    {"temperature": 0.1, "label": "低随机性"},
    {"temperature": 0.7, "label": "中等随机性"},
    {"temperature": 1.2, "label": "高随机性"},
]

for config in test_configs:
    agent = AssistantAgent(
        name="test",
        system_message="你是测试工程师",
        llm_config={
            "config_list": [{"model": "qwen-plus"}],
            "temperature": config["temperature"],
        },
    )
    
    reply = agent.generate_reply(
        messages=[{"role": "user", "content": "生成登录功能的测试用例"}]
    )
    
    print(f"\n{config['label']} (temperature={config['temperature']}):")
    print(reply[:300], "...")
```

## 常见问题

### Q1: 如何切换到 Azure OpenAI？

```python
llm_config = {
    "config_list": [{
        "model": "gpt-4",
        "api_type": "azure",
        "api_key": "your-azure-key",
        "base_url": "https://your-resource.openai.azure.com/",
        "api_version": "2024-02-01",
    }],
}
```

### Q2: 如何配置多个备选模型？

```python
llm_config = {
    "config_list": [
        {"model": "qwen3-next-80b", "api_key": "sk-xxx"},  # 主模型
        {"model": "qwen-plus", "api_key": "sk-xxx"},        # 备选
    ],
}
# AutoGen 会按顺序尝试
```

### Q3: 如何限制成本？

```python
# 1. 使用较小的模型
"model": "qwen-plus"  # 而不是 qwen3-next-80b

# 2. 限制输出长度
"max_tokens": 1024  # 而不是 8192

# 3. 缩短超时时间
"timeout": 60  # 而不是 300

# 4. 降低 temperature（减少重试次数）
"temperature": 0.1
```

## 下一步

现在你已经掌握了智能体配置的所有细节，接下来学习：

📗 [多智能体协作实战](./03-multi-agent-workflow.md) - 让多个智能体协同工作

---

**参考资源**：
- 项目源码：`backend/app/llm/autogen_runner.py`
- 配置文件：`backend/.env.example`
