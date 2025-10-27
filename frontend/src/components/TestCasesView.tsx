import { Table, Tag, Typography } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import React from 'react';
import { useMediaQuery } from '../hooks/useMediaQuery';

const { Text } = Typography;

interface TestCase {
  id: string;
  title: string;
  preconditions?: unknown;
  steps?: unknown[];
  expected?: unknown;
  priority?: string;
}

interface TestModule {
  name: string;
  cases: TestCase[];
}

interface TestCasesData {
  modules?: TestModule[];
}

interface Props {
  data: Record<string, unknown>;
  title?: string;
  emptyText?: string;
}

const priorityColors: Record<string, string> = {
  P0: 'red',
  P1: 'orange',
  P2: 'blue',
  P3: 'green'
};

const TestCasesView: React.FC<Props> = ({ data, title = '测试用例', emptyText = '暂无测试用例' }) => {
  const testData = data as TestCasesData;
  const isMobile = useMediaQuery('(max-width: 767px)');

  // 检测JSON解析错误的情况
  const hasError = !!(data as any)?.error;
  const errorMessage = hasError ? (data as any).error : null;
  const rawResponse = hasError ? (data as any).raw_response : null;

  const modulesRaw = testData.modules;
  const modules: unknown[] = Array.isArray(modulesRaw) ? modulesRaw : [];

  // 调试日志：记录接收到的payload结构
  if (typeof console !== 'undefined' && console.log) {
    console.log('[TestCasesView] 接收到的数据:', {
      hasError,
      errorMessage,
      modulesCount: modules.length,
      dataKeys: Object.keys(data),
      firstModuleKeys: modules[0] ? Object.keys(modules[0]) : null
    });
  }

  const normalizeText = (value: unknown): string => {
    if (value == null) return '';
    if (typeof value === 'string') {
      return value.replace(/<br\s*\/?>/gi, '\n').replace(/\r\n/g, '\n').replace(/\u00a0/g, ' ').trim();
    }
    if (typeof value === 'number' || typeof value === 'boolean') return String(value);
    try {
      return JSON.stringify(value);
    } catch {
      return String(value);
    }
  };

  const renderTextBlock = (text: string) => {
    if (!text) return '-';
    return <div style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{text}</div>;
  };

  const renderListItems = (items: unknown[]) => {
    return (
      <ol style={{ margin: 0, paddingLeft: 20 }}>
        {items.map((item, index) => {
          const content = normalizeText(item);
          return (
            <li key={index} style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
              {content || '-'}
            </li>
          );
        })}
      </ol>
    );
  };

  const ensureArray = (value: unknown): unknown[] | undefined => {
    if (value == null) return undefined;
    if (Array.isArray(value)) return value;
    return [value];
  };

  const columns: ColumnsType<TestCase> = [
    {
      title: '用例ID',
      dataIndex: 'id',
      key: 'id',
      width: 100,
      render: (id: string) => id
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: 80,
      render: (priority: string) => priority || 'N/A',
      sorter: (a, b) => (a.priority || '').localeCompare(b.priority || '')
    },
    {
      title: '用例标题',
      dataIndex: 'title',
      key: 'title',
      width: 200,
      render: (title: string) => <Text strong>{title}</Text>
    },
    {
      title: '前置条件',
      dataIndex: 'preconditions',
      key: 'preconditions',
      width: 200,
      render: (preconditions: unknown) => {
        // 如果是数组，显示为有序列表
        const entries = ensureArray(preconditions) ?? [];
        if (entries.length === 0) {
          return '-';
        }
        if (entries.length === 1) {
          return renderTextBlock(normalizeText(entries[0]));
        }
        return renderListItems(entries);
      }
    },
    {
      title: '测试步骤',
      dataIndex: 'steps',
      key: 'steps',
      width: 350,
      render: (steps: unknown) => {
        const entries = ensureArray(steps) ?? [];
        if (entries.length === 0) {
          return '-';
        }
        if (entries.length === 1) {
          return renderTextBlock(normalizeText(entries[0]));
        }
        return renderListItems(entries);
      }
    },
    {
      title: '预期结果',
      dataIndex: 'expected',
      key: 'expected',
      width: 400,
      render: (expected: unknown) => {
        const entries = ensureArray(expected) ?? [];
        if (entries.length === 0) {
          return '-';
        }
        if (entries.length === 1) {
          return renderTextBlock(normalizeText(entries[0]));
        }
        return renderListItems(entries);
      }
    }
  ];

  return (
    <div>
      {/* 显示JSON解析错误信息 */}
      {hasError && (
        <div style={{ marginBottom: 16, padding: 16, background: '#fff2e8', border: '1px solid #ffbb96', borderRadius: 4 }}>
          <Typography.Text type="warning" strong style={{ display: 'block', marginBottom: 8 }}>
            ⚠️ 测试用例生成失败
          </Typography.Text>
          <Typography.Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>
            {errorMessage}
          </Typography.Text>
          {rawResponse && (
            <details style={{ marginTop: 8 }}>
              <summary style={{ cursor: 'pointer', color: '#8c8c8c' }}>查看原始响应（用于调试）</summary>
              <pre style={{ marginTop: 8, padding: 8, background: '#fafafa', border: '1px solid #d9d9d9', borderRadius: 4, fontSize: 12, maxHeight: 200, overflow: 'auto' }}>
                {rawResponse}
              </pre>
            </details>
          )}
        </div>
      )}

      {modules.map((module, index) => {
        if (!module || typeof module !== 'object' || Array.isArray(module)) {
          const fallbackText = normalizeText(module);
          if (!fallbackText) {
            return null;
          }
          return (
            <div key={index} style={{ marginBottom: 24 }}>
              <Typography.Title level={5}>
                <Tag color="green">模块</Tag>
                模块 {index + 1}
              </Typography.Title>
              <Text type="secondary">{fallbackText}</Text>
            </div>
          );
        }

        const moduleRecord = module as Record<string, unknown>;
        const moduleName =
          normalizeText(moduleRecord.name) ||
          normalizeText(moduleRecord.module) ||
          normalizeText(moduleRecord.title) ||
          `模块 ${index + 1}`;
        const rawCases = Array.isArray(moduleRecord.cases) ? moduleRecord.cases : [];
        const cases = rawCases.map((testCase, caseIndex) => {
          if (!testCase || typeof testCase !== 'object' || Array.isArray(testCase)) {
            const fallbackCaseText = normalizeText(testCase) || `测试用例 ${caseIndex + 1}`;
            return {
              id: `TC-${index + 1}-${caseIndex + 1}`,
              title: fallbackCaseText,
              preconditions: undefined,
              steps: undefined,
              expected: undefined,
              priority: undefined
            } as TestCase;
          }

          const caseObj = testCase as Record<string, unknown>;
          const id =
            normalizeText(caseObj.id) ||
            normalizeText(caseObj.caseId) ||
            normalizeText(caseObj.case_id) ||
            `TC-${index + 1}-${caseIndex + 1}`;
          const title =
            normalizeText(caseObj.title) ||
            normalizeText(caseObj.name) ||
            normalizeText(caseObj.summary) ||
            `测试用例 ${caseIndex + 1}`;

          const preconditions = ensureArray(caseObj.preconditions);
          const steps = ensureArray(caseObj.steps);
          const expected = caseObj.expected ?? caseObj.expectation ?? caseObj.result ?? caseObj.outcome;
          const priorityRaw = normalizeText(caseObj.priority ?? caseObj.level ?? caseObj.rank ?? '');
          const priority = priorityRaw ? priorityRaw.toUpperCase() : undefined;

          return {
            id,
            title,
            preconditions,
            steps,
            expected,
            priority
          } as TestCase;
        });

        return (
          <div key={index} style={{ marginBottom: 24 }}>
            <Typography.Title level={5}>
              <Tag color="green">模块</Tag>
              {moduleName}
              <Text type="secondary" style={{ marginLeft: 8, fontSize: 14, fontWeight: 'normal' }}>
                ({cases.length} 个用例)
              </Text>
            </Typography.Title>

            <div style={{
              overflowX: 'auto',
              WebkitOverflowScrolling: 'touch'
            }}>
              <Table
                columns={columns}
                dataSource={cases}
                rowKey="id"
                pagination={{ pageSize: 10 }}
                size="small"
                bordered
                scroll={{ x: isMobile ? 'max-content' : undefined }}
              />
            </div>
          </div>
        );
      })}

      {modules.length === 0 && (
        <Text type="secondary">{emptyText}</Text>
      )}

    </div>
  );
};

export default TestCasesView;
