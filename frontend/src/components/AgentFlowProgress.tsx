import { Steps, Card } from 'antd';
import React, { useMemo } from 'react';
import type { AgentResult } from '../stores/chatStore';
import { useMediaQuery } from '../hooks/useMediaQuery';

interface AgentFlowProgressProps {
  currentStage: string | null;
  progress: number;
  agentResults: AgentResult[];
  isConnecting: boolean;
  selectedStage: string | null;
  onStageClick: (stage: string) => void;
}

interface FlowStage {
  key: string;
  title: string;
}

const FLOW_STAGES: FlowStage[] = [
  { key: 'requirement_analysis', title: '需求分析' },
  { key: 'test_generation', title: '用例生成' },
  { key: 'review', title: '质量评审' },
  { key: 'test_completion', title: '用例补全' },
  { key: 'completed', title: '合并用例' }
];

const AgentFlowProgress: React.FC<AgentFlowProgressProps> = ({
  currentStage,
  progress,
  agentResults,
  isConnecting: _isConnecting,
  selectedStage,
  onStageClick
}) => {
  const isMobile = useMediaQuery('(max-width: 767px)');

  // 计算当前执行步骤索引
  const currentStepIndex = useMemo(() => {
    // 如果整体完成，直接高亮最后一步
    if (progress >= 1.0) {
      return FLOW_STAGES.length - 1;
    }

    if (!currentStage) return -1;

    // 根据当前阶段查找索引
    const index = FLOW_STAGES.findIndex(stage => stage.key === currentStage);
    return index >= 0 ? index : -1;
  }, [currentStage, progress]);

  // 计算阶段完成状态
  const maxCompletedIndex = useMemo(() => {
    let completedIndex = -1;
    for (let i = 0; i < FLOW_STAGES.length; i += 1) {
      const stage = FLOW_STAGES[i];
      const stageResults = agentResults.filter(result => result.stage === stage.key);
      if (stageResults.length === 0) {
        break;
      }
      const latestResult = stageResults[stageResults.length - 1];
      if (latestResult.needsConfirmation) {
        break;
      }
      completedIndex = i;
    }
    return completedIndex;
  }, [agentResults]);

  const selectedStepIndex = useMemo(() => {
    if (!selectedStage) return -1;
    return FLOW_STAGES.findIndex(stage => stage.key === selectedStage);
  }, [selectedStage]);

  const allowedMaxIndex = useMemo(() => {
    const indices = [maxCompletedIndex, currentStepIndex, selectedStepIndex]
      .filter(index => index != null && index >= 0);
    if (indices.length === 0) {
      return 0;
    }
    return Math.max(...indices);
  }, [currentStepIndex, maxCompletedIndex, selectedStepIndex]);

  const stepsItems = useMemo(() => {
    return FLOW_STAGES.map((stage, index) => {
      const hasResult = agentResults.some(result => result.stage === stage.key);
      const status: 'wait' | 'finish' = hasResult || index < currentStepIndex ? 'finish' : 'wait';
      const disabled = index > allowedMaxIndex;
      return { title: stage.title, status, disabled };
    });
  }, [agentResults, currentStepIndex, allowedMaxIndex]);


  // 处理步骤点击
  const handleStepChange = (current: number) => {
    const stage = FLOW_STAGES[current];
    if (stage && current <= allowedMaxIndex) {
      onStageClick(stage.key);
    }
  };

  // 移动端自定义步骤显示组件
  const renderMobileSteps = () => {
    return (
      <div style={{
        display: 'flex',
        gap: 8,
        flexWrap: 'wrap',
        justifyContent: 'space-between'
      }}>
        {FLOW_STAGES.map((stage, index) => {
          const hasResult = agentResults.some(result => result.stage === stage.key);
          const isCompleted = hasResult || index < currentStepIndex;
          const isCurrent = index === (selectedStepIndex >= 0 ? selectedStepIndex : currentStepIndex);
          const disabled = index > allowedMaxIndex;

          return (
            <div
              key={stage.key}
              onClick={() => !disabled && handleStepChange(index)}
              style={{
                flex: '1 1 auto',
                minWidth: '18%',
                padding: '6px 8px',
                textAlign: 'center',
                borderRadius: 4,
                fontSize: 12,
                fontWeight: isCompleted ? 600 : 400,
                color: isCompleted ? '#1890ff' : disabled ? '#d9d9d9' : '#595959',
                backgroundColor: isCurrent ? '#e6f7ff' : 'transparent',
                border: isCurrent ? '1px solid #1890ff' : '1px solid #f0f0f0',
                cursor: disabled ? 'not-allowed' : 'pointer',
                opacity: disabled ? 0.5 : 1,
                transition: 'all 0.3s ease',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis'
              }}
            >
              {stage.title}
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <Card
      size="small"
      bordered={false}
      style={{ background: '#fafafa' }}
      bodyStyle={{ padding: isMobile ? '12px' : '16px' }}
    >
      {isMobile ? (
        renderMobileSteps()
      ) : (
        <Steps
          current={selectedStepIndex >= 0 ? selectedStepIndex : currentStepIndex >= 0 ? currentStepIndex : -1}
          items={stepsItems}
          onChange={handleStepChange}
          responsive={false}
          size="default"
          style={{ cursor: 'pointer', fontSize: '16px' }}
        />
      )}
    </Card>
  );
};

export default AgentFlowProgress;
