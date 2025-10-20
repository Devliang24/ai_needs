import { CheckCircleOutlined, EditOutlined } from '@ant-design/icons';
import { Button, Card, Empty, Input, Space, Spin, Typography } from 'antd';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import React, { useEffect, useMemo, useRef, useState } from 'react';

import { useAppStore } from '../stores/chatStore';
import type { AgentResult } from '../stores/chatStore';
import TestCasesView from './TestCasesView';
import QualityReviewView from './QualityReviewView';
import SupplementalTestCasesView from './SupplementalTestCasesView';

const isPlainObject = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value);

const toPlainText = (value: unknown): string => {
  if (value == null) return '';
  if (typeof value === 'string') return value;
  if (typeof value === 'number' || typeof value === 'boolean') return String(value);
  if (Array.isArray(value)) {
    return value
      .map((item) => toPlainText(item))
      .filter(Boolean)
      .join('；');
  }
  if (isPlainObject(value)) {
    const preferredKeys = ['description', 'detail', 'text', 'value', 'content', 'summary', 'name', 'title', 'label'];
    for (const key of preferredKeys) {
      if (value[key] != null) {
        const text = toPlainText(value[key]);
        if (text) return text;
      }
    }
    try {
      return JSON.stringify(value, null, 2);
    } catch {
      return String(value);
    }
  }
  return String(value);
};

const formatScenarioItem = (value: unknown): string | null => {
  if (value == null) return null;
  if (typeof value === 'string') return value;
  if (isPlainObject(value)) {
    const name = toPlainText(value.name ?? value.title ?? value.label ?? value.id);
    const description = toPlainText(value.description ?? value.detail ?? value.text ?? value.content ?? value.summary);
    if (name && description && name !== description) {
      return `${name}: ${description}`;
    }
    return name || description || null;
  }
  return toPlainText(value);
};

const buildRequirementMarkdownFromRecord = (data: Record<string, unknown>): string | null => {
  const sections: string[] = [];

  const overviewKeys = ['overview', 'summary', 'description', 'intro'];
  for (const key of overviewKeys) {
    const value = data[key];
    if (value != null) {
      const text = toPlainText(value);
      if (text) {
        sections.push(text);
        break;
      }
    }
  }

  const modulesRaw =
    data['modules'] ??
    data['module_list'] ??
    data['核心功能模块'] ??
    data['功能模块'] ??
    data['模块'];
  const modules = Array.isArray(modulesRaw) ? modulesRaw : [];
  const moduleSections = modules
    .map((module, index) => {
      if (!isPlainObject(module)) {
        const text = toPlainText(module);
        return text ? `### 模块 ${index + 1}: ${text}` : null;
      }

      const moduleObj = module as Record<string, unknown>;
      const moduleName =
        toPlainText(moduleObj['module'] ?? moduleObj['name'] ?? moduleObj['title'] ?? moduleObj['label']) ||
        `模块 ${index + 1}`;
      const lines: string[] = [`### 模块 ${index + 1}: ${moduleName}`];

      const scenariosRaw =
        moduleObj['scenarios'] ??
        moduleObj['scenes'] ??
        moduleObj['use_cases'] ??
        moduleObj['业务场景'] ??
        moduleObj['场景'];
      const scenarios = Array.isArray(scenariosRaw) ? scenariosRaw : [];
      const scenarioLines = scenarios
        .map((scenario) => {
          const text = formatScenarioItem(scenario);
          return text ? `- ${text}` : null;
        })
        .filter(Boolean) as string[];
      if (scenarioLines.length > 0) {
        lines.push('');
        lines.push('**业务场景**');
        lines.push(...scenarioLines);
      }

      const rulesRaw =
        moduleObj['rules'] ??
        moduleObj['business_rules'] ??
        moduleObj['regulations'] ??
        moduleObj['业务规则'] ??
        moduleObj['规则'];
      const rules = Array.isArray(rulesRaw) ? rulesRaw : [];
      const ruleLines = rules
        .map((rule) => {
          const text = formatScenarioItem(rule);
          return text ? `- ${text}` : null;
        })
        .filter(Boolean) as string[];
      if (ruleLines.length > 0) {
        lines.push('');
        lines.push('**业务规则**');
        lines.push(...ruleLines);
      }

      return lines.join('\n');
    })
    .filter(Boolean) as string[];

  if (moduleSections.length > 0) {
    sections.push(['## 核心功能模块', ...moduleSections].join('\n\n'));
  }

  const risksRaw =
    data['risks'] ??
    data['risk_points'] ??
    data['potential_risks'] ??
    data['风险'] ??
    data['风险点'];
  const risks = Array.isArray(risksRaw) ? risksRaw : [];
  const riskLines = risks
    .map((risk) => {
      const text = formatScenarioItem(risk);
      return text ? `- ${text}` : null;
    })
    .filter(Boolean) as string[];
  if (riskLines.length > 0) {
    sections.push(`## 风险点\n\n${riskLines.join('\n')}`);
  }

  if (sections.length === 0) {
    const fallbackLines = Object.entries(data)
      .map(([key, value]) => {
        if (Array.isArray(value) && value.length === 0) return null;
        const text = toPlainText(value);
        return text ? `- **${key}**: ${text}` : null;
      })
      .filter(Boolean) as string[];
    if (fallbackLines.length > 0) {
      sections.push(fallbackLines.join('\n'));
    }
  }

  const markdown = sections.join('\n\n').replace(/\n{3,}/g, '\n\n').trim();
  return markdown || null;
};

const tryParseJsonLike = (input: string): Record<string, unknown> | null => {
  try {
    const parsed = JSON.parse(input);
    return isPlainObject(parsed) ? parsed : null;
  } catch {
    const start = input.indexOf('{');
    const end = input.lastIndexOf('}');
    if (start >= 0 && end > start) {
      const snippet = input.slice(start, end + 1);
      try {
        const parsed = JSON.parse(snippet);
        return isPlainObject(parsed) ? parsed : null;
      } catch {
        return null;
      }
    }
    return null;
  }
};

const getRequirementMarkdown = (result: AgentResult): string | null => {
  if (result.payload && isPlainObject(result.payload)) {
    const markdown = buildRequirementMarkdownFromRecord(result.payload);
    if (markdown) return markdown;
  }

  if (typeof result.content === 'string') {
    const parsed = tryParseJsonLike(result.content);
    if (parsed) {
      const markdown = buildRequirementMarkdownFromRecord(parsed);
      if (markdown) return markdown;
    }
    return result.content.trim();
  }

  if (isPlainObject(result.content)) {
    const markdown = buildRequirementMarkdownFromRecord(result.content);
    if (markdown) return markdown;
  }

  return null;
};

const stageLabels: Record<string, string> = {
  layout_analysis: '版面分析',
  requirement_analysis: '需求分析',
  test_generation: '用例生成',
  test_completion: '用例补全',
  review: '质量评审',
  completed: '完成'
};

const EDITABLE_STAGES = new Set<string>(['layout_analysis', 'requirement_analysis']);

const AgentTimeline: React.FC = () => {
  const {
    agentResults,
    progress,
    selectedStage,
    currentStage,
    confirmAgentResult,
    updateAgentResult,
    sendConfirmation,
    analysisRunning
  } = useAppStore();
  const [editingResultId, setEditingResultId] = useState<string | null>(null);
  const [editContent, setEditContent] = useState<string>('');
  const endRef = useRef<HTMLDivElement | null>(null);

  // 根据选中的阶段过滤结果
  const filteredResults = useMemo(() => {
    if (!selectedStage) return agentResults;
    return agentResults.filter(result => result.stage === selectedStage);
  }, [agentResults, selectedStage]);

  const showStageLoading = useMemo(() => {
    if (!analysisRunning) return false;
    if (!selectedStage) return false;
    if (filteredResults.length > 0) return false;
    return selectedStage === currentStage;
  }, [analysisRunning, selectedStage, filteredResults.length, currentStage]);

  const handleConfirm = (resultId: string) => {
    const result = agentResults.find(r => r.id === resultId);
    if (result) {
      // 发送WebSocket确认消息
      sendConfirmation(resultId, result.stage, result.payload);
      // 更新本地状态
      confirmAgentResult(resultId);
    }
  };

  const handleStartEdit = (result: AgentResult) => {
    setEditingResultId(result.id);
    const isRequirementAnalysis = result.stage === 'requirement_analysis';
    const isLayoutAnalysis = result.stage === 'layout_analysis';
    const isGeneratedCasesStage =
      result.stage === 'test_generation' || result.stage === 'test_completion' || result.stage === 'completed';

    const defaultText = (() => {
      if (typeof result.content === 'string') return result.content;
      try {
        return JSON.stringify(result.content, null, 2);
      } catch {
        return String(result.content);
      }
    })();

    if (isRequirementAnalysis) {
      const markdown = getRequirementMarkdown(result);
      setEditContent(markdown || defaultText || '');
    } else if (isLayoutAnalysis) {
      setEditContent(defaultText || '');
    } else if (isGeneratedCasesStage) {
      // 测试用例编辑payload的JSON格式
      setEditContent(JSON.stringify(result.payload, null, 2));
    } else {
      const content = typeof result.content === 'string' ? result.content : JSON.stringify(result.content, null, 2);
      setEditContent(content);
    }
  };

  const handleSaveEdit = (resultId: string) => {
    const result = agentResults.find(r => r.id === resultId);
    if (result) {
      // 更新内容
      const nextPayload: Record<string, unknown> = {
        ...(result.payload ?? {}),
        editedContent: editContent
      };
      const shouldOverrideContent = EDITABLE_STAGES.has(result.stage);
      updateAgentResult(resultId, nextPayload, shouldOverrideContent ? editContent : undefined);
    }
    setEditingResultId(null);
    setEditContent('');
  };

  const handleCancelEdit = () => {
    setEditingResultId(null);
    setEditContent('');
  };

  const renderResultView = (result: AgentResult) => {
    if (!result.payload || Object.keys(result.payload).length === 0) {
      if (result.stage === 'requirement_analysis') {
        return null;
      }
      return <Typography.Text type="secondary">暂无数据</Typography.Text>;
    }

    // 根据不同的智能体阶段渲染不同的视图
    switch (result.stage) {
      case 'layout_analysis': {
        const documents = Array.isArray((result.payload as any)?.documents)
          ? ((result.payload as any).documents as Array<Record<string, unknown>>)
          : [];
        if (documents.length === 0) {
          return <Typography.Text type="secondary">暂无数据</Typography.Text>;
        }
        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {documents.map((doc, index) => {
              const entry = doc as Record<string, unknown>;
              const name = typeof entry['name'] === 'string' ? (entry['name'] as string) : `文档 ${index + 1}`;
              const charCount = typeof entry['char_count'] === 'number' ? (entry['char_count'] as number) : undefined;
              const lineCount = typeof entry['line_count'] === 'number' ? (entry['line_count'] as number) : undefined;
              const preview = typeof entry['preview'] === 'string' ? (entry['preview'] as string) : '';
              const documentId = typeof entry['document_id'] === 'string' ? (entry['document_id'] as string) : `${index}`;
              const source = entry['source'] === 'vl_model' ? 'VL 模型' : '文本提取';
              return (
                <div key={documentId} style={{ padding: 12, background: '#fafafa', borderRadius: 8 }}>
                  <Typography.Text strong style={{ display: 'block', marginBottom: 8 }}>
                    {name}
                  </Typography.Text>
                  <Typography.Paragraph style={{ marginBottom: 4 }}>
                    {charCount != null && (
                      <span style={{ marginRight: 16 }}>字符数：{charCount}</span>
                    )}
                    {lineCount != null && <span>有效段落数：{lineCount}</span>}
                    <span style={{ marginLeft: 16 }}>识别来源：{source}</span>
                  </Typography.Paragraph>
                  <Typography.Paragraph style={{ whiteSpace: 'pre-wrap', marginBottom: 0 }}>
                    {preview}
                  </Typography.Paragraph>
                </div>
              );
            })}
          </div>
        );
      }
      case 'requirement_analysis':
        // 需求分析师结果以 Markdown 内容为主，结构化视图不再显示
        return null;
      case 'test_generation':
        return <TestCasesView data={result.payload} />;
      case 'review':
        return <QualityReviewView data={result.payload} />;
      case 'test_completion':
        return <SupplementalTestCasesView data={result.payload} />;
      case 'completed':
        return <TestCasesView data={result.payload} title="最终合并的测试用例" emptyText="暂无测试用例" />;
      default:
        return (
          <pre style={{ background: '#f5f5f5', padding: 12, borderRadius: 4, maxHeight: 400, overflow: 'auto' }}>
            {JSON.stringify(result.payload, null, 2)}
          </pre>
        );
    }
  };

  const renderTimelineItem = (result: AgentResult) => {
    const isEditing = editingResultId === result.id;
    const defaultContent =
      typeof result.content === 'string'
        ? result.content
        : (() => {
            try {
              return JSON.stringify(result.content, null, 2);
            } catch {
              return String(result.content);
            }
          })();
    const isRequirementAnalysis = result.stage === 'requirement_analysis';
    const requirementMarkdown = isRequirementAnalysis ? getRequirementMarkdown(result) : null;
    const shouldRenderMarkdown = isRequirementAnalysis;
    const markdownContent = requirementMarkdown ?? defaultContent;
    const shouldRenderPlainText =
      !shouldRenderMarkdown &&
      result.stage !== 'layout_analysis' &&
      result.stage !== 'test_generation' &&
      result.stage !== 'review' &&
      result.stage !== 'test_completion' &&
      result.stage !== 'completed';
    const renderedContent = shouldRenderMarkdown ? markdownContent : defaultContent;

    return (
      <div key={result.id} style={{ marginBottom: 24 }}>
        {isEditing ? (
          // 编辑模式
          <div>
            <Input.TextArea
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
              autoSize={{ minRows: 10, maxRows: 30 }}
              style={{ marginBottom: 12, fontFamily: 'monospace' }}
            />
            <div
              style={{
                position: 'sticky',
                bottom: 0,
                background: '#fff',
                padding: '8px 0',
                textAlign: 'right',
                borderTop: '1px solid #f0f0f0',
                boxShadow: '0 -2px 8px rgba(0,0,0,0.04)',
                zIndex: 1
              }}
            >
              <Space>
                <Button type="primary" size="small" onClick={() => handleSaveEdit(result.id)}>
                  保存并重新分析
                </Button>
                <Button size="small" onClick={handleCancelEdit}>
                  取消
                </Button>
              </Space>
            </div>
          </div>
        ) : (
          // 显示模式
          <>
            {/* 移除每条记录内的编辑入口，仅保留卡片右上角的全局编辑 */}
              {shouldRenderMarkdown ? (
                <div className="markdown-body" style={{ lineHeight: 1.6 }}>
                  <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]}>
                    {renderedContent}
                  </ReactMarkdown>
                </div>
              ) : shouldRenderPlainText ? (
                <div style={{ whiteSpace: 'pre-wrap' }}>
                  {renderedContent}
                </div>
              ) : null}

            {/* 渲染专门的视图组件 */}
            {renderResultView(result)}
          </>
        )}
      </div>
    );
  };

  // 移除自动滚动功能
  // useEffect(() => {
  //   endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  // }, [filteredResults]);

  // 生成标题：显示为“<阶段>步骤结果预览”
  const cardTitle = useMemo(() => {
    const stageLabel = selectedStage ? (stageLabels[selectedStage] || selectedStage) : '';
    return stageLabel ? `${stageLabel}步骤结果预览` : '步骤结果预览';
  }, [selectedStage]);

  // 查找当前需要确认的结果
  const pendingConfirmation = useMemo(() => {
    return filteredResults.find(result => result.needsConfirmation && !result.confirmed);
  }, [filteredResults]);

  // 处于“需求分析”编辑态时隐藏滚动条（仅隐藏，不影响滚动能力）
  const isEditingEditableStage = useMemo(() => {
    return selectedStage != null && EDITABLE_STAGES.has(selectedStage) && editingResultId !== null;
  }, [selectedStage, editingResultId]);

  // 计算分析耗时
  const analysisDuration = useMemo(() => {
    if (filteredResults.length === 0) return null;

    const firstResult = filteredResults[0];
    const lastResult = filteredResults[filteredResults.length - 1];

    // 如果只有一个结果或进度未完成，返回null
    if (filteredResults.length === 1 || progress < 1.0) {
      return null;
    }

    const durationMs = lastResult.timestamp - firstResult.timestamp;
    const durationSec = Math.floor(durationMs / 1000);

    if (durationSec < 60) {
      return `${durationSec}秒`;
    } else {
      const minutes = Math.floor(durationSec / 60);
      const seconds = durationSec % 60;
      return `${minutes}分${seconds}秒`;
    }
  }, [filteredResults, progress]);

  // 卡片右侧操作按钮
  const cardExtra = useMemo(() => {
    // 在可编辑阶段，取最新一条记录用于全局编辑入口
    const isEditableStage = selectedStage != null && EDITABLE_STAGES.has(selectedStage);
    const latestEditable = isEditableStage && filteredResults.length > 0
      ? filteredResults[filteredResults.length - 1]
      : null;

    return (
      <Space>
        {/* 操作按钮 - completed 阶段不显示 */}
        {pendingConfirmation && pendingConfirmation.stage !== 'completed' && (
          <>
            <Button
              type="primary"
              size="small"
              icon={<CheckCircleOutlined />}
              onClick={() => handleConfirm(pendingConfirmation.id)}
            >
              确认,继续下一步
            </Button>
            {/* 只在可编辑阶段显示编辑按钮 */}
            {EDITABLE_STAGES.has(pendingConfirmation.stage) && (
              <Button
                size="small"
                icon={<EditOutlined />}
                onClick={() => handleStartEdit(pendingConfirmation)}
              >
                编辑
              </Button>
            )}
          </>
        )}

        {/* 可编辑阶段：在卡片右上角提供全局“编辑”入口 */}
        {!pendingConfirmation && latestEditable && (
          <Button
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleStartEdit(latestEditable)}
          >
            编辑
          </Button>
        )}
      </Space>
    );
  }, [pendingConfirmation, filteredResults, selectedStage]);

  return (
    <>
      <Card
        title={cardTitle}
        extra={cardExtra}
        bordered={false}
        style={{ height: '100%', width: '100%', display: 'flex', flexDirection: 'column' }}
        bodyStyle={{ flex: 1, minHeight: 0, overflow: 'hidden', padding: 0, display: 'flex', flexDirection: 'column' }}
      >
        <div style={{ display: 'flex', flex: 1, minHeight: 0 }}>
          <div
            className={isEditingEditableStage ? 'no-scrollbar' : undefined}
            style={{
              flex: 1,
              minHeight: 0,
              overflowY: filteredResults.length === 0 ? 'hidden' : 'auto',
              overflowX: 'hidden',
              padding: filteredResults.length === 0 ? '0 24px' : '24px',
              display: 'flex',
              alignItems: filteredResults.length === 0 ? 'center' : 'stretch',
              justifyContent: filteredResults.length === 0 ? 'center' : 'flex-start'
            }}
          >
            {filteredResults.length === 0 ? (
              showStageLoading ? (
                <Spin tip="分析中..." size="large" />
              ) : (
                <Empty description="该阶段暂无执行结果" image={Empty.PRESENTED_IMAGE_SIMPLE} />
              )
            ) : (
              <div style={{ width: '100%' }}>
                {filteredResults.map(renderTimelineItem)}
                <div ref={endRef} />
              </div>
            )}
          </div>
          {analysisDuration && filteredResults.length > 0 && (
            <div
              style={{
                width: 200,
                borderLeft: '1px solid #f0f0f0',
                padding: '24px 24px 24px 16px',
                display: 'flex',
                flexDirection: 'column',
                gap: 8
              }}
            >
              <Typography.Text type="secondary" style={{ fontSize: 14 }}>
                步骤耗时
              </Typography.Text>
              <Typography.Text style={{ fontSize: 20, fontWeight: 600 }}>
                {analysisDuration}
              </Typography.Text>
            </div>
          )}
        </div>
      </Card>
    </>
  );
};

export default AgentTimeline;
