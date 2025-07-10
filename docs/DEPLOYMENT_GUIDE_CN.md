# PCBTool-Rev 生产环境部署指南

本指南提供了将 PCBTool-Rev 应用部署到云服务器（例如，AWS EC2, 阿里云 ECS, DigitalOcean Droplet 等）的详细步骤。本指南以 Ubuntu 22.04 LTS 作为服务器操作系统示例。

## 部署前置要求

1.  **一台云服务器**: 拥有 root 或 sudo 权限。
2.  **一个域名**: (可选) 解析到你的服务器 IP 地址。
3.  **NGINX**: 安装在服务器上，用作反向代理。
4.  **Node.js & npm**: 安装在服务器上，用于构建前端项目。
5.  **Python 3.10+ & pip**: 安装在服务器上。
6.  **Git**: 安装在服务器上。

---

## 第 1 步：服务器设置与环境依赖安装

首先，通过 SSH 连接到你的服务器，并确保所有必要的系统软件包都已安装。

```bash
# 更新软件包列表
sudo apt update && sudo apt upgrade -y

# 安装 NGINX, Python, pip, 和 Node.js
sudo apt install -y nginx python3-pip python3-venv nodejs npm git
```

---

## 第 2 步：克隆项目代码

从你的 Git 仓库将项目克隆到服务器。

```bash
# 将项目克隆到一个合适的目录, 例如 /var/www
git clone <你的Git仓库URL> /var/www/pcbtool-rev
cd /var/www/pcbtool-rev
```

---

## 第 3 步：后端部署 (FastAPI)

我们将使用 `gunicorn` (一个生产级的 Python WSGI HTTP 服务器) 来运行 FastAPI 应用，并使用 `systemd` 来管理该进程，以确保它能作为系统服务稳定运行。

### 3.1. 创建并配置 Python 虚拟环境

```bash
# 进入后端项目目录
cd /var/www/pcbtool-rev/backend

# 创建 Python 虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装所有依赖
pip install -r requirements.txt
# 为生产环境额外安装 gunicorn
pip install gunicorn
```

### 3.2. 配置环境变量

为后端服务创建一个 `.env` 文件。**请勿在生产环境中使用示例密钥。**

```bash
# 创建并使用 nano 编辑器打开 .env 文件
nano .env
```

将 `.env.example` 文件的内容复制到这个新文件中，然后将所有占位符值替换为你的生产环境 API 密钥和一个**强随机生成**的 `SECRET_KEY`。

### 3.3. 创建 `systemd` 服务文件

`systemd` 将负责管理 Gunicorn 进程，如果应用崩溃会自动重启。

```bash
# 创建一个新的 systemd 服务文件
sudo nano /etc/systemd/system/pcbtool-backend.service
```

将以下配置粘贴到文件中。**请务必将 `<your-username>` 替换为你在服务器上的实际用户名。**

```ini
[Unit]
Description=PCBTool-Rev FastAPI Backend Service
After=network.target

[Service]
User=<your-username>
Group=www-data
WorkingDirectory=/var/www/pcbtool-rev/backend
Environment="PATH=/var/www/pcbtool-rev/backend/venv/bin"
ExecStart=/var/www/pcbtool-rev/backend/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app

[Install]
WantedBy=multi-user.target
```
*   `-w 4`: 指定 4 个工作进程。一个推荐的初始值是 `(2 * CPU核心数) + 1`。
*   `-k uvicorn.workers.UvicornWorker`: 告知 Gunicorn 使用 Uvicorn 的工作进程类来运行异步的 FastAPI 应用。

### 3.4. 启动后端服务

```bash
# 重新加载 systemd 守护进程以识别新服务
sudo systemctl daemon-reload

# 启动后端服务
sudo systemctl start pcbtool-backend

# 设置服务开机自启
sudo systemctl enable pcbtool-backend

# 检查服务状态以确保其正常运行
sudo systemctl status pcbtool-backend
```

---

## 第 4 步：前端部署 (Vue.js)

Vue.js 应用需要被“构建”成一组静态的 HTML, CSS, 和 JavaScript 文件，然后由 NGINX 提供服务。

### 4.1. 构建前端静态文件

```bash
# 进入前端项目目录
cd /var/www/pcbtool-rev/frontend

# 安装依赖
npm install

# 构建生产版本
npm run build
```
这个命令会在 `frontend` 目录下创建一个 `dist` 文件夹，其中包含了所有优化过的静态资源。

---

## 第 5 步：配置 NGINX 作为反向代理

NGINX 将负责托管前端的静态文件，并将所有 API 请求 (例如 `/api/...`) 转发到后端的 Gunicorn 服务。

### 5.1. 创建 NGINX 配置文件

```bash
# 创建一个新的 NGINX 站点配置文件
sudo nano /etc/nginx/sites-available/pcbtool-rev
```

粘贴以下配置。**请将 `your_domain.com` 替换为你的服务器域名或 IP 地址。**

```nginx
server {
    listen 80;
    server_name your_domain.com;

    # 前端构建文件的根目录
    root /var/www/pcbtool-rev/frontend/dist;
    index index.html;

    # 适配单页应用 (SPA) 的路由
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 将所有 /api 的请求转发到后端服务
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### 5.2. 启用 NGINX 站点

```bash
# 创建一个符号链接来启用该站点配置
sudo ln -s /etc/nginx/sites-available/pcbtool-rev /etc/nginx/sites-enabled/

# 测试 NGINX 配置是否存在语法错误
sudo nginx -t

# 重启 NGINX 以应用更改
sudo systemctl restart nginx
```

---

## 部署完成！

你的应用现在应该已经成功部署并可以访问了。你可以通过浏览器访问你的服务器域名或 IP 地址来使用它。

### 重要提示：
-   **HTTPS**: 对于真实的生产网站，你**必须**配置 HTTPS。你可以使用 `certbot` 从 Let's Encrypt 获取免费的 SSL 证书。
-   **数据库**: 本指南使用 SQLite，它适用于个人项目或低流量网站。对于更大型的应用，你应该迁移到更健壮的数据库，如 PostgreSQL 或 MySQL。
-   **防火墙**: 请确保你的服务器防火墙 (例如 `ufw`) 已配置为允许端口 80 (HTTP) 和 443 (HTTPS) 的流量。
