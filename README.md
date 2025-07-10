# PCBTool-Rev: AI 驱动的电路分析与生成工具

![App Screenshot](docs/screenshot.png) <!-- Replace with a real screenshot -->

## 1. 项目简介

PCBTool-Rev 是一个现代化的、支持多用户的全栈 Web 应用。它将 `LLM3_Update.ipynb` 的功能从一个本地 Gradio 应用重构为一个可扩展、支持并发、前后端分离的企业级解决方案。

该工具通过一个流畅的对话式界面，引导用户完成从**图片/文本输入**到**电路分析**，再到**BOM生成**、**代码生成**和**部署指南**的全过程。所有交互都以会话形式保存，并与特定用户关联，实现了完整的用户数据隔离。

## 2. 核心功能

- **用户认证系统**:
  - 支持用户注册和登录。
  - 使用 JWT (JSON Web Tokens) 进行安全的会话管理。
  - 所有 API 均受保护，确保用户只能访问自己的数据。
- **灵活的输入方式**: 支持仅文本、仅图片或图文结合的多种输入方式来启动分析流程。
- **实时流式响应**: 所有 AI 生成过程都采用流式响应，前端实时显示进度和结果，极大提升了用户体验。
- **交互式组件分析**:
  - 对生成的 BOM 进行二次分析，以表格形式清���展示。
  - 提供操作按钮，触发后续的代码生成、指南生成等步骤。
- **多模态内容生成**:
  - **部署指南**: 生成图文并茂的详细项目部署文档。
  - **语音朗读**: 将生成的指南文本转换为语音。
  - **硬件代码生成**与**原理图代码**。
- **完整的对话流与管理**:
  - **历史记录**: 自动加载和保存当前用户的所有历史会话。
  - **会话管理**: 支持新建和删除会话。

## 3. 技术栈

- **后端**:
  - **框架**: FastAPI
  - **认证**: OAuth2 with JWT (`python-jose`, `passlib`)
  - **数据库**: SQLite (用于原型)
  - **异步与流式处理**: `StreamingResponse`, `async/await`, `httpx`
  - **核心库**: SQLAlchemy, Pydantic, python-dotenv

- **前端**:
  - **框架**: Vue.js 3 (Composition API)
  - **路由**: Vue Router
  - **状态管理**: Pinia
  - **HTTP客户端**: `fetch` API, Axios (with interceptors for auth)
  - **UI**: 使用原生 CSS 和少量库 (`marked`) 实现。

## 4. 本地启动指南

在开始之前，请确保你已安装 Python 3.10+ 和 Node.js 20+。

### 步骤 1: 启动后端服务

1.  打开一个新的终端窗口。
2.  **导航到后端目录**:
    ```bash
    cd C:\Users\WPP_JKW\PCBTool-Rev\backend
    ```
3.  **(首次运行) 创建环境文件**: 复制 `.env.example` 为 `.env`。
4.  **(首次运行) 删除旧数据库**: 如果存在 `pcbtool.db` 文件，请删除它以应用新的用户模型。
5.  **安装/更新依赖**:
    ```bash
    pip install -r requirements.txt --upgrade
    ```
6.  **启动 FastAPI 服务器**:
    ```bash
    python -m uvicorn app.main:app --reload
    ```
    服务器将在 `http://localhost:8000` 上运行。

### 步骤 2: 启动前端服务

1.  打开**另一个**新的终端窗口。
2.  **导航到前端目录**:
    ```bash
    cd C:\Users\WPP_JKW\PCBTool-Rev\frontend
    ```
3.  **安装依赖** (如果尚未安装):
    ```bash
    npm install
    ```
4.  **启动 Vue 开发服务器**:
    ```bash
    npm run dev
    ```
    终端会显示一个本地 URL，通常是 `http://localhost:5173`。

### 步骤 3: 访问应用

在浏览器中打开前端服务的 URL (例如 `http://localhost:5173`)。你将被引导至登录页面，可以注册新用户后开始使用。