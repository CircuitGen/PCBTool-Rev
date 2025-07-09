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
├── static/
│   └── audio/                # 存放生成的音频文件
└── requirements.txt          # Python 依赖
```

### 2.2. 数据库模型

- **User**: 存储用户信息 (当前为默认用户)。
- **Conversation**: 存储会话信息，关联到用户。
- **Message**: 存储每条消息，关联到会话。消息内容 (`content`) 是一个 JSON 字符串，可以灵活存储不同类型的数据（如分析结果、代码、指南等）。

---

## 3. API 端点文档

所有 API 的基础路径为 `/api/v1`。

### 3.1. 开始新会话 (分析图片/文本)

- **Endpoint**: `POST /conversations`
- **描述**: 创建一个新会话。用户可以上传图片、输入文本，或两者都提供。后端调用 Dify 工作流进行分析，并将结果作为第一条消息存入数据库。
- **请求类型**: `multipart/form-data`
- **表单数据 (可选)**:
  - `image`: (file) 用户上传的图片文件。
  - `text_input`: (string) 用户的初始文本提示。
  - *注意*: `image` 和 `text_input` 至少需要提供一个。
- **成功响应 (200 OK)**:
  ```json
  {
    "conversation_id": 1,
    "message": {
      "id": 1,
      "role": "assistant",
      "content": {
        "type": "initial_analysis",
        "data": {
          "BOM文件": "...",
          "需求文档": "..."
        }
      },
      "created_at": "..."
    }
  }
  ```

### 3.2. 分析元器件

- **Endpoint**: `POST /conversations/{conversation_id}/analyze-components`
- **描述**: 基于初次分析生成的 BOM，对其进行结构化处理，以表格形式返回。
- **请求类型**: `application/x-www-form-urlencoded`
- **表单数据**:
  - `analysis_message_id`: (integer) **必须**。包含初始分析结果（BOM和需求文档）的消息ID。
- **成功响应 (200 OK)**:
  ```json
  {
    "id": 2,
    "role": "assistant",
    "content": {
      "type": "component_analysis",
      "data": {
        "status": "BOM data analyzed successfully.",
        "components": [
          {"器件名称": "Resistor", "单价": 0, "数量": 10, "总价": 0}
        ]
      }
    },
    "created_at": "..."
  }
  ```

### 3.3. 生成部署指南

- **Endpoint**: `POST /conversations/{conversation_id}/generate-deployment-guide`
- **描述**: 根据需求文档和 BOM 生成部署指南，并提供语音朗读文件。
- **请求类型**: `application/x-www-form-urlencoded`
- **表单数据**:
  - `analysis_message_id`: (integer) **必须**。包含初始分析结果的消息ID。
- **成功响应 (200 OK)**:
  ```json
  {
    "message": {
      "id": 3,
      "role": "assistant",
      "content": {
        "type": "deployment_guide",
        "data": {
          "text": "这是详细的部署指南...",
          "audio_url": "/static/audio/guide_1678886400.mp3"
        }
      },
      "created_at": "..."
    },
    "audio_url": "/static/audio/guide_1678886400.mp3"
  }
  ```

### 3.4. 生成代码

- **Endpoint**: `POST /conversations/{conversation_id}/generate-code`
- **描述**: 调用 Dify Agent 生成与项目相关的代码。
- **请求类型**: `application/x-www-form-urlencoded`
- **表单数据**:
  - `analysis_message_id`: (integer) **必须**。包含初始分析结果的消息ID。
- **成功响应 (200 OK)**:
  ```json
  {
    "message": {
      "id": 4,
      "role": "assistant",
      "content": {
        "type": "generated_code",
        "data": {
          "language": "python",
          "code": "print('Hello, World!')"
        }
      },
      "created_at": "..."
    }
  }
  ```

### 3.5. 生成原理图代码

- **Endpoint**: `POST /conversations/{conversation_id}/generate-schematic`
- **描述**: 调用 Dify 工作流生成可用于 EDA 工具的原理图代码。
- **请求类型**: `application/x-www-form-urlencoded`
- **表单数据**:
  - `analysis_message_id`: (integer) **必须**。包含初始分析结果的消息ID。
- **成功响应 (200 OK)**:
  ```json
  {
    "message": {
      "id": 5,
      "role": "assistant",
      "content": {
        "type": "schematic_code",
        "data": {
          "language": "python",
          "code": "..."
        }
      },
      "created_at": "..."
    }
  }
  ```

---

## 4. 前端详解

### 4.1. 目录结构

```
frontend/
├── src/
│   ├── assets/
│   │   └── main.css      # 全局样式
│   ├── components/
│   │   └── MessageRenderer.vue # 动态渲染不同消息类型的组件
│   ├── services/
│   │   └── api.js        # Axios 实例和 API 请求函数
│   ├── stores/
│   │   └── chat.js       # Pinia store, 管理应用状态
│   ├── App.vue           # 主组件, 包含布局和核心UI
│   └── main.js           # Vue 应用入口, 初始化Pinia
└── ... (其他配置文件)
```

### 4.2. 核心组件 (`MessageRenderer.vue`)

这是前端渲染的核心。它接收一个消息对象作为 `prop`，并根据 `content.type` 的值来决定渲染哪个子组件或模板。这使得添加新的消息类型变得非常��易，只需在该组件中增加一个新的 `v-if` 分支即可。

它还负责渲染**操作按钮** (如 "Analyze Components")，并通过 `emit` 将点击事件传递给父组件 `App.vue` 进行处理。

### 4.3. 状态管理 (Pinia)

`src/stores/chat.js` 是应用状态管理的核心。它负责：
- `state`: 存储所有会话 (`conversations`)、当前会话ID (`currentConversationId`)、全局加载状态 (`isLoading`) 和错误信息 (`error`)。
- `getters`: 提供计算属性，如获取当前激活会话的消息列表 (`currentMessages`)。
- `actions`: 定义与后端 API 交互的异步操作。每个 `action` (如 `startConversation`, `analyzeComponents`) 对应一个后端端点。它们负责调用 `api.js` 中的函数，处理响应，并将新数据更新到 `state` 中，从而驱动UI的重新渲染。

### 4.4. 未来开发建议

- **完善用户认证**: 实现真正的用户登录和注册，而非使用默认用户。
- **UI/UX 打磨**:
  - 对代码块增加语法高亮 (如使用 `highlight.js`)。
  - 增加加载动画和更友好的错误提示。
  - 实现流式响应，让 AI 的回答逐字显示，提升体验。
- **错误处理**: 在前端和后端都增加更精细的错误处理和日志记录。
- **功能扩展**:
  - 增加会话的重命名和删除功能。
  - 实现对历史消息的编辑和重新生成。
  - 将BOM表中的单价变为可编辑，以便用户手动输入价格并重新计算总价。