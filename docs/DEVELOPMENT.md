# PCBTool-Rev 开发文档

## 1. 项目架构

本项目采用现代化的前后端分离架构，确保了高度的可扩展性和可维护性。

- **后端 (Backend)**: 使用 FastAPI 构建，负责处理所有业务逻辑、与 AI 服务交互、数据库管理和提供 RESTful API。
- **前端 (Frontend)**: 使用 Vue.js 构建的单页应用 (SPA)，负责用户界面和用户交互，通过 API 与后端通信。

---

## 2. 后端详解

### 2.1. 目录结构

```
backend/
├── app/
│   ├── api/
│   │   └── endpoints.py      # API 路由和端点实现
│   ├── core/
│   │   └── config.py         # 配置文件 (API密钥, 数据库URL等)
│   ├── db/
│   │   ├── crud.py           # 数据库增删改查操作
│   │   ├── database.py       # SQLAlchemy 引擎和会话设置
│   │   └── models.py         # 数据库表模型
│   ├── models/
│   │   └── schemas.py        # Pydantic 数据验证模型
│   ├── services/
│   │   ├── component_service.py # 组件分析和商城搜索逻辑
│   │   ├── dify_service.py     # 与 Dify API 交互的逻辑
│   │   └── guide_service.py    # 部署指南和TTS生成逻辑
│   └── main.py               # FastAPI 应用入口
├── .env.example              # 环境变量示例文件
├── static/
│   └── audio/                # 存放生成的音频文件
└── requirements.txt          # Python 依赖
```

### 2.2. 核心逻辑

- **流式响应 (Streaming)**: 对于所有耗时较长的 AI 生成任务，后端使用 FastAPI 的 `StreamingResponse` 将 Dify API 的 Server-Sent Events (SSE) 直接转发给前端。这使得前端可以实时显示进度（如 "节点开始"）和逐步生成的文本，极大地改善了用户体验。
- **配置管理**: 使用 `.env` 文件进行本地开发的环境变量管理，通过 `python-dotenv` 加载。`config.py` 从环境变量中读取配置，使得 API 密钥等敏感信息的管理更加安全和灵活。

---

## 3. API 端点文档

所有 API 的基础路径为 `/api/v1`。

### 3.1. 获取会话历史
- **Endpoint**: `GET /conversations`
- **描述**: 获取默认用户的所有会话历史，按时间倒序排列。
- **成功响应 (200 OK)**: `List[Conversation]`

### 3.2. 开始新会话 (流式)
- **Endpoint**: `POST /conversations/stream`
- **描述**: 创建一个新会话。用户可以上传图片、输入文本，或两者都提供。后端以流式响应转发 Dify ��作流的事件。
- **请求类型**: `multipart/form-data`
- **成功响应**: 一个 `text/event-stream` 数据流。

### 3.3. 分析元器件
- **Endpoint**: `POST /conversations/{conversation_id}/analyze-components`
- **描述**: 基于初次分析生成的 BOM，对其进行结构化处理。**注意**: 此端点为历史遗留，新功能已集成到流式端点中，但为保证向后兼容性而保留。
- **请求类型**: `application/json`
- **成功响应 (200 OK)**: `MessageResponse`

### 3.4. 生成代码 (流式)
- **Endpoint**: `POST /conversations/{conversation_id}/generate-code/stream`
- **描述**: 根据需求文档和 BOM，流式生成代码。
- **请求类型**: `application/json`
- **成功响应**: 一个 `text/event-stream` 数据流。

### 3.5. 生成部署指南 (流式)
- **Endpoint**: `POST /conversations/{conversation_id}/generate-deployment-guide/stream`
- **描述**: 根据需求文档和 BOM，流式生成部署指南。
- **请求类型**: `application/json`
- **成功响应**: 一个 `text/event-stream` 数据流。

### 3.6. 生成原理图代码 (流式)
- **Endpoint**: `POST /conversations/{conversation_id}/generate-schematic/stream`
- **描述**: 根据需求文档和 BOM，流式生成原理图代码。
- **请求类型**: `application/json`
- **成功响应**: 一个 `text/event-stream` 数据流。

### 3.7. 删除会话
- **Endpoint**: `DELETE /conversations/{conversation_id}`
- **描述**: 删除指定ID的会话。
- **成功响应 (204 No Content)**

---

## 4. 前端详解

### 4.1. 核心逻辑
- **流式处理**: `api.js` 中使用原生的 `fetch` API 来处理 `text/event-stream` 响应。`chat.js` store 中定义了 `onStreamEvent` 回调函数，用于解析 SSE 事件并实时更新 Pinia state。
- **响应式UI**: `MessageRenderer.vue` 组件根据消息的 `type` 和 `data` 动态渲染。对于流式消息，它会先显示一个加载动画，然后随着 `data.streamedContent` 的更新而实时展示文本，提供了优秀的实时反馈。
- **会话管理**:
  - `App.vue` 在 `onMounted`生命周期钩子中调用 `fetchHistory` action 来加载历史记录。
  - “新建”按钮通过调用 `startNewConversation` action 来重置视图。
  - “删除”按钮调用 `deleteConversation` action，该 action 会发送 API 请求并在成功后从本地 state 中移除该会话。

### 4.2. 未来开发建议
- **UI/UX 打磨**:
  - 对代码块增加语法高亮 (如使用 `highlight.js`)。
  - 优化加载和错误状态的视觉反馈。
- **功能扩展**:
  - 增加会话的重命名功能。
  - 实现对历史消息的编辑和重新生成。
  - 将BOM表中的单价变为可���辑，以便用户手动输入价格并重新计算总价。
