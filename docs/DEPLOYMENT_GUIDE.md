# Production Deployment Guide for PCBTool-Rev

This guide provides step-by-step instructions for deploying the PCBTool-Rev application to a cloud server (e.g., AWS EC2, DigitalOcean Droplet, etc.) running a modern Linux distribution like Ubuntu 22.04.

## Prerequisites

1.  **A cloud server**: With root or sudo access.
2.  **Domain name**: (Optional) Pointing to your server's IP address.
3.  **NGINX**: Installed on your server to act as a reverse proxy.
4.  **Node.js & npm**: Installed on your server to build the frontend.
5.  **Python 3.10+ & pip**: Installed on your server.
6.  **Git**: Installed on your server.

---

## Step 1: Server Setup & Dependencies

First, connect to your server via SSH and ensure all necessary system packages are installed.

```bash
# Update package lists
sudo apt update && sudo apt upgrade -y

# Install NGINX, Python, pip, and Node.js
sudo apt install -y nginx python3-pip python3-venv nodejs npm git
```

---

## Step 2: Clone the Project

Clone your project repository from GitHub (or your Git provider) to the server.

```bash
# Clone the repository into a directory, e.g., /var/www
git clone <your-git-repository-url> /var/www/pcbtool-rev
cd /var/www/pcbtool-rev
```

---

## Step 3: Backend Deployment (FastAPI)

We will run the FastAPI application using `gunicorn`, a robust Python WSGI HTTP server, and manage it with `systemd` to ensure it runs as a service.

### 3.1. Create a Virtual Environment

```bash
# Navigate to the backend directory
cd /var/www/pcbtool-rev/backend

# Create a Python virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn # Install gunicorn for production
```

### 3.2. Configure Environment Variables

Create a `.env` file for the backend. **Do not use the example keys in production.**

```bash
# Create and open the .env file
nano .env
```

Copy the contents of `.env.example` into this file and replace the placeholder values with your actual production API keys and a strong, randomly generated `SECRET_KEY`.

### 3.3. Create a `systemd` Service File

`systemd` will manage the Gunicorn process, automatically restarting it if it crashes.

```bash
# Create a new systemd service file
sudo nano /etc/systemd/system/pcbtool-backend.service
```

Paste the following configuration into the file. **Remember to replace `<your-username>` with your actual username on the server.**

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
*   `-w 4`: Specifies 4 worker processes. A good starting point is `(2 * number_of_cpu_cores) + 1`.
*   `-k uvicorn.workers.UvicornWorker`: Tells Gunicorn to use Uvicorn's worker class to run the async FastAPI app.

### 3.4. Start the Backend Service

```bash
# Reload the systemd daemon to recognize the new service
sudo systemctl daemon-reload

# Start the backend service
sudo systemctl start pcbtool-backend

# Enable the service to start on boot
sudo systemctl enable pcbtool-backend

# Check the status to ensure it's running correctly
sudo systemctl status pcbtool-backend
```

---

## Step 4: Frontend Deployment (Vue.js)

The Vue.js application needs to be "built" into a set of static HTML, CSS, and JavaScript files, which will then be served by NGINX.

### 4.1. Build the Frontend

```bash
# Navigate to the frontend directory
cd /var/www/pcbtool-rev/frontend

# Install dependencies
npm install

# Build the application for production
npm run build
```
This command will create a `dist` directory inside `frontend` containing all the static assets.

---

## Step 5: Configure NGINX as a Reverse Proxy

NGINX will serve the static frontend files and forward all API requests (e.g., `/api/...`) to the backend Gunicorn service.

### 5.1. Create an NGINX Configuration File

```bash
# Create a new NGINX config file
sudo nano /etc/nginx/sites-available/pcbtool-rev
```

Paste the following configuration. **Replace `your_domain.com` with your server's domain name or IP address.**

```nginx
server {
    listen 80;
    server_name your_domain.com;

    # Path to the frontend build files
    root /var/www/pcbtool-rev/frontend/dist;
    index index.html;

    location / {
        # Fallback to index.html for Single Page Applications (SPA)
        try_files $uri $uri/ /index.html;
    }

    location /api {
        # Forward API requests to the backend service
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### 5.2. Enable the NGINX Site

```bash
# Create a symbolic link to enable the site
sudo ln -s /etc/nginx/sites-available/pcbtool-rev /etc/nginx/sites-enabled/

# Test the NGINX configuration for syntax errors
sudo nginx -t

# Restart NGINX to apply the changes
sudo systemctl restart nginx
```

---

## Deployment Complete!

Your application should now be live. You can access it by navigating to your server's domain name or IP address in a web browser.

### Important Notes:
-   **HTTPS**: For a real production site, you **must** configure HTTPS. You can get a free SSL certificate from Let's Encrypt using `certbot`.
-   **Database**: This guide uses SQLite, which is fine for single-user or low-traffic sites. For a larger application, you should migrate to a more robust database like PostgreSQL or MySQL.
-   **Firewall**: Ensure your server's firewall (e.g., `ufw`) is configured to allow traffic on port 80 (HTTP) and 443 (HTTPS).
