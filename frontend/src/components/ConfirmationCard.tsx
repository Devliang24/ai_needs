import { Button, Card, Space, Typography } from 'antd';
import React from 'react';

interface Props {
  visible: boolean;
  onConfirm: () => void;
  onRequestChanges: () => void;
}

const ConfirmationCard: React.FC<Props> = ({ visible, onConfirm, onRequestChanges }) => {
  if (!visible) return null;

  return (
    <Card style={{ marginTop: 16 }}>
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        <Typography.Text strong>请确认当前分析结果是否准确：</Typography.Text>
        <Space>
          <Button type="link" onClick={onConfirm}>✓ 准确，继续</Button>
          <Button type="link" onClick={onRequestChanges}>✏️ 需要补充</Button>
        </Space>
      </Space>
    </Card>
  );
};

export default ConfirmationCard;
