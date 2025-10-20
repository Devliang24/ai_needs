import { DeleteOutlined, DownloadOutlined, StopOutlined } from '@ant-design/icons';
import { Button, List, message, Radio, Typography, Space } from 'antd';
import React, { useEffect, useMemo, useRef, useState } from 'react';

import { AgentFlowProgress, AgentTimeline, FileUploader } from '../components';
import { createSession, exportSessionExcel, exportSessionXmind, fetchSessionDetail } from '../services/api';
import { createSessionSocket } from '../services/websocket';
import { useAppStore } from '../stores/chatStore';

const HomePage: React.FC = () => {
  const formatBytes = (bytes: number): string => {
    if (!bytes || bytes <= 0) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    const value = bytes / Math.pow(1024, i);
    const fixed = value >= 100 ? value.toFixed(0) : value >= 10 ? value.toFixed(1) : value.toFixed(2);
    return `${fixed} ${units[i]}`;
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
    removeDocument,
    setWebSocket,
    documentHistories,
    setAgentResults,
    analysisRunning,
    setAnalysisRunning
  } = useAppStore();
  const socketRef = useRef<WebSocket | null>(null);
  // Keep latest selectedStage without re-running socket effect
  const selectedStageRef = useRef<string | null>(null);
  const activeDocIdRef = useRef<string | null>(null);
  const savedHistorySessionIdRef = useRef<string | null>(null);
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const prevDocIdsRef = useRef<string[]>([]);

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
        if (selectedStage !== 'layout_analysis') {
          setSelectedStage('layout_analysis');
        }
      }
    } else if (!session) {
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
      socketRef.current?.close();
    };
  }, [setAnalysisRunning]);

  // 同步选择状态：仅允许单选。若当前选择被删除，则默认选择最新的一个。
  useEffect(() => {
    const currentIds = documents.map((d) => d.id);
    const prevIds = new Set(prevDocIdsRef.current);
    const hasSelected = selectedDocId && currentIds.includes(selectedDocId);
    let nextSelected: string | null = hasSelected ? selectedDocId : null;
    const newlyAdded = currentIds.filter((id) => !prevIds.has(id));
    // 若无选中项，则默认选中最新的一个
    if (!nextSelected && currentIds.length > 0) {
      // 默认选中最新的一个
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
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'agent_message') {
          const message = {
            sender: data.sender ?? 'Agent',
            stage: data.stage ?? 'unknown',
            content: data.content ?? '',
            payload: data.payload,
            progress: data.progress ?? 0,
            needsConfirmation: data.needs_confirmation ?? false,
            confirmed: false,
            editable: true
          } as const;

          // 需求分析师智能体：实时流式输出，追加到同一个结果
          if (message.stage === 'requirement_analysis') {
            appendAgentResult(message as any);
          } else {
            addAgentResult(message as any);
          }
          setProgress(data.progress ?? 0, data.stage ?? null);

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
          if (data.stage && data.stage !== currentStage) {
            setSelectedStage(data.stage);
          }
        } else if (data.type === 'system_message') {
          addSystemMessage(data.content ?? '');
          setProgress(data.progress ?? 0, data.stage ?? null);
          if (typeof data.progress === 'number' && data.progress >= 1.0) {
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
        title: document.original_name,
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

    resetAnalysis();
    setSelectedStage('layout_analysis');
    setAnalysisRunning(true);
    setProgress(0.05, 'layout_analysis');
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

  const handleCancelAnalysis = () => {
    if (!analysisRunning && !session) {
      message.info('当前没有进行中的分析');
      return;
    }

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
    setSelectedStage('layout_analysis');
    addSystemMessage('当前分析已取消。');
    message.success('已取消当前分析');
  };

  const downloadBlob = (blob: Blob, filename: string) => {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  };

  const handleExportXmind = async () => {
    if (!session) return;
    try {
      const blob = await exportSessionXmind(session.id);
      downloadBlob(blob, `session-${session.id}.xmind`);
      message.success('XMind 导出完成');
    } catch (error) {
      console.error(error);
      message.error('导出 XMind 失败');
    }
  };

  const handleExportExcel = async () => {
    if (!session) return;
    try {
      const blob = await exportSessionExcel(session.id);
      downloadBlob(blob, `session-${session.id}.xlsx`);
      message.success('Excel 导出完成');
    } catch (error) {
      console.error(error);
      message.error('导出 Excel 失败');
    }
  };

  const exportMenuItems = [
    // {
    //   key: 'xmind',
    //   label: '导出 XMind',
    //   onClick: handleExportXmind
    // },
    {
      key: 'excel',
      label: '导出 Excel',
      onClick: handleExportExcel
    }
  ];

  // 检查是否有completed阶段的结果
  const hasCompletedStage = useMemo(() => {
    return agentResults.some(result => result.stage === 'completed');
  }, [agentResults]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: 24, gap: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography.Title level={3} style={{ margin: 0 }}>
          智能分析平台
        </Typography.Title>
        <Space size={12}>
          <Button
            danger
            icon={<StopOutlined />}
            disabled={!analysisRunning}
            onClick={handleCancelAnalysis}
          >
            取消分析
          </Button>
          <Button
            type="primary"
            icon={<DownloadOutlined />}
            disabled={!session || !hasCompletedStage}
            onClick={handleExportExcel}
          >
            导出 Excel
          </Button>
        </Space>
      </div>

      <div style={{ display: 'flex', flex: 1, gap: 16, minHeight: 0 }}>
        {/* 左侧：上传区域 */}
        <div
          style={{
            flex: '0 0 30%',
            minWidth: 360,
            maxWidth: 520,
            display: 'flex',
            flexDirection: 'column',
            minHeight: 0
          }}
        >
          <div
            className="no-scrollbar"
            style={{ flex: 1, overflowY: 'auto', overflowX: 'hidden', display: 'flex', flexDirection: 'column' }}
          >
            <FileUploader />
            <List
              header={<Typography.Text>选择要分析的文档</Typography.Text>}
              dataSource={documentList}
              locale={{ emptyText: '暂未上传文档' }}
              renderItem={(item) => (
                <List.Item
                  actions={[
                    <Button
                      key="delete"
                      type="text"
                      danger
                      size="small"
                      icon={<DeleteOutlined />}
                      onClick={() => handleRemoveDocument(item.id)}
                    >
                      删除
                    </Button>
                  ]}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, width: '100%' }}>
                    <Radio
                      checked={selectedDocId === item.id}
                      onChange={() => setSelectedDocId(item.id)}
                    />
                    <List.Item.Meta
                      title={
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <span>{item.title}</span>
                          <Typography.Text type="secondary">{item.sizeString}</Typography.Text>
                        </div>
                      }
                    />
                  </div>
                </List.Item>
              )}
              style={{ marginTop: 16, background: '#fff', padding: 16, borderRadius: 8 }}
            />
            <Button
              type="primary"
              htmlType="button"
              block
              disabled={documents.length === 0 || !selectedDocId || analysisRunning}
              loading={analysisRunning}
              style={{ marginTop: 16 }}
              onClick={(e) => { e.preventDefault(); handleStartAnalysis(); }}
            >
              {analysisRunning ? '分析中...' : agentResults.length > 0 ? '重新分析' : '开始分析'}
            </Button>
          </div>
        </div>

        {/* 右侧：流程步骤条 + 智能体执行结果 */}
        <div style={{ flex: 1.7, minWidth: 0, display: 'flex', flexDirection: 'column', gap: 16 }}>
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
