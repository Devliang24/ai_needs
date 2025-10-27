# 多智能体协作实战

## 项目工作流程

本项目实现了 4 个智能体的协作流程：

```
需求分析师 → 测试工程师 → 质量评审专家 → 测试补全工程师
```

## generate_reply 基础用法

```python
from autogen import AssistantAgent

agent = AssistantAgent(
    name="analyst",
    system_message="你是需求分析师",
    llm_config={"config_list": [{"model": "qwen-plus", "api_key": "sk-xxx"}]}
)

# 发送消息并获取回复
reply = agent.generate_reply(
    messages=[{"role": "user", "content": "分析这个需求..."}]
)
print(reply)
```

## 项目实战：4 阶段工作流

从 `backend/app/llm/autogen_runner.py` 提取：

###  1. 需求分析阶段

```python
def run_requirement_analysis(document_data: list[dict]):
    system_message = (
        "你是一位资深需求分析师。请仔细阅读需求文档，"
        "识别并提取文档中的所有具体功能模块、业务场景和业务规则。"
    )
    
    # 构建提示词
    documents_text = "\n".join([doc["content"] for doc in document_data])
    prompt = f"请分析以下需求文档:\n{documents_text}"
    
    # 创建智能体
    analyst = AssistantAgent(
        name="requirement_analyst",
        system_message=system_message,
        llm_config={"config_list": [{"model": "qwen3-vl-flash"}]},
        human_input_mode="NEVER",
    )
    
    # 生成回复
    reply = analyst.generate_reply(
        messages=[{"role": "user", "content": prompt}]
    )
    
    # 提取 JSON 结果
    analysis_result = extract_json(reply)
    return analysis_result
```

### 2. 测试用例生成阶段

```python
def run_test_generation(analysis_result: dict):
    system_message = (
        "你是一位资深测试工程师。根据需求分析结果，"
        "为每个功能模块生成详细的测试用例。以Markdown格式输出。"
    )
    
    prompt = f"根据以下需求生成测试用例:\n{json.dumps(analysis_result)}"
    
    test_engineer = AssistantAgent(
        name="test_engineer",
        system_message=system_message,
        llm_config={"config_list": [{"model": "qwen3-next-80b"}]},
    )
    
    test_cases = test_engineer.generate_reply(
        messages=[{"role": "user", "content": prompt}]
    )
    
    return test_cases
```

### 3. 质量评审阶段

```python
def run_quality_review(test_cases: str):
    system_message = (
        "你是质量评审专家。仔细评审测试用例的完整性和准确性，"
        "以Markdown格式输出评审报告。"
    )
    
    reviewer = AssistantAgent(
        name="quality_reviewer",
        system_message=system_message,
        llm_config={"config_list": [{"model": "qwen3-next-80b"}]},
    )
    
    review_report = reviewer.generate_reply(
        messages=[{"role": "user", "content": f"评审以下测试用例:\n{test_cases}"}]
    )
    
    return review_report
```

### 4. 用例补全阶段

```python
def run_test_completion(test_cases: str, review_report: str):
    system_message = (
        "你是一位测试补全工程师。根据质量评审发现的缺口与建议，"
        "以Markdown格式补充缺失的测试用例。"
    )
    
    completer = AssistantAgent(
        name="test_completer",
        system_message=system_message,
        llm_config={"config_list": [{"model": "qwen3-next-80b"}]},
    )
    
    additional_cases = completer.generate_reply(
        messages=[{"role": "user", "content": f"原测试用例:\n{test_cases}\n\n评审报告:\n{review_report}"}]
    )
    
    return additional_cases
```

## 完整工作流编排

从 `backend/app/orchestrator/workflow.py` 提取：

```python
class SessionWorkflowExecution:
    async def execute(self):
        # 1. 需求分析
        analysis_result = await run_requirement_analysis(document_data)
        await self._emit_progress("需求分析完成", progress=0.3)
        
        # 2. 测试用例生成
        test_cases = await run_test_generation(analysis_result)
        await self._emit_progress("测试用例生成完成", progress=0.6)
        
        # 3. 质量评审
        review_report = await run_quality_review(test_cases)
        await self._emit_progress("质量评审完成", progress=0.8)
        
        # 4. 用例补全
        additional_cases = await run_test_completion(test_cases, review_report)
        await self._emit_progress("用例补全完成", progress=0.9)
        
        # 5. 合并结果
        final_result = merge_test_cases(test_cases, additional_cases)
        return final_result
```

## JSON 提取技巧

项目中的 `_extract_json` 函数：

```python
import json

def extract_json(content: str) -> dict:
    """从 LLM 回复中提取 JSON"""
    try:
        start = content.index("{")
        end = content.rfind("}") + 1
        json_str = content[start:end]
        return json.loads(json_str)
    except Exception as e:
        logger.error(f"JSON 提取失败: {e}")
        return {"error": "解析失败", "raw": content[:500]}
```

## 测试用例合并

项目中的 `_merge_test_cases` 函数：

```python
def merge_test_cases(base: dict, supplement: dict) -> dict:
    """合并基础测试用例和补充用例，去重"""
    merged = {"modules": []}
    
    for source in (base, supplement):
        for module in source.get("modules", []):
            existing_module = next(
                (m for m in merged["modules"] if m["name"] == module["name"]),
                None
            )
            
            if existing_module:
                # 合并到已有模块，去重
                existing_ids = {case["id"] for case in existing_module["cases"]}
                for case in module["cases"]:
                    if case["id"] not in existing_ids:
                        existing_module["cases"].append(case)
            else:
                # 新模块
                merged["modules"].append(module)
    
    return merged
```

## 流式输出（进阶）

从 `backend/app/llm/autogen_runner.py` 提取：

```python
from openai import OpenAI

def generate_streaming(system_message: str, prompt: str, on_chunk=None):
    """流式生成，逐块回调"""
    client = OpenAI(api_key="sk-xxx", base_url="https://...")
    
    stream = client.chat.completions.create(
        model="qwen-plus",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt},
        ],
        stream=True,
    )
    
    full_content = ""
    for chunk in stream:
        if chunk.choices[0].delta.content:
            text = chunk.choices[0].delta.content
            full_content += text
            if on_chunk:
                on_chunk(text)  # 实时回调
    
    return full_content

# 使用示例
def my_callback(text):
    print(text, end="", flush=True)

result = generate_streaming(
    system_message="你是测试工程师",
    prompt="生成测试用例",
    on_chunk=my_callback
)
```

## 最佳实践

### 1. 错误处理

```python
try:
    reply = agent.generate_reply(messages=[...])
    result = extract_json(reply)
except Exception as e:
    logger.error(f"智能体调用失败: {e}")
    result = {"error": str(e)}
```

### 2. 超时控制

```python
llm_config = {
    "config_list": [...],
    "timeout": 300,  # 复杂任务给足时间
}
```

### 3. 日志记录

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("开始需求分析...")
reply = agent.generate_reply(...)
logger.info(f"分析完成，结果长度: {len(reply)}")
```

## 下一步

📙 [进阶技巧与最佳实践](./04-advanced-tips.md)
