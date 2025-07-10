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
│   │   ├── component_service.py # 组件分析逻辑
│   │   ├── dify_service.py     # 与 Dify API 交���的逻辑
│   │   ├── guide_service.py    # 部署指南和TTS生成逻辑
│   │   └── security_service.py # 密码哈希、JWT令牌和依赖项
│   └── main.py               # FastAPI 应用入口
├── .env.example              # 环境变量示例文件
└── requirements.txt          # Python 依赖
```

### 2.2. 认证与授权
- **机制**: 采用标准的 OAuth2 密码流和 JWT (JSON Web Tokens) 进行认证。
- **实现**:
  - `security_service.py` 包含所有核心安全功能：
    - 使用 `passlib` 对用户密码进行哈希处理和验证。
    - 使用 `python-jose` 创建和解码 JWT 令牌。
    - `get_current_user` 是一个 FastAPI 依赖项，它会解码请求头中的 `Bearer` 令牌，验证用户身份，并将用户对象注入到需要保护的端点中。
  - `endpoints.py` 中所有需要用户登录的端点都依赖于 `get_current_user`，从而实现了路由保护。
  - 数据库 `crud` 操作现在都与 `user_id` 关联，确保了严格的用户数据隔离。

---

## 3. API 端点文档

所有 API 的基础路径为 `/api/v1`。

### 3.1. 认证 (Public)
- **`POST /token`**: 用户登录，返回 JWT 访问令牌。
- **`POST /users/register`**: 注册新用户。

### 3.2. 会话管理 (Protected)
- **`GET /conversations`**: 获取当前登��用户的所有会话历史。
- **`POST /conversations/stream`**: 为当前用户开始一个新的流式分析会话。
- **`DELETE /conversations/{conversation_id}`**: 删除当前用户的指定会话。

### 3.3. 内容生成 (Protected)
- **`POST /conversations/{conversation_id}/analyze-components`**: 分析BOM。
- **`POST /conversations/{conversation_id}/generate-code/stream`**: 流式生成代码。
- **`POST /conversations/{conversation_id}/generate-deployment-guide/stream`**: 流式生成部署指南。
- **`POST /conversations/{conversation_id}/generate-schematic/stream`**: 流式生成原理图代码。

---

## 4. 前端详解

### 4.1. 目录结构
```
frontend/
├── src/
│   ├── assets/           # CSS 和静态资源
│   ├── components/       # 可复用Vue组件 (MessageRenderer)
│   ├── router/           # Vue Router 配置
│   ├── services/         # API 请求服务 (api.js)
│   ├── stores/           # Pinia 状态管理 (auth.js, chat.js)
│   ├── views/            # 页面级组件 (LoginView, RegisterView)
│   ├── App.vue           # 主聊天界面 (受保护)
│   ├── Root.vue          # 应用根组件, 包含 <router-view>
│   └── main.js           # Vue 应用入口
└── ...
```

### 4.2. 认证流程
- **��由**: `router/index.js` 定义了公共路由 (`/login`, `/register`) 和受保护的路由 (`/`)。`beforeEach` 导航守卫会检查用户的认证状态，如果未登录的用户尝试访问受保护路由，则会自动重定向到 `/login`。
- **状态管理**: `stores/auth.js` 负责处理用户的认证状态。
  - `token` 和 `username` 从 `localStorage` 中初始化，以实现会话持久化。
  - `login` 和 `register` action 调用 API，成功后将令牌存入 `localStorage` 并重定向到主页。
  - `logout` action 清除令牌和 `localStorage`，并重定向到登录页。
- **API 请求**: `services/api.js` 使用 Axios 拦截器自动将 `Authorization: Bearer <token>` 请求头附加到所有发出的 `apiClient` 请求中。对于使用 `fetch` 的流式请求，该请求头也会被手动添加。