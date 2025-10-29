# AI Needs 开发指南

> 从环境搭建到部署上线的完整开发指南

## 📋 目录

- [环境搭建](#环境搭建)
- [配置说明](#配置说明)
- [开发流程](#开发流程)
- [API 文档](#api-文档)
- [数据流图](#数据流图)
- [故障排查](#故障排查)
- [部署指南](#部署指南)

---

## 🛠️ 环境搭建

### 系统要求

- **操作系统**: Linux / macOS / Windows (WSL2推荐)
- **Python**: 3.10+
- **Node.js**: 16+
- **Redis**: 5.0+ (可选，用于生产环境)
- **Docker**: 20.10+ (可选，用于容器化部署)

### 后端环境

```bash
# 1. 克隆项目
git clone <repository-url>
cd ai_needs/backend

# 2. 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env，配置 QWEN_API_KEY

# 5. 初始化数据库
# FastAPI会在启动时自动创建数据库表

# 6. 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端环境

```bash
# 1. 进入前端目录
cd frontend

# 2. 安装依赖
npm install

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env，配置 VITE_API_URL

# 4. 启动开发服务器
npm run dev
```

### Redis 启动（可选）

```bash
# macOS (Homebrew)
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# Docker
docker run -d -p 6379:6379 redis:7-alpine
```

---

## ⚙️ 配置说明

### 后端环境变量 (.env)

#### 基础配置

```bash
# 应用配置
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=false
```

#### LLM 模型配置

```bash
# 通义千问基础配置
QWEN_API_KEY=sk-xxxxxxxxxxxxx
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-plus
```

#### VL 模型配置（图片识别）

```bash
# 是否启用VL模型进行图片识别
VL_ENABLED=true

# VL模型名称（用于快速图片识别）
VL_MODEL=qwen3-vl-flash

# VL模型API Key（默认使用QWEN_API_KEY）
# VL_API_KEY=

# VL模型base URL（默认使用QWEN_BASE_URL）
# VL_BASE_URL=
```

#### PDF OCR 专用配置

```bash
# 是否对PDF使用专用OCR模型
PDF_OCR_ENABLED=true

# PDF专用OCR模型
PDF_OCR_MODEL=qwen-vl-ocr-2025-08-28

# PDF OCR模型API Key（默认使用QWEN_API_KEY）
# PDF_OCR_API_KEY=

# PDF OCR模型base URL（默认使用QWEN_BASE_URL）
# PDF_OCR_BASE_URL=
```

#### 智能体专用配置

```bash
# 需求分析师配置
ANALYSIS_AGENT_MODEL=qwen3-vl-flash
# ANALYSIS_AGENT_API_KEY=  # 默认使用QWEN_API_KEY
# ANALYSIS_AGENT_BASE_URL=  # 默认使用QWEN_BASE_URL

# 是否启用多模态分析（直接处理图片，保留视觉信息）
ANALYSIS_MULTIMODAL_ENABLED=false

# 测试工程师配置
TEST_AGENT_MODEL=qwen3-next-80b-a3b-instruct
# TEST_AGENT_API_KEY=
# TEST_AGENT_BASE_URL=

# 质量评审专家配置
REVIEW_AGENT_MODEL=qwen3-next-80b-a3b-instruct
# REVIEW_AGENT_API_KEY=
# REVIEW_AGENT_BASE_URL=
```

#### 数据库与缓存配置

```bash
# 数据库URL（支持SQLite和PostgreSQL）
DATABASE_URL=sqlite+aiosqlite:///./ai_requirement.db
# 生产环境使用PostgreSQL:
# DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/ai_needs

# Redis URL（用于缓存和WebSocket事件存储）
REDIS_URL=redis://localhost:6379/0

# 会话配置
SESSION_TTL_HOURS=72
SESSION_CLEANUP_INTERVAL=3600
```

#### 文件上传配置

```bash
# 最大文件大小（字节，默认10MB）
MAX_FILE_SIZE=10485760

# 上传目录
UPLOAD_DIR=/tmp/uploads

# LLM超时时间（秒）
LLM_TIMEOUT=120
```

### 前端环境变量 (.env)

```bash
# 后端API地址
VITE_API_URL=http://localhost:8000
```

---

## 🔄 开发流程

### 1. 本地开发

#### 后端开发流程

```bash
# 1. 启动Redis（如果使用）
redis-server

# 2. 启动后端（自动重载）
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 3. 查看日志
tail -f app.log

# 4. 访问API文档
open http://localhost:8000/docs
```

#### 前端开发流程

```bash
# 1. 启动前端（自动重载）
cd frontend
npm run dev

# 2. 访问应用
open http://localhost:3000
```

### 2. 代码规范

#### Python 代码规范

- 使用 `black` 格式化代码
- 使用 `mypy` 进行类型检查
- 使用 `pylint` 进行代码质量检查

```bash
# 格式化代码
black app/

# 类型检查
mypy app/

# 代码质量检查
pylint app/
```

#### TypeScript 代码规范

- 使用 `prettier` 格式化代码
- 使用 `eslint` 进行代码质量检查

```bash
# 格式化代码
npm run format

# 代码质量检查
npm run lint
```

### 3. Git 工作流

```bash
# 1. 创建功能分支
git checkout -b feature/your-feature-name

# 2. 提交代码
git add .
git commit -m "feat: add your feature description"

# 3. 推送到远程
git push origin feature/your-feature-name

# 4. 创建Pull Request
# 在GitHub/GitLab上创建PR

# 5. 合并到main分支
# 代码审查通过后合并
```

---

## 📡 API 文档

### 1. 文档上传

**POST** `/api/uploads`

**请求**:
- Content-Type: `multipart/form-data`
- Body: `file` (文件，最大10MB)

**响应**:
```json
{
  "document_id": "uuid",
  "original_name": "需求文档.pdf",
  "size": 1234567,
  "checksum": "sha256_hash"
}
```

**错误码**:
- `400`: 文件过大或格式不支持
- `500`: 服务器内部错误

---

### 2. 创建分析会话

**POST** `/api/sessions`

**请求**:
```json
{
  "document_ids": ["doc_uuid_1", "doc_uuid_2"],
  "config": {}
}
```

**响应**:
```json
{
  "session_id": "session_uuid",
  "status": "created"
}
```

**错误码**:
- `404`: 文档不存在
- `500`: 服务器内部错误

---

### 3. 获取会话详情

**GET** `/api/sessions/{session_id}`

**响应**:
```json
{
  "id": "session_uuid",
  "status": "processing",
  "current_stage": "requirement_analysis",
  "progress": 0.3,
  "documents": [
    {
      "id": "doc_uuid",
      "original_name": "需求文档.pdf",
      "size": 1234567
    }
  ],
  "created_at": "2025-01-01T00:00:00",
  "last_activity_at": "2025-01-01T00:05:00"
}
```

---

### 4. 获取会话结果

**GET** `/api/sessions/{session_id}/results`

**响应**:
```json
{
  "summary": {
    "modules": [
      {
        "name": "用户登录模块",
        "scenarios": [
          {"description": "用户通过手机号+验证码登录"}
        ],
        "rules": [
          {"description": "验证码有效期5分钟"}
        ]
      }
    ]
  },
  "test_cases": {
    "modules": [
      {
        "name": "用户登录模块",
        "cases": [
          {
            "id": "TC-LOGIN-001",
            "title": "手机号验证码登录",
            "preconditions": "用户未登录",
            "steps": "1. 输入手机号\n2. 获取验证码\n3. 输入验证码\n4. 点击登录",
            "expected": "登录成功",
            "priority": "HIGH"
          }
        ]
      }
    ]
  }
}
```

---

### 5. 导出XMind

**POST** `/api/sessions/{session_id}/exports/xmind`

**请求**:
```json
{
  "result_version": 1
}
```

**响应**: 
- Content-Type: `application/octet-stream`
- 文件下载: `test_cases_{session_id}.xmind`

---

### 6. WebSocket 连接

**WebSocket** `/ws/sessions/{session_id}`

**客户端接收消息**:

1. **agent_message** (智能体输出结果)
```json
{
  "type": "agent_message",
  "sender": "需求分析师",
  "stage": "requirement_analysis",
  "content": "需求分析完成",
  "payload": {"modules": [...]},
  "progress": 0.3,
  "needs_confirmation": true,
  "is_streaming": false,
  "timestamp": 1234567890.123
}
```

2. **system_message** (系统提示)
```json
{
  "type": "system_message",
  "sender": "系统",
  "stage": "system",
  "content": "分析流程已开始",
  "progress": 0.12,
  "timestamp": 1234567890.123
}
```

**客户端发送确认**:
```json
{
  "type": "confirm_agent",
  "stage": "requirement_analysis",
  "result_id": "result_uuid",
  "confirmed": true,
  "payload": {...}
}
```

---

## 🔍 数据流图

### 完整分析流程

```
用户上传文档
    ↓
[POST /api/uploads]
    ↓
返回 document_id
    ↓
用户点击"开始分析"
    ↓
[POST /api/sessions] (传入 document_ids)
    ↓
创建 Session 记录
    ↓
后台启动工作流
    ↓
┌─────────────────────────────────────┐
│  工作流编排 (workflow.py)            │
│                                      │
│  1. 准备文档数据                     │
│     - 提取文本 / VL识别图片          │
│                                      │
│  2. 阶段1: 需求分析                  │
│     - AutoGen调用需求分析师          │
│     - WebSocket推送结果              │
│     - 等待人工确认                   │
│                                      │
│  3. 阶段2: 测试用例生成              │
│     - AutoGen调用测试工程师          │
│     - Markdown解析为JSON             │
│     - WebSocket推送结果              │
│     - 等待人工确认                   │
│                                      │
│  4. 阶段3: 质量评审                  │
│     - AutoGen调用质量评审专家        │
│     - WebSocket推送结果              │
│     - 等待人工确认                   │
│                                      │
│  5. 阶段4: 用例补全                  │
│     - AutoGen调用测试补全工程师      │
│     - Markdown解析为JSON             │
│     - WebSocket推送结果              │
│     - 等待人工确认                   │
│                                      │
│  6. 合并测试用例                     │
│     - 合并阶段2和阶段4的用例         │
│     - 保存到 SessionResult 表        │
│     - WebSocket推送completed事件     │
└─────────────────────────────────────┘
    ↓
前端接收WebSocket消息
    ↓
更新UI展示结果
    ↓
用户可导出XMind
```

### WebSocket 消息流

```
前端                           后端
  |                              |
  |--- WebSocket连接 ----------->|
  |                              |
  |<-- 历史事件推送 -------------|
  |                              |
  |<-- agent_message (阶段1) ----|
  |    {stage: "requirement_     |
  |     analysis", payload: ...} |
  |                              |
  |--- confirm_agent ----------->|
  |    {stage: "requirement_     |
  |     analysis", confirmed:    |
  |     true, payload: ...}      |
  |                              |
  |<-- agent_message (阶段2) ----|
  |                              |
  |--- confirm_agent ----------->|
  |                              |
  |      ... 重复 ...             |
  |                              |
  |<-- agent_message (完成) -----|
  |    {stage: "completed",      |
  |     progress: 1.0}           |
  |                              |
  |--- WebSocket关闭 ----------->|
```

---

## 🐛 故障排查

### 常见问题

#### 1. Redis 连接失败

**症状**: 
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**解决方案**:
```bash
# 检查Redis是否运行
redis-cli ping  # 应返回 PONG

# 检查Redis配置
cat .env | grep REDIS_URL

# 启动Redis
redis-server

# 或使用Docker
docker run -d -p 6379:6379 redis:7-alpine
```

---

#### 2. LLM API 调用失败

**症状**:
```
openai.error.AuthenticationError: Incorrect API key provided
```

**解决方案**:
```bash
# 检查API Key是否配置
cat .env | grep QWEN_API_KEY

# 测试API Key是否有效
curl -X POST "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions" \
  -H "Authorization: Bearer $QWEN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen-plus", "messages": [{"role": "user", "content": "你好"}]}'
```

---

#### 3. 文档解析失败

**症状**:
```
FileNotFoundError: [Errno 2] No such file or directory
```

**解决方案**:
```bash
# 检查上传目录是否存在
mkdir -p /tmp/uploads

# 检查文件权限
chmod 755 /tmp/uploads

# 检查磁盘空间
df -h
```

---

#### 4. WebSocket 连接断开

**症状**: 前端显示 "实时通道已关闭"

**解决方案**:
```bash
# 检查后端日志
tail -f backend/app.log

# 检查nginx配置（如果使用）
# 需要添加WebSocket支持:
# proxy_http_version 1.1;
# proxy_set_header Upgrade $http_upgrade;
# proxy_set_header Connection "upgrade";

# 检查防火墙规则
sudo ufw status
```

---

#### 5. 多模态模型调用失败

**症状**:
```
dashscope.common.error.UnsupportedModel: qwen3-vl-flash is not available
```

**解决方案**:
```bash
# 检查模型配置
cat .env | grep VL_MODEL

# 使用备用模型
VL_MODEL=qwen-vl-plus

# 检查API文档确认可用模型
# https://help.aliyun.com/zh/model-studio/
```

---

### 调试技巧

#### 1. 启用详细日志

```bash
# backend/.env
DEBUG=true

# 查看日志
tail -f backend/app.log | grep ERROR
```

#### 2. 使用API文档测试

```bash
# 访问Swagger UI
open http://localhost:8000/docs

# 使用curl测试API
curl -X POST "http://localhost:8000/api/uploads" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test.pdf"
```

#### 3. 前端控制台调试

```typescript
// 在前端代码中添加调试日志
console.log('[Debug] WebSocket message:', data);
console.log('[Debug] Current state:', useAppStore.getState());
```

---

## 🚀 部署指南

### Docker 部署

#### 1. 构建镜像

```bash
# 构建后端镜像
cd backend
docker build -t ai-needs-backend:latest .

# 构建前端镜像
cd frontend
docker build -t ai-needs-frontend:latest .
```

#### 2. 使用 Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data

  backend:
    image: ai-needs-backend:latest
    ports:
      - "8000:8000"
    environment:
      - QWEN_API_KEY=${QWEN_API_KEY}
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=sqlite+aiosqlite:////app/data/ai_requirement.db
    volumes:
      - ./data:/app/data
      - ./uploads:/app/uploads
    depends_on:
      - redis

  frontend:
    image: ai-needs-frontend:latest
    ports:
      - "3000:80"
    environment:
      - VITE_API_URL=http://localhost:8000

volumes:
  redis-data:
```

#### 3. 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

---

### 生产环境部署

#### 1. 使用 Nginx 反向代理

```nginx
# /etc/nginx/sites-available/ai-needs
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /var/www/ai-needs-frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # 后端API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

#### 2. 使用 Systemd 管理服务

```ini
# /etc/systemd/system/ai-needs-backend.service
[Unit]
Description=AI Needs Backend Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/ai-needs/backend
Environment="PATH=/opt/ai-needs/backend/.venv/bin"
ExecStart=/opt/ai-needs/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# 启动服务
sudo systemctl enable ai-needs-backend
sudo systemctl start ai-needs-backend

# 查看状态
sudo systemctl status ai-needs-backend
```

#### 3. 数据库备份

```bash
# SQLite备份
cp backend/ai_requirement.db backend/ai_requirement.db.backup

# PostgreSQL备份
pg_dump -U user -d ai_needs > backup.sql

# 定时备份（crontab）
0 2 * * * /usr/local/bin/backup-database.sh
```

---

## 📊 监控与日志

### 日志配置

```python
# backend/app/utils/logger.py
import logging
from logging.handlers import RotatingFileHandler

def configure_logging(level: str = "INFO"):
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # 文件日志（自动轮转）
    file_handler = RotatingFileHandler(
        "app.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    
    # 控制台日志
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # 配置根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
```

### 性能监控

```bash
# 使用 htop 监控系统资源
htop

# 使用 nethogs 监控网络流量
sudo nethogs

# 使用 redis-cli 监控Redis
redis-cli --stat

# 查看进程状态
ps aux | grep uvicorn
```

---

**祝你开发顺利！如有问题，请参考[故障排查](#故障排查)章节或提交Issue。**
