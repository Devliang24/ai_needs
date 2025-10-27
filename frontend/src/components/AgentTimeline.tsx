import { CheckCircleOutlined } from '@ant-design/icons';
import { Button, Card, Empty, Spin, Typography } from 'antd';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import React, { useEffect, useMemo, useRef, useState } from 'react';

import { useAppStore } from '../stores/chatStore';
import type { AgentResult } from '../stores/chatStore';
import TestCasesView from './TestCasesView';
import { useMediaQuery } from '../hooks/useMediaQuery';

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

const formatDurationSeconds = (seconds: number): string => {
  if (!Number.isFinite(seconds)) {
    return '0秒';
  }
  const value = Math.max(0, seconds);
  const trim = (num: number, fractionDigits: number) => {
    const fixed = num.toFixed(fractionDigits);
    return parseFloat(fixed).toString();
  };

  if (value < 1) {
    return `${trim(value, 2)}秒`;
  }

  if (value < 60) {
    const digits = value < 10 ? 2 : 1;
    return `${trim(value, digits)}秒`;
  }

  const minutes = Math.floor(value / 60);
  const remainder = value - minutes * 60;
  if (remainder < 0.01) {
    return `${minutes}分`;
  }
  const digits = remainder < 10 ? 2 : 1;
  return `${minutes}分${trim(remainder, digits)}秒`;
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
  requirement_analysis: '需求分析',
  test_generation: '用例生成',
  test_completion: '用例补全',
  review: '质量评审',
  completed: '合并用例'
};

const STAGE_SEQUENCE = [
  'requirement_analysis',
  'test_generation',
  'review',
  'test_completion',
  'completed'
] as const;

const AgentTimeline: React.FC = () => {
  const {
    agentResults,
    progress,
    selectedStage,
    currentStage,
    confirmAgentResult,
    sendConfirmation,
    analysisRunning,
    setSelectedStage,
    setProgress,
    updateActivityTime
  } = useAppStore();
  const [pendingStage, setPendingStage] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement | null>(null);
  const isMobile = useMediaQuery('(max-width: 767px)');

  // 根据选中的阶段过滤结果
  const filteredResults = useMemo(() => {
    if (!selectedStage) return agentResults;
    return agentResults.filter(result => result.stage === selectedStage);
  }, [agentResults, selectedStage]);

  const showStageLoading = useMemo(() => {
    if (!analysisRunning) return false;

    if (!selectedStage) {
      // 若未选择具体阶段且仍在分析，默认显示加载
      return filteredResults.length === 0 && agentResults.length === 0;
    }

    // 优先检查：如果当前阶段正在等待（pendingStage），始终显示加载
    if (pendingStage === selectedStage) {
      return true;
    }

    // 如果选中的阶段已经有结果，不再显示加载（无论当前执行到哪个阶段）
    if (filteredResults.length > 0) {
      const lastResult = filteredResults[filteredResults.length - 1];
      // 只有当结果还在流式更新中（未完成）时才显示加载
      return !lastResult.needsConfirmation;
    }

    const selectedIndex = STAGE_SEQUENCE.indexOf(selectedStage as typeof STAGE_SEQUENCE[number]);
    const currentIndex = currentStage ? STAGE_SEQUENCE.indexOf(currentStage as typeof STAGE_SEQUENCE[number]) : -1;

    const hasAnyResult = agentResults.length > 0;
    const isCurrentStageRunning = selectedStage === currentStage;
    const isInitialRequirementAnalysis =
      selectedStage === 'requirement_analysis' && (!currentStage || currentStage === 'requirement_analysis');
    const isFutureStageRunning = currentIndex >= 0 && selectedIndex > currentIndex;
    const isAwaitingFirstStage = !hasAnyResult && selectedIndex === 0;

    return (
      isCurrentStageRunning ||
      isInitialRequirementAnalysis ||
      isFutureStageRunning ||
      isAwaitingFirstStage ||
      (!hasAnyResult && analysisRunning)
    );
  }, [analysisRunning, agentResults.length, selectedStage, filteredResults, currentStage, pendingStage]);

  const handleConfirm = (resultId: string) => {
    const result = agentResults.find(r => r.id === resultId);
    if (result) {
      // 更新用户活动时间
      updateActivityTime();

      // 发送WebSocket确认消息
      sendConfirmation(resultId, result.stage, result.payload);
      // 更新本地状态
      confirmAgentResult(resultId);

      // 乐观切换到下一个阶段，显示加载态并高亮步骤
      const currentStageIndex = STAGE_SEQUENCE.findIndex(stage => stage === result.stage);
      if (currentStageIndex >= 0 && currentStageIndex < STAGE_SEQUENCE.length - 1) {
        const nextStage = STAGE_SEQUENCE[currentStageIndex + 1];
        setSelectedStage(nextStage);
        setProgress(progress, nextStage);
        setPendingStage(nextStage);
      }
    }
  };

  useEffect(() => {
    if (!selectedStage) return;
    // 只有当选中阶段有结果时，才清空 pendingStage
    if (filteredResults.length > 0) {
      setPendingStage((prev) => (prev === selectedStage ? null : prev));
    }
    // 移除 else if 分支，避免过早清空 pendingStage
  }, [selectedStage, filteredResults.length]);

  const renderResultView = (result: AgentResult) => {
    const hasTextContent = typeof result.content === 'string' && result.content.trim().length > 0;
    const hasPayload = !!(result.payload && Object.keys(result.payload).length > 0);

    if (!hasPayload && !hasTextContent) {
      if (result.stage === 'requirement_analysis') {
        return null;
      }
      return <Typography.Text type="secondary">暂无数据</Typography.Text>;
    }

    // 根据不同的智能体阶段渲染不同的视图
    switch (result.stage) {
      case 'test_generation':
        // 用例生成阶段使用表格视图
        if (hasPayload && result.payload && typeof result.payload === 'object') {
          return <TestCasesView data={result.payload} title="测试用例" emptyText="暂无测试用例" />;
        }
        return null;

      case 'test_completion':
        // 用例补全阶段使用表格视图
        if (hasPayload && result.payload && typeof result.payload === 'object') {
          return <TestCasesView data={result.payload} title="补充测试用例" emptyText="暂无补充测试用例" />;
        }
        return null;

      case 'review':
        // 质量评审阶段使用结构化卡片视图
        if (hasPayload && result.payload && typeof result.payload === 'object') {
          return <ReviewView data={result.payload} />;
        }
        // 如果解析失败，降级显示Markdown渲染的完整内容
        if (hasTextContent) {
          return (
            <div className="markdown-body" style={{ padding: '0 16px' }}>
              <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]}>
                {String(result.content)}
              </ReactMarkdown>
            </div>
          );
        }
        return null;

      case 'completed':
        // completed阶段使用表格视图展示合并的测试用例
        if (hasPayload && result.payload && typeof result.payload === 'object') {
          return <TestCasesView data={result.payload} title="测试用例（合并）" emptyText="暂无测试用例" />;
        }
        return null;

      case 'requirement_analysis':
        // 需求分析阶段通过 Markdown 预览展示
        return null;

      default:
        return (
          <pre style={{ background: '#f5f5f5', padding: 12, borderRadius: 4, maxHeight: 400, overflow: 'auto' }}>
            {JSON.stringify(result.payload, null, 2)}
          </pre>
        );
    }
  };

  const renderTimelineItem = (result: AgentResult, index: number, total: number) => {
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

    // 只有requirement_analysis阶段使用Markdown，其他阶段使用结构化组件
    const markdownStages = ['requirement_analysis'];

    const isRequirementAnalysis = result.stage === 'requirement_analysis';
    const requirementMarkdown = isRequirementAnalysis ? getRequirementMarkdown(result) : null;

    const candidateMarkdown = requirementMarkdown ?? defaultContent;
    let normalizedMarkdown =
      typeof candidateMarkdown === 'string' ? candidateMarkdown.trim() : String(candidateMarkdown);
    // 移除底部耗时信息（如果存在）
    normalizedMarkdown = normalizedMarkdown.replace(/>\s*\*\*耗时[：:].*?秒\*\*/g, '').trim();
    const shouldRenderMarkdown = markdownStages.includes(result.stage) && normalizedMarkdown.length > 0;

    const hasPlainText = typeof defaultContent === 'string' && defaultContent.trim().length > 0;
    const shouldRenderPlainText =
      !shouldRenderMarkdown &&
      hasPlainText &&
      result.stage !== 'test_generation' &&
      result.stage !== 'review' &&
      result.stage !== 'test_completion' &&
      result.stage !== 'completed';

    const isSingleResult = total === 1;
    const itemStyle: React.CSSProperties = {
      marginBottom: index === total - 1 ? 0 : 24,
      display: 'flex',
      flexDirection: 'column',
      flex: isSingleResult ? 1 : undefined,
      minHeight: isSingleResult ? '100%' : undefined
    };

    return (
      <div key={result.id} style={itemStyle}>
        {shouldRenderMarkdown ? (
          <div
            className="markdown-body"
            style={{
              flex: 1,
              minHeight: 0,
              borderRadius: 4,
              padding: '0 16px',
              overflow: 'visible'
            }}
          >
            <MarkdownPreview content={normalizedMarkdown} />
          </div>
        ) : shouldRenderPlainText ? (
          <div style={{ whiteSpace: 'pre-wrap', flex: 1 }}>{defaultContent}</div>
        ) : null}

        {/* 渲染专门的视图组件（非流式阶段）*/}
        {!shouldRenderMarkdown && renderResultView(result)}
      </div>
    );
  };

  // 移除自动滚动功能
  // useEffect(() => {
  //   endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  // }, [filteredResults]);

  // 计算阶段耗时
  const stageDurationSeconds = useMemo(() => {
    for (let i = filteredResults.length - 1; i >= 0; i -= 1) {
      const candidate = filteredResults[i].durationSeconds;
      if (typeof candidate === 'number' && Number.isFinite(candidate)) {
        return candidate;
      }
    }
    return null;
  }, [filteredResults]);

  const fallbackDurationText = useMemo(() => {
    if (stageDurationSeconds != null) return null;
    if (filteredResults.length === 0) return null;

    let earliestStart = Number.POSITIVE_INFINITY;
    let latestEnd = 0;

    for (const result of filteredResults) {
      const start = typeof result.startedAt === 'number' ? result.startedAt : result.timestamp;
      if (start < earliestStart) {
        earliestStart = start;
      }
      if (result.timestamp > latestEnd) {
        latestEnd = result.timestamp;
      }
    }

    if (!Number.isFinite(earliestStart) || latestEnd < earliestStart) {
      return null;
    }

    const durationMs = latestEnd - earliestStart;
    const durationSec = durationMs / 1000;
    if (durationSec <= 0) {
      return '<1秒';
    }
    return formatDurationSeconds(durationSec);
  }, [filteredResults, stageDurationSeconds]);

  const stageDurationText = useMemo(() => {
    if (stageDurationSeconds != null) {
      return formatDurationSeconds(stageDurationSeconds);
    }
    return fallbackDurationText;
  }, [stageDurationSeconds, fallbackDurationText]);

  // 生成标题：显示为"<阶段>步骤结果预览"
  const cardTitle = useMemo(() => {
    const stageLabel = selectedStage ? (stageLabels[selectedStage] || selectedStage) : '';
    const baseTitle = stageLabel ? `${stageLabel}步骤结果预览` : '步骤结果预览';
    return baseTitle;
  }, [selectedStage]);

  // 查找当前需要确认的结果
  const pendingConfirmation = useMemo(() => {
    return filteredResults.find(result => result.needsConfirmation && !result.confirmed);
  }, [filteredResults]);

  // 卡片右侧操作按钮
  const cardExtra = useMemo(() => {
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: isMobile ? 8 : 12 }}>
        {stageDurationText && !isMobile && (
          <Typography.Text type="secondary" style={{ fontSize: 14 }}>
            耗时: {stageDurationText}
          </Typography.Text>
        )}
        {pendingConfirmation && pendingConfirmation.stage !== 'completed' && (
          <Button
            type="primary"
            size={isMobile ? 'middle' : 'small'}
            icon={<CheckCircleOutlined />}
            onClick={() => handleConfirm(pendingConfirmation.id)}
          >
            {isMobile ? '下一步' : '确认,继续下一步'}
          </Button>
        )}
      </div>
    );
  }, [pendingConfirmation, stageDurationText, isMobile]);

  return (
    <>
      <Card
        title={cardTitle}
        extra={cardExtra}
        bordered={false}
        style={{ height: '100%', width: '100%', display: 'flex', flexDirection: 'column' }}
        bodyStyle={{ flex: 1, minHeight: 0, overflow: 'hidden', padding: 0, display: 'flex', flexDirection: 'column' }}
        headStyle={{ padding: isMobile ? '12px 16px' : undefined }}
      >
        <div
          style={{
            flex: 1,
            minHeight: 0,
            overflowY: filteredResults.length === 0 ? 'hidden' : 'auto',
            overflowX: 'hidden',
            padding: isMobile ? '0 12px' : '0 24px',
            display: 'flex',
            alignItems: filteredResults.length === 0 ? 'center' : 'stretch',
            justifyContent: filteredResults.length === 0 ? 'center' : 'flex-start',
            background: '#fafafa'
          }}
        >
          {filteredResults.length === 0 ? (
            showStageLoading ? (
              <Spin tip="分析中..." size="large" />
            ) : (
              <Empty description="该阶段暂无执行结果" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            )
          ) : (
            <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
              {filteredResults.map((result, index) => renderTimelineItem(result, index, filteredResults.length))}
              {/* 如果有结果但仍在加载中，显示底部加载提示 */}
              {showStageLoading && (
                <div style={{ display: 'flex', justifyContent: 'center', padding: '24px 0' }}>
                  <Spin tip="继续分析中..." />
                </div>
              )}
              <div ref={endRef} />
            </div>
          )}
        </div>
      </Card>
    </>
  );
};

export default AgentTimeline;

const MarkdownPreview = React.memo(({ content }: { content: string }) => (
  <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]}>
    {content}
  </ReactMarkdown>
));

MarkdownPreview.displayName = 'MarkdownPreview';

// 质量评审结构化视图组件
const ReviewView: React.FC<{ data: Record<string, unknown> }> = ({ data }) => {
  const summary = typeof data.summary === 'string' ? data.summary : '';
  const defects = Array.isArray(data.defects) ? data.defects : [];
  const suggestions = Array.isArray(data.suggestions) ? data.suggestions : [];

  const hasContent = summary || defects.length > 0 || suggestions.length > 0;

  if (!hasContent) {
    return <Typography.Text type="secondary">暂无评审数据</Typography.Text>;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {summary && (
        <Card
          size="small"
          title="评审摘要"
          style={{ background: '#fff', border: '1px solid #e8e8e8' }}
        >
          {/* 使用ReactMarkdown渲染摘要，支持加粗、列表等格式 */}
          <div className="markdown-body" style={{ fontSize: 14 }}>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {summary}
            </ReactMarkdown>
          </div>
        </Card>
      )}

      {defects.length > 0 && (
        <Card
          size="small"
          title={`发现的缺陷 (${defects.length})`}
          style={{ background: '#fff', border: '1px solid #e8e8e8' }}
        >
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            {defects.map((item, index) => (
              <li key={index} style={{ marginBottom: 8 }}>
                {/* 每个列表项也支持Markdown渲染 */}
                <div className="markdown-body" style={{ fontSize: 14, display: 'inline' }}>
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {String(item)}
                  </ReactMarkdown>
                </div>
              </li>
            ))}
          </ul>
        </Card>
      )}

      {suggestions.length > 0 && (
        <Card
          size="small"
          title={`改进建议 (${suggestions.length})`}
          style={{ background: '#fff', border: '1px solid #e8e8e8' }}
        >
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            {suggestions.map((item, index) => (
              <li key={index} style={{ marginBottom: 8 }}>
                {/* 每个列表项也支持Markdown渲染 */}
                <div className="markdown-body" style={{ fontSize: 14, display: 'inline' }}>
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {String(item)}
                  </ReactMarkdown>
                </div>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
};
