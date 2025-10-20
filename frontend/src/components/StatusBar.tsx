import { Alert, Progress, Space, Typography } from 'antd';
import React from 'react';

import { useAppStore } from '../stores/chatStore';

const StatusBar: React.FC = () => {
  const { session, progress, currentStage, systemMessages, isConnecting } = useAppStore();

  if (!session) {
    return null;
  }

  const latestMessage = systemMessages[systemMessages.length - 1];
  const progressPercent = Math.round(progress * 100);

  return (
    <Space direction="vertical" style={{ width: '100%' }} size="small">
      <Space style={{ width: '100%', justifyContent: 'space-between' }}>
        <Typography.Text>
          会话ID: <Typography.Text code>{session.id}</Typography.Text>
        </Typography.Text>
        <Typography.Text>
          当前阶段: <Typography.Text strong>{currentStage ?? session.current_stage ?? '初始化'}</Typography.Text>
        </Typography.Text>
      </Space>
      <Progress percent={progressPercent} status={isConnecting ? 'active' : 'normal'} />
      {latestMessage && (
        <Alert message={latestMessage.content} type="info" showIcon style={{ marginBottom: 8 }} />
      )}
    </Space>
  );
};

export default StatusBar;
