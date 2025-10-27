# AutoGen 快速入门

## 什么是 AutoGen？

**AutoGen** 是由微软开发的开源框架，用于构建基于大语言模型（LLM）的多智能体系统。它让多个 AI 智能体能够相互对话、协作完成复杂任务。

### 核心概念

| 概念 | 说明 | 类比 |
|------|------|------|
| **Agent（智能体）** | 具有特定角色和能力的 AI 实体 | 团队中的不同岗位（产品经理、开发、测试） |
| **Conversation（对话）** | 智能体之间的消息交互 | 团队成员之间的工作沟通 |
| **LLM Config（模型配置）** | 连接和配置底层大语言模型 | 团队成员的技能和工具 |

### 为什么选择 AutoGen？

- ✅ **简化多智能体开发**：无需自己管理对话状态和消息传递
- ✅ **灵活的模型支持**：兼容 OpenAI、Azure、通义千问等
- ✅ **生产级特性**：错误处理、重试、超时控制等开箱即用

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
