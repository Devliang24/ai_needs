# 智能体配置详解

## system_message 编写

从项目 `backend/app/llm/autogen_runner.py` 提取的真实示例：

```python
# 需求分析师
system_message = (
    "你是一位资深需求分析师。请仔细阅读需求文档，"
    "识别并提取文档中的所有具体功能模块、业务场景和业务规则。"
    "输出JSON格式。"
)

# 测试工程师  
system_message = (
    "你是一位资深测试工程师。根据需求分析结果，"
    "为每个功能模块生成详细的测试用例。以Markdown格式输出。"
)
```

## llm_config 配置

```python
llm_config = {
    "config_list": [{
        "model": "qwen-plus",
        "api_key": "sk-xxx",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"
    }],
    "timeout": 120,
}
```

## 完整示例（项目真实代码）

```python
from autogen import AssistantAgent

analyst = AssistantAgent(
    name="requirement_analyst",
    system_message="你是一位资深需求分析师...",
    llm_config={
        "config_list": [{"model": "qwen3-vl-flash", "api_key": "sk-xxx"}],
        "timeout": 120,
    },
    human_input_mode="NEVER",
    max_consecutive_auto_reply=1,
    code_execution_config=False,
)
```

## 参数说明

| 参数 | 说明 | 推荐值 |
|------|------|--------|
| name | 智能体名称 | 描述性命名 |
| system_message | 角色定义 | 明确任务 |
| llm_config | 模型配置 | 根据任务选择 |
| human_input_mode | 人工介入 | NEVER |
| max_consecutive_auto_reply | 回复次数 | 1 |

## 下一步

📗 [多智能体协作实战](./03-multi-agent-workflow.md)
