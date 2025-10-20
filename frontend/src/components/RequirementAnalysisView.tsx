import { Card, Col, Collapse, Descriptions, List, Row, Tag, Typography } from 'antd';
import React from 'react';

const { Panel } = Collapse;
const { Text, Paragraph } = Typography;

interface Module {
  module: string;
  scenarios?: Array<{ name: string; description: unknown }>;
  rules?: unknown[];
}

interface RequirementAnalysisData {
  modules?: Module[];
  risks?: string[];
}

interface Props {
  data: Record<string, unknown>;
}

const RequirementAnalysisView: React.FC<Props> = ({ data }) => {
  const analysisData = data as RequirementAnalysisData;
  const modules = analysisData.modules || [];
  const risks = analysisData.risks || [];

  const toText = (value: unknown): string => {
    if (value == null) return '';
    if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') return String(value);
    try {
      return JSON.stringify(value);
    } catch {
      return String(value);
    }
  };

  return (
    <div style={{ marginTop: 16 }}>
      <Typography.Title level={5}>需求分析结果</Typography.Title>

      {modules.length > 0 && (
        <Row gutter={[16, 16]}>
          {modules.map((module, index) => (
            <Col span={24} key={index}>
              <Card
                size="small"
                bordered={false}
                title={
                  <span>
                    <Tag color="blue">模块 {index + 1}</Tag>
                    <Text strong>{module.module}</Text>
                  </span>
                }
              >
                <Descriptions column={1} size="small">
                  {module.scenarios && module.scenarios.length > 0 && (
                    <Descriptions.Item label="业务场景">
                      <List
                        size="small"
                        dataSource={module.scenarios}
                        renderItem={(scenario) => (
                          <List.Item>
                            <List.Item.Meta
                              title={scenario.name}
                              description={toText(scenario.description)}
                            />
                          </List.Item>
                        )}
                      />
                    </Descriptions.Item>
                  )}

                  {module.rules && module.rules.length > 0 && (
                    <Descriptions.Item label="业务规则">
                      <ul style={{ margin: 0, paddingLeft: 20 }}>
                        {module.rules.map((rule, rIndex) => (
                          <li key={rIndex}>{toText(rule)}</li>
                        ))}
                      </ul>
                    </Descriptions.Item>
                  )}
                </Descriptions>
              </Card>
            </Col>
          ))}
        </Row>
      )}

      {risks.length > 0 && (
        <Card
          size="small"
          bordered={false}
          title={<Text type="warning">风险点</Text>}
          style={{ marginTop: 16 }}
        >
          <List
            size="small"
            dataSource={risks}
            renderItem={(risk, index) => (
              <List.Item>
                <Tag color="warning">{index + 1}</Tag>
                <Text>{toText(risk)}</Text>
              </List.Item>
            )}
          />
        </Card>
      )}

      <Collapse ghost style={{ marginTop: 16 }}>
        <Panel header="查看原始JSON数据" key="1">
          <pre style={{ background: '#f5f5f5', padding: 12, borderRadius: 4, maxHeight: 300, overflow: 'auto' }}>
            {JSON.stringify(data, null, 2)}
          </pre>
        </Panel>
      </Collapse>
    </div>
  );
};

export default RequirementAnalysisView;
