# AI Needs 前端开发完整提示词

> 基于 React 18 + TypeScript + Ant Design 的多智能体需求分析平台前端开发指南

## 📋 项目概述

**项目名称**: AI Needs - 智能需求分析平台前端  
**核心功能**: 文档上传、实时WebSocket通信、多阶段流程可视化、人工确认机制  
**技术架构**: React 18 + TypeScript + Zustand + Socket.IO + Ant Design

---

## 🏗️ 技术栈

### 核心框架
- **React**: 18.2.0 (函数组件 + Hooks)
- **TypeScript**: 5.3.0 (类型安全)
- **构建工具**: Vite 5.0.0 (快速开发)

### UI 与样式
- **UI 组件库**: Ant Design 5.12.0
- **图标**: @ant-design/icons 5.2.6
- **Markdown 渲染**: react-markdown 9.0.1
- **代码高亮**: rehype-highlight 7.0.2

### 状态与通信
- **状态管理**: Zustand 4.4.7 (轻量级)
- **HTTP 客户端**: Axios 1.6.0
- **WebSocket**: Socket.IO Client 4.6.1
- **文件上传**: react-dropzone 14.2.3

---

## 📁 项目结构

```
frontend/src/
├── components/          # UI组件
│   ├── FileUploader.tsx            # 文件上传（拖拽支持）
│   ├── AgentFlowProgress.tsx       # 流程进度条
│   ├── AgentTimeline.tsx           # 智能体时间线
│   ├── RequirementAnalysisView.tsx # 需求分析视图
│   ├── TestCasesView.tsx           # 测试用例视图
│   ├── QualityReviewView.tsx       # 质量评审视图
│   ├── SupplementalTestCasesView.tsx # 补充用例视图
│   ├── ConfirmationCard.tsx        # 人工确认卡片
│   └── StatusBar.tsx               # 状态栏
├── pages/               # 页面组件
│   └── Home.tsx                    # 主页面（唯一页面）
├── services/            # API服务
│   ├── api.ts                      # HTTP客户端（Axios）
│   └── websocket.ts                # WebSocket客户端
├── stores/              # 状态管理
│   └── chatStore.ts                # 全局状态（Zustand）
├── types/               # TypeScript类型定义
│   ├── document.ts
│   ├── session.ts
│   └── index.ts
├── hooks/               # 自定义Hooks
│   └── useMediaQuery.ts            # 响应式媒体查询
├── styles/              # 全局样式
├── App.tsx              # 应用入口
└── main.tsx             # React挂载入口
```

---

## 🎯 核心功能特性

### 1. 文档上传与管理
- ✅ 拖拽上传 + 点击上传
- ✅ 文件类型验证（PDF/DOCX/图片）
- ✅ 文件大小限制（10MB）
- ✅ 重复文件检测（基于checksum）
- ✅ 多文档管理（单选机制）
- ✅ 文档删除与清理
- ✅ localStorage持久化

### 2. 实时WebSocket通信
- ✅ Socket.IO实时连接
- ✅ 消息类型处理（agent_message、system_message）
- ✅ 流式消息追加（appendAgentResult）
- ✅ 完整消息创建（addAgentResult）
- ✅ 断线重连机制
- ✅ 历史事件恢复

### 3. 多阶段流程可视化
- ✅ 5阶段进度条（Steps组件）
- ✅ 智能体时间线（Timeline组件）
- ✅ 阶段自动切换
- ✅ 手动阶段切换
- ✅ 进度百分比显示

### 4. 人工确认机制
- ✅ 可编辑payload（JSON编辑器）
- ✅ 确认/拒绝按钮
- ✅ WebSocket发送确认消息
- ✅ 等待确认状态显示

### 5. 历史记录管理
- ✅ localStorage持久化（每个文档最多10条）
- ✅ 点击文档恢复历史结果
- ✅ 智能默认阶段选择
- ✅ 历史记录清理

### 6. 超时管理
- ✅ 10分钟无操作自动断开WebSocket
- ✅ 用户活动时间追踪
- ✅ 超时提示消息

---

## 🗂️ 状态管理设计 (Zustand)

### Store 结构

```typescript
interface AppState {
  // 文档管理
  documents: Document[];
  addDocument: (doc: Document) => void;
  removeDocument: (id: string) => void;
  
  // 会话管理
  session: SessionDetail | null;
  setSession: (session: SessionDetail) => void;
  
  // 智能体结果
  agentResults: AgentResult[];
  addAgentResult: (result: AgentResult) => void;
  appendAgentResult: (result: AgentResult) => void;  // 流式追加
  setAgentResults: (results: AgentResult[]) => void;
  
  // 系统消息
  systemMessages: SystemMessage[];
  addSystemMessage: (content: string) => void;
  
  // 进度与状态
  progress: number;
  currentStage: string | null;
  selectedStage: string | null;
  setProgress: (progress: number, stage: string | null) => void;
  setSelectedStage: (stage: string | null) => void;
  
  // WebSocket连接
  isConnecting: boolean;
  websocket: WebSocket | null;
  setConnecting: (value: boolean) => void;
  setWebSocket: (ws: WebSocket | null) => void;
  
  // 分析状态
  analysisRunning: boolean;
  setAnalysisRunning: (value: boolean) => void;
  
  // 活动时间（用于超时检测）
  lastActivityTime: number;
  updateActivityTime: () => void;
  
  // 历史记录
  documentHistories: Record<string, DocumentHistoryEntry[]>;
  addDocumentHistory: (docId: string, entry: DocumentHistoryEntry) => void;
  clearDocumentHistory: (docId: string) => void;
  
  // 人工确认
  sendConfirmation: (resultId: string, stage: string, payload?: Record<string, unknown>) => void;
  confirmAgentResult: (resultId: string) => void;
  updateAgentResult: (resultId: string, payload: Record<string, unknown>) => void;
  
  // 重置与清理
  clearAnalysisResults: () => void;
  resetAnalysis: () => void;
  reset: () => void;
}
```

### AgentResult 数据结构

```typescript
interface AgentResult {
  id: string;
  sender: string;              // "需求分析师"、"测试工程师"等
  stage: string;               // "requirement_analysis"、"test_generation"等
  content: unknown;            // 文本内容或Markdown
  payload?: Record<string, unknown>;  // JSON数据（用于表格展示）
  progress: number;            // 进度 0-1
  timestamp: number;
  startedAt?: number;
  durationSeconds?: number | null;  // 执行耗时（秒）
  needsConfirmation?: boolean; // 是否需要确认
  confirmed?: boolean;         // 是否已确认
  editable?: boolean;          // 是否可编辑
}
```

### localStorage 持久化

```typescript
// 存储结构
const DOCUMENT_HISTORY_STORAGE_KEY = 'document_histories';

// 数据格式
{
  "doc_uuid_1": [
    {
      "sessionId": "session_uuid",
      "timestamp": 1234567890000,
      "agentResults": [...]
    }
  ]
}

// 持久化函数
const persistDocumentHistories = (histories: Record<string, DocumentHistoryEntry[]>) => {
  if (Object.keys(histories).length === 0) {
    localStorage.removeItem(DOCUMENT_HISTORY_STORAGE_KEY);
  } else {
    localStorage.setItem(DOCUMENT_HISTORY_STORAGE_KEY, JSON.stringify(histories));
  }
};
```

---

## 📡 WebSocket 集成

### 连接管理

```typescript
// services/websocket.ts
export function createSessionSocket(sessionId: string): WebSocket {
  const baseURL = import.meta.env.VITE_API_URL || window.location.origin;
  const wsURL = baseURL.replace(/^http/, 'ws');
  const socket = io(`${wsURL}/ws/sessions/${sessionId}`, {
    transports: ['websocket'],
    reconnection: true,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 5000,
    reconnectionAttempts: 5,
  });
  
  return socket;
}
```

### 消息处理逻辑

```typescript
// pages/Home.tsx
socket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  updateActivityTime();  // 收到消息时更新活动时间
  
  if (data.type === 'agent_message') {
    const message = {
      sender: data.sender ?? 'Agent',
      stage: data.stage ?? 'unknown',
      content: data.content ?? '',
      payload: data.payload,
      progress: data.progress ?? 0,
      needsConfirmation: data.needs_confirmation ?? false,
      confirmed: false,
      editable: true,
      durationSeconds: data.duration_seconds ?? null,
    };
    
    // 流式消息（is_streaming=true）：追加到现有结果
    // 非流式消息：创建新结果
    if (data.is_streaming === true) {
      appendAgentResult(message);
    } else {
      addAgentResult(message);
    }
    
    // 更新进度
    setProgress(data.progress ?? 0, data.stage);
    
    // 自动切换到新阶段
    if (data.stage && shouldAutoSwitch(data.stage)) {
      setSelectedStage(data.stage);
    }
  } else if (data.type === 'system_message') {
    addSystemMessage(data.content ?? '');
    setProgress(data.progress ?? 0, data.stage);
  }
};
```

### 流式消息追加逻辑

```typescript
// stores/chatStore.ts
appendAgentResult: (result) =>
  set((state) => {
    const results = state.agentResults;
    
    // 从后往前找最近的同sender+stage且未确认的项
    let idx = -1;
    for (let i = results.length - 1; i >= 0; i--) {
      if (results[i].sender === result.sender && 
          results[i].stage === result.stage && 
          !results[i].confirmed) {
        idx = i;
        break;
      }
    }
    
    if (idx >= 0) {
      // 找到了，追加内容
      const target = results[idx];
      const prevText = String(target.content || '');
      const newText = String(result.content || '');
      
      let mergedContent: string;
      if (!prevText) {
        mergedContent = newText;
      } else if (newText.includes(prevText)) {
        // 新内容包含旧内容，替换避免重复
        mergedContent = newText;
      } else {
        // 追加新内容
        mergedContent = `${prevText}\n${newText}`;
      }
      
      const merged = {
        ...target,
        content: mergedContent,
        payload: result.payload ?? target.payload,
        needsConfirmation: result.needsConfirmation || target.needsConfirmation,
      };
      
      const next = results.slice();
      next[idx] = merged;
      return { agentResults: next };
    }
    
    // 否则创建新结果
    return {
      agentResults: [...results, { ...result, id: nanoid(), timestamp: Date.now() }]
    };
  }),
```

---

## 🎨 核心组件实现

### 1. FileUploader 组件

```typescript
// components/FileUploader.tsx
const FileUploader: React.FC = () => {
  const { documents, addDocument } = useAppStore();
  const [uploading, setUploading] = useState(false);
  
  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    setUploading(true);
    for (const file of acceptedFiles) {
      try {
        const response = await uploadDocument(file);
        const document: Document = {
          id: response.document_id,
          original_name: response.original_name,
          size: response.size,
          checksum: response.checksum,
        };
        addDocument(document);
        
        // 触发自定义事件（供Home组件自动选中）
        window.dispatchEvent(new CustomEvent('document_uploaded', {
          detail: { id: document.id }
        }));
        
        message.success(`已上传: ${file.name}`);
      } catch (error) {
        message.error(`上传失败: ${file.name}`);
      }
    }
    setUploading(false);
  }, [addDocument]);
  
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'image/*': ['.png', '.jpg', '.jpeg', '.bmp', '.gif']
    },
    maxSize: 10 * 1024 * 1024,  // 10MB
    multiple: true,
  });
  
  return (
    <div {...getRootProps()} style={{ border: '2px dashed #d9d9d9', padding: 24 }}>
      <input {...getInputProps()} />
      {uploading ? <Spin /> : (
        isDragActive ? <p>拖放文件到这里...</p> : <p>拖拽文件到这里，或点击选择文件</p>
      )}
    </div>
  );
};
```

### 2. AgentFlowProgress 组件

```typescript
// components/AgentFlowProgress.tsx
const STAGES = [
  { key: 'requirement_analysis', title: '需求分析' },
  { key: 'test_generation', title: '用例生成' },
  { key: 'review', title: '质量评审' },
  { key: 'test_completion', title: '用例补全' },
  { key: 'completed', title: '完成' },
];

const AgentFlowProgress: React.FC<{
  currentStage: string | null;
  progress: number;
  selectedStage: string | null;
  onStageClick: (stage: string) => void;
}> = ({ currentStage, progress, selectedStage, onStageClick }) => {
  const currentIndex = STAGES.findIndex(s => s.key === currentStage);
  
  return (
    <Steps
      current={currentIndex}
      percent={Math.round(progress * 100)}
      items={STAGES.map(stage => ({
        title: stage.title,
        status: selectedStage === stage.key ? 'process' : undefined,
        onClick: () => onStageClick(stage.key),
      }))}
    />
  );
};
```

### 3. AgentTimeline 组件

```typescript
// components/AgentTimeline.tsx
const AgentTimeline: React.FC = () => {
  const { agentResults, selectedStage } = useAppStore();
  
  // 过滤当前选中阶段的结果
  const filteredResults = agentResults.filter(r => r.stage === selectedStage);
  
  // 根据阶段渲染不同的视图
  const renderView = (result: AgentResult) => {
    switch (result.stage) {
      case 'requirement_analysis':
        return <RequirementAnalysisView payload={result.payload} />;
      case 'test_generation':
        return <TestCasesView payload={result.payload} />;
      case 'review':
        return <QualityReviewView payload={result.payload} />;
      case 'test_completion':
        return <SupplementalTestCasesView payload={result.payload} />;
      case 'completed':
        return <TestCasesView payload={result.payload} />;
      default:
        return <ReactMarkdown>{String(result.content)}</ReactMarkdown>;
    }
  };
  
  return (
    <div style={{ overflowY: 'auto', height: '100%' }}>
      {filteredResults.length === 0 ? (
        <Empty description="暂无数据" />
      ) : (
        filteredResults.map(result => (
          <Card key={result.id} style={{ marginBottom: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography.Text strong>{result.sender}</Typography.Text>
              {result.durationSeconds && (
                <Typography.Text type="secondary">
                  耗时: {result.durationSeconds}s
                </Typography.Text>
              )}
            </div>
            {renderView(result)}
            {result.needsConfirmation && !result.confirmed && (
              <ConfirmationCard result={result} />
            )}
          </Card>
        ))
      )}
    </div>
  );
};
```

### 4. TestCasesView 组件（表格展示）

```typescript
// components/TestCasesView.tsx
const TestCasesView: React.FC<{ payload?: Record<string, unknown> }> = ({ payload }) => {
  if (!payload || !payload.modules) {
    return <Empty description="暂无测试用例" />;
  }
  
  const modules = payload.modules as Array<{
    name: string;
    cases: Array<{
      id: string;
      title: string;
      preconditions?: string;
      steps?: string;
      expected?: string;
      priority?: string;
    }>;
  }>;
  
  return (
    <Collapse accordion>
      {modules.map((module, idx) => (
        <Collapse.Panel key={idx} header={`${module.name} (${module.cases.length}条)`}>
          <Table
            dataSource={module.cases}
            rowKey="id"
            pagination={false}
            columns={[
              { title: '用例ID', dataIndex: 'id', width: 150 },
              { title: '标题', dataIndex: 'title', width: 200 },
              { title: '前置条件', dataIndex: 'preconditions', ellipsis: true },
              { title: '测试步骤', dataIndex: 'steps', ellipsis: true },
              { title: '预期结果', dataIndex: 'expected', ellipsis: true },
              { title: '优先级', dataIndex: 'priority', width: 100 },
            ]}
          />
        </Collapse.Panel>
      ))}
    </Collapse>
  );
};
```

### 5. ConfirmationCard 组件（人工确认）

```typescript
// components/ConfirmationCard.tsx
const ConfirmationCard: React.FC<{ result: AgentResult }> = ({ result }) => {
  const { sendConfirmation, confirmAgentResult } = useAppStore();
  const [editing, setEditing] = useState(false);
  const [editedPayload, setEditedPayload] = useState(result.payload);
  
  const handleConfirm = () => {
    sendConfirmation(result.id, result.stage, editedPayload);
    confirmAgentResult(result.id);
    message.success('已确认');
  };
  
  const handleReject = () => {
    sendConfirmation(result.id, result.stage, undefined);
    message.info('已拒绝');
  };
  
  return (
    <Alert
      message="需要人工确认"
      description={
        <div>
          {editing && (
            <Input.TextArea
              value={JSON.stringify(editedPayload, null, 2)}
              onChange={(e) => {
                try {
                  setEditedPayload(JSON.parse(e.target.value));
                } catch {}
              }}
              rows={10}
            />
          )}
          <Space style={{ marginTop: 16 }}>
            <Button type="primary" onClick={handleConfirm}>确认</Button>
            <Button danger onClick={handleReject}>拒绝</Button>
            {result.editable && (
              <Button onClick={() => setEditing(!editing)}>
                {editing ? '取消编辑' : '编辑'}
              </Button>
            )}
          </Space>
        </div>
      }
      type="warning"
      showIcon
    />
  );
};
```

---

## 🔄 核心业务流程

### 1. 开始分析流程

```typescript
// pages/Home.tsx
const handleStartAnalysis = async () => {
  if (!selectedDocId) {
    message.warning('请先选择需要分析的文档');
    return;
  }
  
  // 1. 设置加载状态
  setAnalysisRunning(true);
  setSelectedStage('requirement_analysis');
  setProgress(0.12, 'requirement_analysis');
  
  // 2. 清除旧结果
  clearAnalysisResults();
  
  try {
    // 3. 创建会话
    const payload = {
      document_ids: [selectedDocId],
      config: {}
    };
    const response = await createSession(payload);
    const detail = await fetchSessionDetail(response.session_id);
    setSession(detail);  // 触发WebSocket连接
    
    addSystemMessage('分析会话已创建，开始排队执行智能体。');
  } catch (error) {
    message.error(`创建分析会话失败: ${error.message}`);
    setAnalysisRunning(false);
    setProgress(0, null);
  }
};
```

### 2. 取消分析流程

```typescript
const handleCancelAnalysis = () => {
  // 1. 清除超时定时器
  clearInactivityTimer();
  
  // 2. 停止分析状态
  setAnalysisRunning(false);
  setConnecting(false);
  
  // 3. 关闭WebSocket
  if (socketRef.current) {
    socketRef.current.close();
    socketRef.current = null;
  }
  
  // 4. 重置状态
  resetAnalysis();
  
  // 5. 清除历史记录
  if (selectedDocId) {
    clearDocumentHistory(selectedDocId);
  }
  
  message.success('已取消当前分析');
};
```

### 3. 历史记录恢复

```typescript
// pages/Home.tsx
useEffect(() => {
  if (!selectedDocId) return;
  
  // 如果WebSocket连接活跃，不恢复历史记录
  const activeSocket = socketRef.current;
  if (activeSocket && activeSocket.readyState !== WebSocket.CLOSED) {
    return;
  }
  
  // 恢复最近的历史记录
  const historyEntries = documentHistories[selectedDocId] ?? [];
  if (historyEntries.length > 0) {
    const latest = historyEntries[0];
    setAgentResults(latest.agentResults);
    setProgress(1, 'completed');
    
    // 智能选择默认阶段
    const availableStages = new Set(latest.agentResults.map(r => r.stage));
    const stagePriority = ['completed', 'test_completion', 'review', 'test_generation', 'requirement_analysis'];
    const defaultStage = stagePriority.find(stage => availableStages.has(stage)) || 'requirement_analysis';
    setSelectedStage(defaultStage);
  }
}, [selectedDocId, documentHistories]);
```

### 4. 超时管理

```typescript
// 10分钟无操作自动断开
const INACTIVITY_TIMEOUT = 10 * 60 * 1000;

const resetInactivityTimer = () => {
  clearInactivityTimer();
  
  // completed阶段不启动超时
  if (currentStage === 'completed') return;
  
  inactivityTimerRef.current = setTimeout(() => {
    if (analysisRunning || session) {
      handleCancelAnalysis(true);  // isTimeout=true
    }
  }, INACTIVITY_TIMEOUT);
};

// 用户活动时更新时间
useEffect(() => {
  if (lastActivityTime > 0 && (analysisRunning || session)) {
    resetInactivityTimer();
  }
}, [lastActivityTime]);
```

---

## 📱 响应式设计

### useMediaQuery Hook

```typescript
// hooks/useMediaQuery.ts
export const useMediaQuery = (query: string): boolean => {
  const [matches, setMatches] = useState(false);
  
  useEffect(() => {
    const mediaQuery = window.matchMedia(query);
    setMatches(mediaQuery.matches);
    
    const listener = (e: MediaQueryListEvent) => setMatches(e.matches);
    mediaQuery.addEventListener('change', listener);
    
    return () => mediaQuery.removeEventListener('change', listener);
  }, [query]);
  
  return matches;
};

// 使用示例
const isMobile = useMediaQuery('(max-width: 767px)');
```

### 移动端适配

```typescript
// pages/Home.tsx
<div style={{
  display: 'flex',
  flexDirection: isMobile ? 'column' : 'row',
  gap: isMobile ? 12 : 16,
}}>
  <div style={{
    flex: isMobile ? '0 0 auto' : '0 0 30%',
    minWidth: isMobile ? 'auto' : 360,
  }}>
    {/* 文件上传区域 */}
  </div>
  <div style={{
    flex: isMobile ? 1 : 1.7,
  }}>
    {/* 流程进度和结果展示区域 */}
  </div>
</div>
```

---

## 🎨 样式与主题

### 全局样式

```css
/* styles/global.css */
.no-scrollbar::-webkit-scrollbar {
  display: none;
}

.no-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

/* Markdown样式 */
.markdown-content h2 {
  margin-top: 24px;
  margin-bottom: 16px;
  font-size: 20px;
  font-weight: 600;
}

.markdown-content table {
  border-collapse: collapse;
  width: 100%;
  margin: 16px 0;
}

.markdown-content table th,
.markdown-content table td {
  border: 1px solid #d9d9d9;
  padding: 8px 12px;
  text-align: left;
}
```

### Ant Design 主题配置

```typescript
// App.tsx
import zhCN from 'antd/locale/zh_CN';

<ConfigProvider locale={zhCN}>
  <Layout style={{ height: '100vh' }}>
    <Content>
      <HomePage />
    </Content>
  </Layout>
</ConfigProvider>
```

---

## 🚀 启动与运行

```bash
# 安装依赖
cd frontend
npm install

# 配置环境变量
cp .env.example .env
# 编辑.env，配置VITE_API_URL

# 运行开发服务器
npm run dev
```

访问: http://localhost:3000

---

## 🐛 调试与优化

### 1. WebSocket 调试

```typescript
// 添加详细日志
socket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('[WebSocket] 收到消息:', {
    type: data.type,
    stage: data.stage,
    sender: data.sender,
    hasPayload: !!data.payload,
    payloadKeys: data.payload ? Object.keys(data.payload) : null,
  });
  
  // 处理消息...
};
```

### 2. 性能优化

- **Zustand 选择器**: 使用浅比较避免不必要的重渲染
- **React.memo**: 包装纯组件减少渲染
- **useMemo/useCallback**: 缓存计算结果和回调函数
- **虚拟滚动**: 测试用例列表使用虚拟滚动（react-window）

### 3. 错误边界

```typescript
// ErrorBoundary.tsx
class ErrorBoundary extends React.Component<Props, State> {
  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('React Error:', error, info);
    message.error('页面渲染出错，请刷新重试');
  }
  
  render() {
    if (this.state.hasError) {
      return <Result status="500" title="出错了" />;
    }
    return this.props.children;
  }
}
```

---

## 📚 开发最佳实践

1. **类型安全**: 所有API响应和状态都使用TypeScript类型定义
2. **错误处理**: 使用try-catch捕获异常，并通过message.error提示用户
3. **用户体验**: 加载状态、空状态、错误状态都有友好提示
4. **代码复用**: 公共逻辑抽取为自定义Hooks
5. **性能优化**: 使用Zustand浅比较、React.memo、useMemo等优化手段

---

**本文档基于真实项目代码提取，可直接用于AI辅助开发或团队协作。**
