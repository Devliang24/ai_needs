import { Table, Tag, Typography } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import React from 'react';

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
  const modules = testData.modules || [];

  const toText = (value: unknown): string => {
    if (value == null) return '';
    if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') return String(value);
    try {
      return JSON.stringify(value);
    } catch {
      return String(value);
    }
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
      width: 300,
      render: (title: string) => <Text strong>{title}</Text>
    },
    {
      title: '前置条件',
      dataIndex: 'preconditions',
      key: 'preconditions',
      width: 200,
      render: (preconditions: unknown) => {
        // 如果是数组，显示为有序列表
        if (Array.isArray(preconditions) && preconditions.length > 0) {
          if (preconditions.length === 1) {
            return toText(preconditions[0]);
          }
          return (
            <ol style={{ margin: 0, paddingLeft: 20 }}>
              {preconditions.map((item, index) => (
                <li key={index}>{toText(item)}</li>
              ))}
            </ol>
          );
        }
        return toText(preconditions) || '-';
      }
    },
    {
      title: '测试步骤',
      dataIndex: 'steps',
      key: 'steps',
      width: 350,
      render: (steps: unknown[]) => (
        Array.isArray(steps) && steps.length > 0 ? (
          <ol style={{ margin: 0, paddingLeft: 20 }}>
            {steps.map((step, index) => (
              <li key={index}>{toText(step)}</li>
            ))}
          </ol>
        ) : '-'
      )
    },
    {
      title: '预期结果',
      dataIndex: 'expected',
      key: 'expected',
      render: (expected: unknown) => {
        // 如果是数组，显示为有序列表
        if (Array.isArray(expected) && expected.length > 0) {
          if (expected.length === 1) {
            return toText(expected[0]);
          }
          return (
            <ol style={{ margin: 0, paddingLeft: 20 }}>
              {expected.map((item, index) => (
                <li key={index}>{toText(item)}</li>
              ))}
            </ol>
          );
        }
        return toText(expected) || '-';
      }
    }
  ];

  return (
    <div style={{ marginTop: 16 }}>
      <Typography.Title level={5}>{title}</Typography.Title>

      {modules.map((module, index) => (
        <div key={index} style={{ marginBottom: 24 }}>
          <Typography.Title level={5}>
            <Tag color="green">模块</Tag>
            {module.name}
            <Text type="secondary" style={{ marginLeft: 8, fontSize: 14, fontWeight: 'normal' }}>
              ({module.cases.length} 个用例)
            </Text>
          </Typography.Title>

          <Table
            columns={columns}
            dataSource={module.cases}
            rowKey="id"
            pagination={{ pageSize: 10 }}
            size="small"
            bordered
          />
        </div>
      ))}

      {modules.length === 0 && (
        <Text type="secondary">{emptyText}</Text>
      )}

    </div>
  );
};

export default TestCasesView;
