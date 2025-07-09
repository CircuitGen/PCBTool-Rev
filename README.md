# PCBTool-Rev: AI 驱动的电路分析与生成工具

![App Screenshot](docs/screenshot.png) <!-- Replace with a real screenshot -->

## 1. 项目简介

PCBTool-Rev 是一个现代化的全栈 Web 应用，旨在将 `LLM3_Update.ipynb` 的功能从一个本地 Gradio 应用重构为一个可扩展、支持并发、前后端分离的企业级解决方案。

该工具通过一个流畅的对话式界面，引导用户完成从**图片/文本输入**到**电路分析**，再到**BOM生成**、**代码生成**和**部署指南**的全过程。所有交互都以会话形式保存，支持历史查阅和用户隔离。

## 2. 核心功能

- **灵活的输入方式**: 支持仅文本、仅图片或图文结合的多种输入方式来启动分析流程。
- **AI 图像分析**: 上传电路图或硬件图片，AI 自动分析并提取关键信息。
- **BOM 与需求文档生成**: 基于分析结果，一键生成结构化的物料清单 (BOM) 和详细的需求文档。
- **交互式组件分析**:
  - 对生成的 BOM 进行二次分析，以表格形式清晰展示。
  - 提供操作按钮，触发后续的代码生成、指南生成等步骤。
- **多模态内容生成**:
  - **部署指南**: 生成图文并茂的���细项目部署文档。
  - **语音朗读**: 将生成的指南文本转换为语音，并提供在线播放器。
  - **硬件代码生成**: 生成与硬件配套的驱动或应用代码。
  - **原理图代码**: 生成可用于 EDA 工具（如立创EDA）的原理图代码。
- **完整的对话流**:
  - 所有操作都在一个会话中完成，上下文清晰，易于追溯。
  - 支持多会话管理，用户可以轻松切换和查看不同的分析任务。

## 3. 技术栈

- **后端**:
  - **框架**: FastAPI
  - **语言**: Python 3
  - **数据库**: SQLite (用于原型)
  - **异步处理**: Uvicorn
  - **核心库**: SQLAlchemy, Pydantic, OpenAI, Dify-Client, gTTS

- **前端**:
  - **框架**: Vue.js 3 (Composition API)
  - **状态管理**: Pinia
  - **HTTP客户端**: Axios
  - **UI**: 使用原生 CSS 和少量库 (`marked`) 实现，轻量且高效。
  - **构建工具**: Vite

- **AI 服务**:
  - **核心逻辑**: Dify 平台 (工作流与 Agent)
  - **文本生成**: 阿里云通义千问 (通过 OpenAI 兼容模式)

## 4. 本地启动指南

在开始之前，请确保你已安装 Python 3.10+ 和 Node.js 20+。

### 步骤 1: 启动后端服务

1.  打开一个新的终端窗口。
2.  **导航到后端目录**:
    ```bash
    cd C:\Users\WPP_JKW\PCBTool-Rev\backend
    ```
3.  **安装/更新依赖**:
    ```bash
    pip install -r requirements.txt --upgrade
    ```
4.  **启动 FastAPI 服务器**:
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

在浏览器中打开前端服务的 URL (例如 `http://localhost:5173`) 即可开始使用。