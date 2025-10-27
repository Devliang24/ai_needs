# 进阶技巧与最佳实践

## 1. 多模态模型集成

### 视觉模型配置

项目使用 Qwen-VL 模型直接分析图片文档：

```python
# .env 配置
ANALYSIS_AGENT_MODEL=qwen3-vl-flash
ANALYSIS_MULTIMODAL_ENABLED=true

# 创建支持视觉的智能体
analyst = AssistantAgent(
    name="multimodal_analyst",
    system_message="你是需求分析师，可以理解图片内容",
    llm_config={
        "config_list": [{
            "model": "qwen3-vl-flash",  # VL 模型
            "api_key": "sk-xxx",
        }],
        "timeout": 180,
    },
)
```

### 多模态分析流程

从 `backend/app/llm/multimodal_client.py` 调用：

```python
async def analyze_with_multimodal(file_path: Path, api_key: str, model: str):
    """使用多模态模型直接分析图片"""
    # 实现细节见项目源码
    pass
```

## 2. 流式输出

### 为什么需要流式输出？

- ✅ 用户体验好：逐字显示，实时反馈
- ✅ 降低感知延迟：不用等全部生成完
- ✅ 便于进度展示

### 实现方式

从 `backend/app/llm/autogen_runner.py` 提取：

```python
from openai import OpenAI

def generate_streaming(system_message: str, prompt: str, on_chunk=None) -> str:
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
            
            # 实时回调
            if on_chunk:
                on_chunk(text)
    
    return full_content
```

### 使用示例

```python
def print_chunk(text):
    print(text, end="", flush=True)

result = generate_streaming(
    system_message="你是测试工程师",
    prompt="生成测试用例",
    on_chunk=print_chunk
)
```

## 3. 人工确认机制（Human-in-the-Loop）

### 工作流中的确认点

从 `backend/app/orchestrator/workflow.py` 提取：

```python
async def _wait_for_confirmation(self, stage: str, timeout: int = 300) -> bool:
    """等待用户确认当前阶段"""
    
    # 清除旧确认数据
    await session_events.clear_confirmation(self.session_id)
    
    # 轮询等待
    for _ in range(timeout):
        await asyncio.sleep(1)
        
        confirmation = await session_events.get_confirmation(self.session_id)
        if confirmation and confirmation.get("stage") == stage:
            if confirmation.get("confirmed"):
                return True
            elif confirmation.get("rejected"):
                return False
    
    # 超时
    return False
```

### 在工作流中使用

```python
# 执行智能体任务
result = await run_requirement_analysis(docs)

# 等待人工确认
confirmed = await self._wait_for_confirmation("requirement_analysis")
if not confirmed:
    raise RuntimeError("用户拒绝确认")

# 继续下一步
test_cases = await run_test_generation(result)
```

## 4. 智能体专用模型配置

### 为什么要用不同模型？

| 任务类型 | 模型选择 | 原因 |
|---------|---------|------|
| 图片分析 | qwen3-vl-flash | 视觉理解能力 |
| 深度推理 | qwen3-next-80b | 强推理能力 |
| 简单任务 | qwen-plus | 成本优化 |

### 配置示例

```bash
# .env 配置
ANALYSIS_AGENT_MODEL=qwen3-vl-flash
TEST_AGENT_MODEL=qwen3-next-80b-a3b-instruct
REVIEW_AGENT_MODEL=qwen3-next-80b-a3b-instruct
```

### 代码实现

从 `backend/app/config.py` 和 `backend/app/llm/autogen_runner.py`：

```python
def get_agent_config(agent_type: str) -> dict:
    """根据智能体类型返回专用配置"""
    if agent_type == "analysis":
        return {
            "model": settings.analysis_agent_model,
            "api_key": settings.analysis_agent_api_key or settings.qwen_api_key,
            "base_url": settings.analysis_agent_base_url or settings.qwen_base_url,
        }
    elif agent_type == "test":
        return {
            "model": settings.test_agent_model,
            "api_key": settings.test_agent_api_key or settings.qwen_api_key,
            "base_url": settings.test_agent_base_url or settings.qwen_base_url,
        }
    # ...
```

## 5. WebSocket 实时推送

### 推送进度更新

从 `backend/app/websocket/manager.py`：

```python
class ConnectionManager:
    async def broadcast(self, session_id: str, message: dict):
        """向指定会话的所有客户端广播消息"""
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id]:
                await connection.send_json(message)

# 使用示例
await manager.broadcast(session_id, {
    "type": "agent_message",
    "sender": "需求分析师",
    "content": analysis_result,
    "progress": 0.3,
})
```

## 6. 错误处理与重试

### 异常捕获

```python
try:
    reply = agent.generate_reply(messages=[...])
    result = extract_json(reply)
except TimeoutError:
    logger.error("请求超时")
    result = {"error": "timeout"}
except json.JSONDecodeError:
    logger.error("JSON 解析失败")
    result = {"error": "invalid_json", "raw": reply[:200]}
except Exception as e:
    logger.error(f"未知错误: {e}")
    result = {"error": str(e)}
```

### 重试策略

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def call_agent_with_retry(agent, prompt):
    return agent.generate_reply(messages=[{"role": "user", "content": prompt}])
```

## 7. 性能优化

### 1. 并行执行（慎用）

```python
import asyncio

# 可以并行执行的任务
results = await asyncio.gather(
    run_simple_task_1(),
    run_simple_task_2(),
)

# 注意：智能体协作通常需要串行执行（后一个依赖前一个结果）
```

### 2. 结果缓存

```python
import hashlib
import json

def cache_key(prompt: str) -> str:
    return hashlib.sha256(prompt.encode()).hexdigest()

# 检查缓存
key = cache_key(prompt)
if key in cache:
    return cache[key]

# 调用智能体
result = agent.generate_reply(...)
cache[key] = result
return result
```

### 3. 超时分级

```python
# 简单任务
simple_config = {"timeout": 60}

# 中等任务
medium_config = {"timeout": 120}

# 复杂任务
complex_config = {"timeout": 300}
```

## 8. 测试与调试

### 单元测试

```python
import pytest

def test_requirement_analysis():
    result = run_requirement_analysis([{
        "content": "用户登录功能"
    }])
    
    assert "modules" in result
    assert len(result["modules"]) > 0
```

### 日志调试

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.info("开始调用智能体...")
```

## 9. 生产环境检查清单

- [ ] 环境变量安全配置（不要硬编码密钥）
- [ ] 错误处理和降级方案
- [ ] 超时配置合理
- [ ] 日志记录完整
- [ ] 敏感信息脱敏
- [ ] 资源限制（并发数、内存等）
- [ ] 监控和告警
- [ ] 测试覆盖

## 10. 常见问题

### Q: 如何处理超长文档？

```python
# 分块处理
def chunk_document(content: str, max_length: int = 8000):
    chunks = []
    for i in range(0, len(content), max_length):
        chunks.append(content[i:i+max_length])
    return chunks

# 逐块分析后合并
results = []
for chunk in chunk_document(long_doc):
    result = agent.generate_reply(...)
    results.append(result)
```

### Q: 如何减少 API 调用成本？

1. 使用缓存（相同输入返回缓存结果）
2. 选择合适的模型（简单任务用小模型）
3. 优化提示词（减少冗余描述）
4. 批量处理（一次处理多个任务）

### Q: 如何提高输出质量？

1. 优化 system_message（明确任务和约束）
2. 提供示例（few-shot learning）
3. 降低 temperature（0.1-0.7）
4. 增加验证步骤（质量评审智能体）
5. 使用更强的模型（如 qwen3-next-80b）

## 总结

本指南涵盖了 AutoGen 的核心概念和项目实战，现在你应该能够：

- ✅ 配置和创建各种智能体
- ✅ 设计多智能体协作工作流
- ✅ 集成多模态模型
- ✅ 实现流式输出和人工确认
- ✅ 应用生产级最佳实践

## 参考资源

- [AutoGen 官方文档](https://microsoft.github.io/autogen/)
- [项目源码](../../backend/app/llm/autogen_runner.py)
- [工作流编排](../../backend/app/orchestrator/workflow.py)

---

**继续探索？** 查看项目源码，尝试修改和优化工作流！
