# 后端

python, flask

# 前端

vite, react, ts, shadcn, tailwind

# 数据库

mysql, redis

# 部署手册

## 🚀 全栈应用部署手册 (Windows -> Ubuntu)

### 阶段一：本地准备 (Windows)

在 Windows 终端（PowerShell 或 CMD）中，位于项目根目录下执行：

**1. 构建前端静态资源**
进入前端目录并打包，生成 `dist` 文件夹。

```powershell
cd frontend
# 安装依赖 (如果没有安装)
npm install
# 构建生产环境代码
npm run build

```

*构建完成后，请确认 `frontend` 目录下是否生成了 `dist` 文件夹。*

**2. 准备后端 Dockerfile**
确保 `backend` 文件夹内有一个有效的 `Dockerfile`。如果没有，请参考以下通用模板（以 Node.js 为例，如果是 Java/Python 请相应修改）：

> **文件名: Dockerfile (位于 backend 目录下)**
> ```dockerfile
> FROM node:18-alpine
> WORKDIR /app
> COPY package*.json ./
> RUN npm install --production
> COPY . .
> EXPOSE 8080
> CMD ["npm", "start"]
> 
> ```
> 
> 

---

### 阶段二：文件传输 (Windows -> Ubuntu)

将构建好的前端资源和后端源码上传到服务器。

**1. 在服务器创建目录**
在 Windows 终端连接服务器执行（或者使用 SSH 工具）：

```powershell
ssh root@your-server-ip "mkdir -p /var/www/gogen/frontend /var/www/gogen/backend"

```

**2. 上传文件**
回到 Windows 项目根目录，执行文件拷贝命令（`scp`）：

```powershell
# 1. 上传前端 dist 目录下的所有内容
scp -r .\frontend\dist\* root@your-server-ip:/var/www/gogen/frontend/

# 2. 上传后端源码 (排除 node_modules 等不需要的大文件夹建议使用 .dockerignore，这里直接上传源码)
scp -r .\backend\* root@your-server-ip:/var/www/gogen/backend/

scp .\backend\.env.example root@your-server-ip:/var/www/gogen/backend/.env
```

---

### 阶段三：服务器端部署 (Ubuntu)

现在登录到你的 Ubuntu 服务器：`ssh root@your-server-ip`

#### 步骤 1：环境安装 (如果尚未安装)

```bash
sudo apt update
sudo apt install nginx docker.io -y
sudo systemctl start docker
sudo systemctl enable docker

```

#### 步骤 2：部署后端 (Docker)

进入后端目录，构建镜像并运行。

```bash
cd /var/www/gogen/backend

# 1. 构建镜像
docker-compose up -d --build

```

*此时使用 `curl 127.0.0.1:5000` 测试后端是否存活。*

#### 步骤 3：配置 Nginx (前端 + 反向代理)

**1. 创建配置文件**

```bash
sudo nano /etc/nginx/sites-available/gogen
scp .\gogen root@your-server-ip:/etc/nginx/sites-available/gogen
```

**2. 粘贴以下内容 (按需修改 IP)**

```nginx
server {
    listen 80;
    server_name your-server-ip; # 例如 123.456.78.90

    # --- 前端配置 ---
    location / {
        root /var/www/gogen/frontend; # 指向上传的 dist 文件
        index index.html;
        # 解决 SPA 单页应用刷新 404 问题
        try_files $uri $uri/ /index.html;
    }

    # --- 后端接口反向代理 ---
    # 假设你的前端请求前缀是 /api
    location /api/ {
        # 转发给本地 Docker 容器
        proxy_pass http://127.0.0.1:5000/;
        
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}

```

*按 `Ctrl + O` 保存，`Enter` 确认，`Ctrl + X` 退出。*

#### 步骤 4：激活与权限修复

**1. 修复文件权限 (防止 403 Forbidden)**

```bash
sudo chown -R www-data:www-data /var/www/gogen
sudo chmod -R 755 /var/www/gogen

```

**2. 激活 Nginx 配置**

```bash
# 建立软链接
sudo ln -s /etc/nginx/sites-available/gogen /etc/nginx/sites-enabled/

# 移除默认配置 (防止冲突)
sudo rm /etc/nginx/sites-enabled/default

# 检查语法
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
sudo systemctl reload nginx
```

---

### ✅ 验证部署

打开浏览器访问：`http://你的服务器IP`

1. 应该能看到前端页面。
2. 前端发起的 `/api` 请求应该能成功返回数据。