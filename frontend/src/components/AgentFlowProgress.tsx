import { Steps, Card } from 'antd';
import React, { useMemo } from 'react';
import type { AgentResult } from '../stores/chatStore';

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
  { key: 'layout_analysis', title: '版面分析' },
  { key: 'requirement_analysis', title: '需求分析' },
  { key: 'test_generation', title: '用例生成' },
  { key: 'review', title: '质量评审' },
  { key: 'test_completion', title: '用例补全' },
  { key: 'completed', title: '完成' }
];

const AgentFlowProgress: React.FC<AgentFlowProgressProps> = ({
  currentStage,
  progress,
  agentResults,
  isConnecting,
  selectedStage,
  onStageClick
}) => {
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

  // 计算选中步骤的索引（用于高亮显示）
  const selectedStepIndex = useMemo(() => {
    if (!selectedStage) return -1;
    return FLOW_STAGES.findIndex(stage => stage.key === selectedStage);
  }, [selectedStage]);

  // 为每个步骤生成状态
  const stepsItems = useMemo(() => {
    return FLOW_STAGES.map((stage, index) => {
      let status: 'wait' | 'process' | 'finish' | 'error' = 'wait';

      // 检查该阶段是否有结果
      const hasResult = agentResults.some(result => result.stage === stage.key);

      // 如果有结果，显示为完成状态
      if (hasResult) {
        status = 'finish';
      } else if (index === currentStepIndex && isConnecting) {
        // 当前执行的步骤（且正在连接中）
        status = 'process';
      } else {
        // 等待中的步骤
        status = 'wait';
      }

      return {
        title: stage.title,
        status
      };
    });
  }, [agentResults, currentStepIndex, isConnecting]);


  // 处理步骤点击
  const handleStepChange = (current: number) => {
    const stage = FLOW_STAGES[current];
    if (stage) {
      onStageClick(stage.key);
    }
  };

  return (
    <Card
      size="small"
      bordered={false}
      style={{ background: '#fafafa' }}
    >
      <Steps
        current={selectedStepIndex >= 0 ? selectedStepIndex : currentStepIndex >= 0 ? currentStepIndex : -1}
        items={stepsItems}
        onChange={handleStepChange}
        responsive={false}
        style={{ cursor: 'pointer', fontSize: '16px' }}
      />
    </Card>
  );
};

export default AgentFlowProgress;
