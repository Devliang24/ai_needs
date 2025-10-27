import { ClearOutlined, DeleteOutlined } from '@ant-design/icons';
import { Button, List, message, Radio, Tooltip, Typography } from 'antd';
import React, { useEffect, useMemo, useRef, useState } from 'react';

import { AgentFlowProgress, AgentTimeline, FileUploader } from '../components';
import { createSession, fetchSessionDetail } from '../services/api';
import { createSessionSocket } from '../services/websocket';
import { useAppStore } from '../stores/chatStore';
import { useMediaQuery } from '../hooks/useMediaQuery';

const STAGE_SEQUENCE = ['requirement_analysis', 'test_generation', 'review', 'test_completion', 'completed'] as const;

const getStageIndex = (stage: string | null | undefined): number => {
  if (!stage) return -1;
  return STAGE_SEQUENCE.indexOf(stage as typeof STAGE_SEQUENCE[number]);
};

const HomePage: React.FC = () => {
  const formatBytes = (bytes: number): string => {
    if (!bytes || bytes <= 0) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    const value = bytes / Math.pow(1024, i);
    const fixed = value >= 100 ? value.toFixed(0) : value >= 10 ? value.toFixed(1) : value.toFixed(2);
    return `${fixed} ${units[i]}`;
  };

  // 截断文件名：保留前6位字符 + 扩展名
  const truncateFileName = (fileName: string): string => {
    if (!fileName) return '';

    // 找到最后一个点的位置（扩展名）
    const lastDotIndex = fileName.lastIndexOf('.');

    // 如果没有扩展名或文件名很短，直接返回
    if (lastDotIndex === -1 || fileName.length <= 10) {
      return fileName;
    }

    // 分离文件名和扩展名
    const nameWithoutExt = fileName.substring(0, lastDotIndex);
    const extension = fileName.substring(lastDotIndex); // 包含 .

    // 如果文件名（不含扩展名）长度 <= 6，直接返回完整文件名
    if (nameWithoutExt.length <= 6) {
      return fileName;
    }

    // 截取前6位 + ... + 扩展名
    return `${nameWithoutExt.substring(0, 6)}...${extension}`;
  };
  const {
    documents,
    session,
    agentResults,
    currentStage,
    progress,
    isConnecting,
    selectedStage,
    addAgentResult,
    addSystemMessage,
    setSession,
    setConnecting,
    setProgress,
    setSelectedStage,
    appendAgentResult,
    resetAnalysis,
    clearDocumentHistory,
    clearAnalysisResults,
    removeDocument,
    setWebSocket,
    documentHistories,
    setAgentResults,
    analysisRunning,
    setAnalysisRunning,
    lastActivityTime,
    updateActivityTime
  } = useAppStore();
  const socketRef = useRef<WebSocket | null>(null);
  // Keep latest selectedStage without re-running socket effect
  const selectedStageRef = useRef<string | null>(null);
  const activeDocIdRef = useRef<string | null>(null);
  const savedHistorySessionIdRef = useRef<string | null>(null);
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const prevDocIdsRef = useRef<string[]>([]);
  const inactivityTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Sync refs with latest values to avoid re-binding socket handlers
  useEffect(() => {
    selectedStageRef.current = selectedStage;
  }, [selectedStage]);

  // 当未在实时分析时，点击左侧文档显示最近的历史记录
  useEffect(() => {
    if (!selectedDocId) {
      if (!session && agentResults.length > 0) {
        setAgentResults([]);
        setProgress(0, null);
      }
      return;
    }

    const isStartingSession = analysisRunning && activeDocIdRef.current === selectedDocId;
    if (isStartingSession) return;

    const activeSocket = socketRef.current;
    if (activeSocket && activeSocket.readyState !== WebSocket.CLOSED) {
      return;
    }

    const historyEntries = documentHistories[selectedDocId] ?? [];
    if (historyEntries.length > 0) {
      const latest = historyEntries[0];
      if (agentResults !== latest.agentResults) {
        setAgentResults(latest.agentResults);
      }
      if (!session) {
        setProgress(1, 'completed');

        // 智能选择默认阶段：找到历史记录中最后有结果的阶段
        const availableStages = new Set(latest.agentResults.map(r => r.stage));

        // 如果当前选中的阶段在历史数据中不存在，则智能选择一个合适的阶段
        if (!selectedStage || !availableStages.has(selectedStage)) {
          // 按优先级选择：优先选择最后完成的阶段
          const stagePriority = ['completed', 'test_completion', 'review', 'test_generation', 'requirement_analysis'];
          const defaultStage = stagePriority.find(stage => availableStages.has(stage)) || 'requirement_analysis';
          setSelectedStage(defaultStage);
        }
        // 如果当前选中的阶段存在，则保持不变
      }
    } else if (!session && !analysisRunning) {
      // 重要：只有在非分析状态下才清除，避免在开始分析时重置进度
      if (agentResults.length > 0) {
        setAgentResults([]);
      }
      setProgress(0, null);
    }
  }, [selectedDocId, documentHistories, analysisRunning, session, setAgentResults, setProgress, setSelectedStage, selectedStage, agentResults]);

  // 当上传文件完成时，自动选中该文件（包括重复文件场景）
  useEffect(() => {
    const handler = (e: Event) => {
      try {
        const ce = e as CustomEvent<{ id?: string }>;
        if (ce.detail && ce.detail.id) {
          setSelectedDocId(ce.detail.id);
        }
      } catch {}
    };
    window.addEventListener('document_uploaded', handler as EventListener);
    return () => window.removeEventListener('document_uploaded', handler as EventListener);
  }, []);

  useEffect(() => {
    return () => {
      setAnalysisRunning(false);
      clearInactivityTimer();
      socketRef.current?.close();
    };
  }, [setAnalysisRunning]);

  // 监听用户活动时间，重置超时定时器
  useEffect(() => {
    if (lastActivityTime > 0 && (analysisRunning || session)) {
      resetInactivityTimer();
    }
  }, [lastActivityTime]);

  // 同步选择状态：仅允许单选。若当前选择被删除，则默认选择最新的一个。
  useEffect(() => {
    const currentIds = documents.map((d) => d.id);
    const prevIds = new Set(prevDocIdsRef.current);
    const hasSelected = selectedDocId && currentIds.includes(selectedDocId);
    let nextSelected: string | null = hasSelected ? selectedDocId : null;
    const newlyAdded = currentIds.filter((id) => !prevIds.has(id));
    if (newlyAdded.length > 0) {
      // 优先选中新添加的文档（包括批量恢复的场景）
      nextSelected = newlyAdded[newlyAdded.length - 1];
    } else if (!nextSelected && currentIds.length > 0) {
      // 若仍未选中，则默认选中文档列表的最后一个
      nextSelected = currentIds[currentIds.length - 1];
    }
    setSelectedDocId(nextSelected);
    prevDocIdsRef.current = currentIds;
  }, [documents]);

  useEffect(() => {
    if (!session) return;

    setConnecting(true);
    const socket = createSessionSocket(session.id);
    socketRef.current = socket;
    setWebSocket(socket);

    socket.onopen = () => {
      setConnecting(false);
      addSystemMessage('WebSocket 已连接，等待 Agent 输出...');
      // 启动超时定时器
      resetInactivityTimer();
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        // 收到消息时更新活动时间
        updateActivityTime();

        if (data.type === 'agent_message') {
          // 调试日志：记录接收到的WebSocket消息
          console.log('[WebSocket] 收到agent_message:', {
            stage: data.stage,
            sender: data.sender,
            hasPayload: !!data.payload,
            payloadKeys: data.payload ? Object.keys(data.payload) : null,
            contentLength: data.content ? String(data.content).length : 0
          });

          const message = {
            sender: data.sender ?? 'Agent',
            stage: data.stage ?? 'unknown',
            content: data.content ?? '',
            payload: data.payload,
            progress: data.progress ?? 0,
            needsConfirmation: data.needs_confirmation ?? false,
            confirmed: false,
            editable: true,
            durationSeconds: typeof data.duration_seconds === 'number' ? data.duration_seconds : null
          } as const;

          // 流式消息(is_streaming=true)：追加到现有结果，实现流式更新
          // 非流式消息：创建新结果
          // 注意：流式阶段的最终消息也带is_streaming=true，但会设置needsConfirmation=true和完整payload
          if (data.is_streaming === true) {
            appendAgentResult(message as any);
          } else {
            addAgentResult(message as any);
          }
          const previousState = useAppStore.getState();
          const previousStage = previousState.currentStage;
          const incomingStageIndex = getStageIndex(data.stage);
          const previousStageIndex = getStageIndex(previousStage);
          const isStageInSequence = incomingStageIndex !== -1;
          const isRegressing = isStageInSequence && previousStageIndex >= 0 && incomingStageIndex < previousStageIndex;
          const isStreamingEvent = data.is_streaming === true;

          let stageForProgress: string | null = data.stage ?? null;
          if (!isStageInSequence) {
            stageForProgress = previousStage;
          } else if (isRegressing && isStreamingEvent) {
            stageForProgress = previousStage;
          }
          setProgress(data.progress ?? 0, stageForProgress);

          const isCompleted = (typeof data.progress === 'number' && data.progress >= 1.0) || message.stage === 'completed';
          if (isCompleted) {
            setConnecting(false);
            setAnalysisRunning(false);

            const targetDocId = activeDocIdRef.current;
            const stateSnapshot = useAppStore.getState();
            const activeSessionId = stateSnapshot.session?.id;
            if (
              targetDocId &&
              activeSessionId &&
              savedHistorySessionIdRef.current !== activeSessionId &&
              stateSnapshot.agentResults.length > 0
            ) {
              const historyResults = JSON.parse(JSON.stringify(stateSnapshot.agentResults)) as typeof stateSnapshot.agentResults;
              stateSnapshot.addDocumentHistory(targetDocId, {
                sessionId: activeSessionId,
                timestamp: Date.now(),
                agentResults: historyResults
              });
              savedHistorySessionIdRef.current = activeSessionId;
              activeDocIdRef.current = null;
            }
          }

          // 自动切换到新阶段（避免依赖 effect 重连）
          const currentStage = selectedStageRef.current;
          const selectedStageIndex = getStageIndex(currentStage);
          const shouldAutoSwitch = (() => {
            if (!data.stage || !isStageInSequence) {
              return false;
            }
            if (isRegressing && isStreamingEvent) {
              return false;
            }
            if (isRegressing) {
              return true;
            }
            return selectedStageIndex === -1 || incomingStageIndex >= selectedStageIndex;
          })();
          if (data.stage && shouldAutoSwitch && data.stage !== currentStage) {
            setSelectedStage(data.stage);
          }
        } else if (data.type === 'system_message') {
          addSystemMessage(data.content ?? '');
          const previousState = useAppStore.getState();
          const previousStage = previousState.currentStage;
          const incomingStageIndex = getStageIndex(data.stage);
          const previousStageIndex = getStageIndex(previousStage);
          const isStageInSequence = incomingStageIndex !== -1;
          const isRegressing = isStageInSequence && previousStageIndex >= 0 && incomingStageIndex < previousStageIndex;
          let stageForProgress: string | null = data.stage ?? null;
          if (!isStageInSequence || isRegressing) {
            stageForProgress = previousStage;
          }
          setProgress(data.progress ?? 0, stageForProgress);
          if (typeof data.progress === 'number' && data.progress >= 1.0) {
            setAnalysisRunning(false);
          } else if (data.content && data.content.includes('失败')) {
            setAnalysisRunning(false);
          }
        }
      } catch (error) {
        console.error('解析WebSocket消息失败:', error);
        addSystemMessage(`收到消息: ${event.data}`);
      }
    };

    socket.onerror = () => {
      setConnecting(false);
      addSystemMessage('实时通道连接异常。');
      setAnalysisRunning(false);
    };

    socket.onclose = () => {
      setConnecting(false);
      setWebSocket(null);
      addSystemMessage('实时通道已关闭。');
      activeDocIdRef.current = null;
      savedHistorySessionIdRef.current = null;
      setAnalysisRunning(false);
      // 清除超时定时器
      clearInactivityTimer();
    };

    return () => {
      socket.close();
      setWebSocket(null);
    };
    // Only depend on session to keep one socket per session
  }, [session]);


  const documentList = useMemo(
    () =>
      documents.map((document) => ({
        id: document.id,
        title: truncateFileName(document.original_name),
        fullTitle: document.original_name, // 保留完整文件名用于 tooltip
        sizeString: formatBytes(document.size)
      })),
    [documents]
  );

  const handleRemoveDocument = (documentId: string) => {
    removeDocument(documentId);

    // 同步更新 localStorage
    try {
      const UPLOADED_LIST_KEY = 'uploaded_documents';
      const listRaw = localStorage.getItem(UPLOADED_LIST_KEY);
      if (listRaw) {
        const list = JSON.parse(listRaw);
        const updatedList = list.filter((d: any) => d.id !== documentId);
        localStorage.setItem(UPLOADED_LIST_KEY, JSON.stringify(updatedList));
      }
    } catch (error) {
      console.error('Failed to update localStorage:', error);
    }

    message.success('文档已删除');
  };

  const handleStartAnalysis = async () => {
    if (documents.length === 0) {
      message.warning('请先上传至少一个需求文档');
      return;
    }
    if (!selectedDocId) {
      message.warning('请先选择需要分析的文档');
      return;
    }

    activeDocIdRef.current = selectedDocId;
    savedHistorySessionIdRef.current = null;

    if (socketRef.current) {
      socketRef.current.onmessage = null;
      socketRef.current.onerror = null;
      socketRef.current.onclose = null;
      socketRef.current.close();
      socketRef.current = null;
    }

    // 重要：先设置加载状态，确保UI立即显示加载交互
    setAnalysisRunning(true);
    setSelectedStage('requirement_analysis');
    setProgress(0.12, 'requirement_analysis');

    // 然后清除旧结果（不会重置analysisRunning）
    clearAnalysisResults();

    try {
      const payload = {
        document_ids: [selectedDocId],
        config: {}
      };
      const response = await createSession(payload);
      const detail = await fetchSessionDetail(response.session_id);
      setSession(detail);
      addSystemMessage('分析会话已创建，开始排队执行智能体。');
    } catch (error) {
      console.error('创建分析会话失败:', error);
      const errorMsg = error instanceof Error ? error.message : '未知错误';
      activeDocIdRef.current = null;
      savedHistorySessionIdRef.current = null;
      message.error(`创建分析会话失败: ${errorMsg}`);
      setAnalysisRunning(false);
      setProgress(0, null);
    }
  };

  // 清除超时定时器
  const clearInactivityTimer = () => {
    if (inactivityTimerRef.current) {
      clearTimeout(inactivityTimerRef.current);
      inactivityTimerRef.current = null;
    }
  };

  // 重置超时定时器（10分钟无操作自动断开）
  const resetInactivityTimer = () => {
    clearInactivityTimer();

    // 如果当前阶段是 completed，不启动超时定时器
    if (currentStage === 'completed') {
      return;
    }

    // 10分钟 = 600000ms
    const INACTIVITY_TIMEOUT = 10 * 60 * 1000;
    inactivityTimerRef.current = setTimeout(() => {
      if (analysisRunning || session) {
        handleCancelAnalysis(true);
      }
    }, INACTIVITY_TIMEOUT);
  };

  const handleCancelAnalysis = (isTimeout = false) => {
    if (!analysisRunning && !session) {
      if (!isTimeout) {
        message.info('当前没有进行中的分析');
      }
      return;
    }

    clearInactivityTimer();
    setAnalysisRunning(false);
    setConnecting(false);
    activeDocIdRef.current = null;
    savedHistorySessionIdRef.current = null;

    if (socketRef.current) {
      socketRef.current.onmessage = null;
      socketRef.current.onerror = null;
      socketRef.current.onclose = null;
      socketRef.current.close();
      socketRef.current = null;
    }

    resetAnalysis();
    setSelectedStage('requirement_analysis');

    if (selectedDocId) {
      clearDocumentHistory(selectedDocId);
    }

    if (isTimeout) {
      addSystemMessage('由于10分钟无操作，分析已自动停止。');
      message.warning('分析已因超时自动停止');
    } else {
      addSystemMessage('当前分析已取消。');
      message.success('已取消当前分析');
    }
  };

  const handleClearSession = () => {
    // 1. 清除超时定时器
    clearInactivityTimer();

    // 2. 停止分析状态
    setAnalysisRunning(false);
    setConnecting(false);

    // 3. 清除引用
    activeDocIdRef.current = null;
    savedHistorySessionIdRef.current = null;

    // 4. 关闭WebSocket连接
    if (socketRef.current) {
      socketRef.current.onmessage = null;
      socketRef.current.onerror = null;
      socketRef.current.onclose = null;
      socketRef.current.close();
      socketRef.current = null;
    }

    // 5. 清空选中的文档 ID，避免触发历史记录重新加载
    setSelectedDocId(null);

    // 6. 重置所有分析状态
    resetAnalysis();
    setSelectedStage('requirement_analysis');

    // 7. 显示成功消息
    addSystemMessage('会话已清理。');
    message.success('会话已清理');
  };

  // 检查是否有completed阶段的结果
  const isMobile = useMediaQuery('(max-width: 767px)');

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      padding: isMobile ? 12 : 24,
      gap: isMobile ? 12 : 16
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography.Title level={isMobile ? 4 : 3} style={{ margin: 0 }}>
          智能分析平台
        </Typography.Title>
        <div style={{ display: 'flex', gap: isMobile ? 4 : 8 }}>
          {/* 清理会话按钮 */}
          {(session || agentResults.length > 0) && (
            <Button
              danger
              icon={<ClearOutlined />}
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                handleClearSession();
              }}
              size={isMobile ? 'middle' : 'middle'}
              style={{
                touchAction: 'manipulation',
                userSelect: 'none'
              }}
            >
              {isMobile ? '清理' : '清理会话'}
            </Button>
          )}
        </div>
      </div>

      <div style={{
        display: 'flex',
        flexDirection: isMobile ? 'column' : 'row',
        flex: 1,
        gap: isMobile ? 12 : 16,
        minHeight: 0
      }}>
        {/* 左侧/上部：上传区域 */}
        <div
          style={{
            flex: isMobile ? '0 0 auto' : '0 0 30%',
            minWidth: isMobile ? 'auto' : 360,
            maxWidth: isMobile ? '100%' : 520,
            display: 'flex',
            flexDirection: 'column',
            minHeight: isMobile ? 'auto' : 0,
            maxHeight: isMobile ? (documents.length === 0 ? '25vh' : '28vh') : 'none'
          }}
        >
          <div
            className="no-scrollbar"
            style={{
              flex: 1,
              overflowY: 'auto',
              overflowX: 'hidden',
              display: 'flex',
              flexDirection: 'column'
            }}
          >
            <FileUploader />
            <List
              header={isMobile ? null : <Typography.Text>选择要分析的文档</Typography.Text>}
              dataSource={documentList}
              locale={{ emptyText: '暂未上传文档' }}
              renderItem={(item) => (
                <List.Item
                  style={{ alignItems: 'center' }}
                  actions={[
                    <Button
                      key="delete"
                      type="text"
                      danger
                      size="small"
                      icon={<DeleteOutlined />}
                      onClick={() => handleRemoveDocument(item.id)}
                      style={{ flexShrink: 0, minWidth: isMobile ? 'auto' : undefined }}
                    >
                      {isMobile ? '' : '删除'}
                    </Button>
                  ]}
                >
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: isMobile ? 6 : 8,
                    width: '100%',
                    minWidth: 0,
                    overflow: 'hidden'
                  }}>
                    <Radio
                      checked={selectedDocId === item.id}
                      onChange={() => setSelectedDocId(item.id)}
                      style={{ flexShrink: 0 }}
                    />
                    <List.Item.Meta
                      style={{ minWidth: 0, overflow: 'hidden', flex: 1 }}
                      title={
                        <div style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: isMobile ? 4 : 8,
                          overflow: 'hidden'
                        }}>
                          <Tooltip title={item.fullTitle} placement="topLeft">
                            <span
                              style={{
                                cursor: 'pointer',
                                whiteSpace: 'nowrap',
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                flex: 1,
                                minWidth: 0,
                                fontSize: isMobile ? '13px' : undefined
                              }}
                              onClick={() => setSelectedDocId(item.id)}
                            >
                              {item.title}
                            </span>
                          </Tooltip>
                          <Typography.Text
                            type="secondary"
                            style={{
                              flexShrink: 0,
                              fontSize: isMobile ? '12px' : undefined
                            }}
                          >
                            {item.sizeString}
                          </Typography.Text>
                        </div>
                      }
                    />
                  </div>
                </List.Item>
              )}
              style={{
                marginTop: isMobile ? 8 : 16,
                background: '#fff',
                padding: isMobile ? 8 : 16,
                borderRadius: 8
              }}
            />
            {documents.length > 0 && (
              <Button
                type="primary"
                htmlType="button"
                block
                disabled={!selectedDocId || analysisRunning}
                loading={analysisRunning}
                style={{ marginTop: isMobile ? 8 : 16 }}
                onClick={(e) => { e.preventDefault(); handleStartAnalysis(); }}
              >
                {analysisRunning ? '分析中...' : agentResults.length > 0 ? '重新分析' : '开始分析'}
              </Button>
            )}
          </div>
        </div>

        {/* 右侧/下部：流程步骤条 + 智能体执行结果 */}
        <div style={{
          flex: isMobile ? 1 : 1.7,
          minWidth: 0,
          display: 'flex',
          flexDirection: 'column',
          gap: isMobile ? 12 : 16,
          minHeight: isMobile ? 0 : 'auto'
        }}>
          <AgentFlowProgress
            currentStage={currentStage}
            progress={progress}
            agentResults={agentResults}
            isConnecting={isConnecting}
            selectedStage={selectedStage}
            onStageClick={setSelectedStage}
          />
          <div style={{ flex: 1, minHeight: 0, display: 'flex', width: '100%' }}>
            <AgentTimeline />
          </div>
        </div>
      </div>
    </div>
  );
};

export default HomePage;
