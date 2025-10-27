# AutoGen 学习指南

欢迎来到 AutoGen 多智能体框架学习之旅！本指南基于真实项目实战，帮助你从零开始掌握 AutoGen。

## 📖 学习路径

### 新手入门（3-4小时）

1. **[快速入门](./01-quickstart.md)** ⏱️ 30分钟
   - AutoGen 是什么
   - 环境配置
   - 第一个智能体程序

2. **[智能体配置详解](./02-agent-configuration.md)** ⏱️ 1小时
   - AssistantAgent 参数详解
   - llm_config 配置技巧
   - system_message 编写实战

3. **[多智能体协作实战](./03-multi-agent-workflow.md)** ⏱️ 2小时
   - 智能体对话机制
   - 工作流编排
   - 真实项目案例：需求分析流程

### 进阶应用（2-3小时）

4. **[进阶技巧与最佳实践](./04-advanced-tips.md)** ⏱️ 2小时
   - 多模态模型集成
   - 流式输出
   - 人工确认机制
   - 性能优化

## 🎯 学习目标

完成本指南后，你将能够：

- ✅ 理解 AutoGen 的核心概念和设计理念
- ✅ 独立配置和创建各种类型的智能体
- ✅ 设计并实现多智能体协作工作流
- ✅ 集成到生产环境，处理真实业务场景

## 💡 学习建议

1. **边学边做**：每个章节都包含可运行的代码示例
2. **理解原理**：不要死记硬背参数，理解背后的设计思想
3. **参考项目代码**：文档中的示例都来自 `/backend/app/llm/autogen_runner.py` 和 `/backend/app/orchestrator/workflow.py`
4. **动手实验**：尝试修改参数，观察输出变化

## 📚 项目实战案例

本指南基于 **AI 需求分析平台** 项目，该项目使用 AutoGen 实现了：

- 📄 **需求分析师**：分析需求文档，提取功能模块和业务规则
- 🧪 **测试工程师**：根据需求生成测试用例
- 🔍 **质量评审专家**：评审测试用例的完整性
- ✏️ **测试补全工程师**：补充缺失的测试用例

## 🔗 相关资源

- [AutoGen 官方文档](https://microsoft.github.io/autogen/)
- [项目源码](../../backend/app/llm/autogen_runner.py)
- [工作流编排](../../backend/app/orchestrator/workflow.py)

---

**准备好了吗？让我们从 [快速入门](./01-quickstart.md) 开始！** 🚀
