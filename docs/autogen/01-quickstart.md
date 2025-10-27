# AutoGen 快速入门

## 什么是 AutoGen？

**AutoGen**（全称 AutoGen Framework）是由微软研究院开发并开源的 Python 框架，专门用于构建基于大语言模型（LLM）的多智能体协作系统。它的核心理念是让多个 AI 智能体能够像人类团队一样相互对话、分工协作，共同完成复杂的任务。

在传统的 AI 应用中，我们通常直接调用大语言模型的 API，让它一次性完成所有任务。但现实中很多任务是复杂的、多步骤的，单个模型很难一次性做好。AutoGen 借鉴了人类团队协作的模式：将复杂任务分解给具有不同专长的"智能体"，让它们各司其职、相互配合。

### 核心概念深度解析

#### 1. Agent（智能体）

**智能体**是 AutoGen 中最基本的概念。你可以把它理解为一个具有特定角色、能力和职责的 AI 工作者。

在本项目中，我们定义了四个智能体：
- **需求分析师**：负责阅读需求文档，提取功能模块、业务场景和规则
- **测试工程师**：根据需求分析结果，生成详细的测试用例
- **质量评审专家**：评审测试用例的完整性和准确性
- **测试补全工程师**：根据评审意见，补充缺失的测试用例

每个智能体都有：
- **身份定位**（system_message）：它是谁，擅长什么
- **工作能力**（llm_config）：它使用哪个大语言模型，有多强的推理能力
- **行为规范**（其他参数）：它如何与其他智能体交互，何时需要人工确认

**类比**：就像一个软件团队，产品经理负责需求分析，开发负责实现，测试负责质量保证，每个人各司其职。

#### 2. Conversation（对话）

**对话**是智能体之间的消息传递机制。AutoGen 自动管理对话的上下文（context），确保每个智能体都能"记住"之前说过什么。

在本项目的工作流中：
1. 需求分析师分析文档，输出结构化的需求（JSON 格式）
2. 测试工程师接收需求分析结果，生成测试用例（Markdown 表格）
3. 质量评审专家阅读测试用例，输出评审报告
4. 测试补全工程师根据评审意见，补充缺失的用例

每一步的输出都会作为下一步的输入，形成一个完整的对话链。

**类比**：就像团队开会，产品经理讲完需求，开发提问澄清，测试提出质量关注点，大家围绕同一个主题逐步推进。

#### 3. LLM Config（模型配置）

**模型配置**定义了智能体背后的"大脑"——使用哪个大语言模型、如何连接、超时时间等。

AutoGen 的强大之处在于**灵活性**：
- 你可以为不同智能体配置不同的模型（需求分析用视觉模型，测试生成用强推理模型）
- 你可以配置多个备选模型（主模型失败时自动切换）
- 你可以统一管理所有模型的 API 密钥和超时设置

在本项目中：
- **需求分析师**使用 `qwen3-vl-flash`（多模态视觉模型，能直接理解图片）
- **测试工程师**和**质量评审专家**使用 `qwen3-next-80b`（强推理模型，生成高质量测试用例）

**类比**：就像给不同岗位配备不同的工具，设计师用 Figma，开发用 IDE，测试用自动化工具。

### 为什么选择 AutoGen？

#### 1. 简化多智能体开发

如果不用 AutoGen，你需要手动实现：
- 消息队列：管理智能体之间的消息传递
- 上下文维护：保存每个对话的历史记录
- 状态机：控制工作流的执行顺序
- 错误处理：处理超时、重试、降级等异常情况

AutoGen 把这些复杂性都封装好了，你只需要关注业务逻辑：定义智能体的角色和任务。

#### 2. 灵活的模型支持

AutoGen 底层使用 OpenAI 兼容的 API 接口，这意味着它支持几乎所有主流的大语言模型：
- **OpenAI**：GPT-4、GPT-3.5
- **Azure OpenAI**：企业级 GPT 部署
- **通义千问**：本项目使用的国产大模型
- **Anthropic Claude**、**Google Gemini**、**本地模型**（通过 vLLM、Ollama 等）

你可以无缝切换模型，只需修改配置文件，无需改动业务代码。

#### 3. 生产级特性

AutoGen 不是一个玩具框架，它内置了很多生产环境必需的特性：
- **超时控制**：防止某个智能体卡住，影响整个流程
- **错误处理**：自动捕获异常，支持自定义降级策略
- **日志记录**：详细记录每个智能体的输入输出，便于调试
- **人工介入**：支持在关键步骤暂停，等待人工确认（本项目使用）

这些特性让你可以放心地将 AutoGen 应用部署到生产环境。

## 环境配置

### 1. 安装 AutoGen

```bash
pip install pyautogen==0.2.0
```

### 2. 安装 LLM SDK（以通义千问为例）

```bash
pip install openai==1.10.0
pip install dashscope>=1.24.6
```

### 3. 配置 API 密钥

创建 `.env` 文件：

```bash
QWEN_API_KEY=sk-your-api-key-here
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-plus
```

## 第一个 AutoGen 程序

### 示例 1：单个智能体

```python
from autogen import AssistantAgent

# 配置 LLM
llm_config = {
    "config_list": [{
        "model": "qwen-plus",
        "api_key": "sk-your-api-key",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"
    }],
    "timeout": 120,
}

# 创建智能体
assistant = AssistantAgent(
    name="assistant",
    system_message="你是一位友好的AI助手。",
    llm_config=llm_config,
    human_input_mode="NEVER",
    max_consecutive_auto_reply=1,
)

# 生成回复
response = assistant.generate_reply(
    messages=[{"role": "user", "content": "你好，介绍一下你自己"}]
)

print(response)
```

**输出示例**：
```
你好！我是一位AI助手，基于大语言模型构建...
```

### 示例 2：项目中的智能体创建（真实代码）

从 `backend/app/llm/autogen_runner.py` 中提取：

```python
from autogen import AssistantAgent

def create_agent(system_message: str, agent_type: str = "default") -> AssistantAgent:
    """创建智能体，根据类型使用不同的模型配置."""
    
    # 根据智能体类型获取配置
    if agent_type == "analysis":
        config = {
            "model": "qwen3-vl-flash",  # 需求分析用视觉模型
            "api_key": "sk-your-key",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"
        }
    elif agent_type == "test":
        config = {
            "model": "qwen3-next-80b-a3b-instruct",  # 测试生成用强力模型
            "api_key": "sk-your-key",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"
        }
    else:
        config = {
            "model": "qwen-plus",  # 默认模型
            "api_key": "sk-your-key",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"
        }
    
    return AssistantAgent(
        name=f"{agent_type}_agent",
        system_message=system_message,
        llm_config={
            "config_list": [config],
            "timeout": 120,
        },
        human_input_mode="NEVER",  # 不需要人工输入
        max_consecutive_auto_reply=1,  # 只自动回复一次
        code_execution_config=False,  # 禁用代码执行
    )

# 创建需求分析师
analyst = create_agent(
    system_message="你是一位资深需求分析师，擅长从文档中提取功能模块和业务规则。",
    agent_type="analysis"
)

# 使用智能体
prompt = "请分析以下需求：用户登录系统，支持密码和指纹两种方式..."
reply = analyst.generate_reply(messages=[{"role": "user", "content": prompt}])
print(reply)
```

## AutoGen vs 直接调用 OpenAI SDK

### 直接调用 OpenAI SDK

```python
from openai import OpenAI

client = OpenAI(api_key="sk-xxx", base_url="https://...")
response = client.chat.completions.create(
    model="qwen-plus",
    messages=[
        {"role": "system", "content": "你是一位需求分析师"},
        {"role": "user", "content": "分析这个需求..."}
    ]
)
print(response.choices[0].message.content)
```

### 使用 AutoGen

```python
from autogen import AssistantAgent

agent = AssistantAgent(
    name="analyst",
    system_message="你是一位需求分析师",
    llm_config={"config_list": [{"model": "qwen-plus", "api_key": "sk-xxx"}]}
)
reply = agent.generate_reply(messages=[{"role": "user", "content": "分析这个需求..."}])
print(reply)
```

### 对比总结

| 特性 | OpenAI SDK | AutoGen |
|------|-----------|---------|
| **简单单次调用** | ✅ 更简洁 | ❌ 稍显冗长 |
| **多智能体协作** | ❌ 需要手动实现 | ✅ 内置支持 |
| **对话上下文管理** | ❌ 需要手动维护 | ✅ 自动管理 |
| **重试和错误处理** | ❌ 需要手动实现 | ✅ 内置支持 |
| **适用场景** | 简单问答 | 复杂多步骤任务 |

## 核心 API 快速参考

### AssistantAgent 参数

```python
AssistantAgent(
    name="agent_name",           # 智能体名称（唯一标识）
    system_message="...",        # 系统提示词（定义角色和能力）
    llm_config={...},            # LLM 配置（模型、API密钥等）
    human_input_mode="NEVER",    # 人工介入模式：NEVER/TERMINATE/ALWAYS
    max_consecutive_auto_reply=1,# 最大自动回复次数
    code_execution_config=False, # 是否允许执行代码
)
```

### generate_reply 方法

```python
response = agent.generate_reply(
    messages=[
        {"role": "user", "content": "你的提示词"}
    ]
)
```

**返回值**：字符串或字典类型的回复内容

## 常见问题

### 1. 如何切换不同的 LLM 提供商？

只需修改 `llm_config` 中的 `base_url` 和 `api_key`：

```python
# OpenAI
config = {"model": "gpt-4", "api_key": "sk-xxx"}

# Azure OpenAI
config = {
    "model": "gpt-4",
    "api_key": "xxx",
    "base_url": "https://your-resource.openai.azure.com/",
    "api_type": "azure",
    "api_version": "2024-02-01"
}

# 通义千问
config = {
    "model": "qwen-plus",
    "api_key": "sk-xxx",
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"
}
```

### 2. 如何调试智能体的输出？

```python
import logging
logging.basicConfig(level=logging.INFO)

# AutoGen 会自动打印详细的对话日志
```

### 3. 超时怎么办？

```python
llm_config = {
    "config_list": [...],
    "timeout": 300,  # 增加超时时间到 5 分钟
}
```

## 下一步

恭喜你完成了快速入门！接下来学习：

- 📘 [智能体配置详解](./02-agent-configuration.md) - 深入理解各种配置参数
- 📗 [多智能体协作实战](./03-multi-agent-workflow.md) - 构建复杂的工作流

---

**有疑问？** 查看 [AutoGen 官方文档](https://microsoft.github.io/autogen/) 或参考项目源码 `backend/app/llm/autogen_runner.py`
