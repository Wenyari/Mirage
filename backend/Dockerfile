# Python 3.11 基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖（使用清华源加速）
RUN pip install --upgrade pip && \
    pip install -r requirements.txt
# 复制项目文件
COPY . .

# 复制启动脚本并设置执行权限
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN sed -i 's/\r$//' /docker-entrypoint.sh && chmod +x /docker-entrypoint.sh

# 暴露端口
EXPOSE 5000

# 设置启动脚本为入口点
ENTRYPOINT ["/docker-entrypoint.sh"]

# 默认启动命令 (由 docker-compose 覆盖)
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "run:app"]
