import { List, Progress, Row, Col, Statistic, Card, Typography, Tag } from 'antd';
import React from 'react';

const { Text } = Typography;

interface QualityReviewData {
  coverage?: number;
  gaps?: unknown[];
  recommendations?: unknown[];
}

interface Props {
  data: Record<string, unknown>;
}

const QualityReviewView: React.FC<Props> = ({ data }) => {
  const reviewData = data as QualityReviewData;
  const rawCoverageValue = Number(reviewData.coverage ?? 0);
  const normalizedInput = Number.isFinite(rawCoverageValue) ? rawCoverageValue : 0;
  const coverageValue = normalizedInput > 1 ? normalizedInput : normalizedInput * 100;
  const coverage = Math.min(100, Math.max(0, coverageValue));
  const gaps = reviewData.gaps || [];
  const recommendations = reviewData.recommendations || [];

  const getProgressStatus = (coverage: number) => {
    if (coverage >= 90) return 'success';
    if (coverage >= 70) return 'normal';
    return 'exception';
  };

  const getCoverageColor = (coverage: number) => {
    if (coverage >= 90) return '#52c41a';
    if (coverage >= 70) return '#1890ff';
    return '#ff4d4f';
  };

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
      <Typography.Title level={5}>质量评审结果</Typography.Title>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={12}>
          <Card bordered={false}>
            <Statistic
              title="测试覆盖率"
              value={coverage}
              precision={1}
              suffix="%"
              valueStyle={{ color: getCoverageColor(coverage) }}
            />
            <Progress
              percent={coverage}
              status={getProgressStatus(coverage)}
              strokeColor={getCoverageColor(coverage)}
              style={{ marginTop: 16 }}
            />
          </Card>
        </Col>

        <Col span={12}>
          <Card bordered={false}>
            <Statistic
              title="发现的缺口"
              value={gaps.length}
              suffix="项"
              valueStyle={{ color: gaps.length > 0 ? '#faad14' : '#52c41a' }}
            />
            <Statistic
              title="改进建议"
              value={recommendations.length}
              suffix="条"
              style={{ marginTop: 16 }}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
      </Row>

      {gaps.length > 0 && (
        <Card
          bordered={false}
          title={
            <span>
              <Tag color="warning">缺口分析</Tag>
              <Text>需要关注的问题</Text>
            </span>
          }
          size="small"
          style={{ marginBottom: 16 }}
        >
          <List
            size="small"
            dataSource={gaps}
            renderItem={(gap, index) => (
              <List.Item>
                <Text>
                  <Tag color="orange">{index + 1}</Tag>
                  {toText(gap)}
                </Text>
              </List.Item>
            )}
          />
        </Card>
      )}

      {recommendations.length > 0 && (
        <Card
          bordered={false}
          title={
            <span>
              <Tag color="blue">改进建议</Tag>
              <Text>优化方向</Text>
            </span>
          }
          size="small"
        >
          <List
            size="small"
            dataSource={recommendations}
            renderItem={(recommendation, index) => (
              <List.Item>
                <Text>
                  <Tag color="blue">{index + 1}</Tag>
                  {toText(recommendation)}
                </Text>
              </List.Item>
            )}
          />
        </Card>
      )}
    </div>
  );
};

export default QualityReviewView;
