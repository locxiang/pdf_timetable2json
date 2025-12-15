# 使用Python 3.9作为基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖（Camelot需要Ghostscript和Tkinter相关库）
RUN apt-get update && apt-get install -y \
    ghostscript \
    python3-tk \
    && rm -rf /var/lib/apt/lists/*

# 配置pip使用阿里云镜像源
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
    pip config set install.trusted-host mirrors.aliyun.com

# 先只复制依赖配置文件，利用Docker缓存层
COPY pyproject.toml ./

# 复制src的必要文件（至少需要__init__.py让setuptools能找到包结构）
COPY src/app/__init__.py ./src/app/__init__.py


# 安装Python依赖（只有pyproject.toml变化时才会重新执行此步骤）
# pip install -e . 会自动从pyproject.toml读取依赖并安装
RUN pip install -e .

# 复制完整的源代码（代码变化时只需要重新构建这一层）
COPY src/ ./src/

# 创建临时文件目录
RUN mkdir -p /tmp/uploads && chmod 777 /tmp/uploads

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=src.app.main
ENV FLASK_ENV=production

# 暴露端口
EXPOSE 5001

# 启动应用
CMD ["python", "-m", "src.app.main"]

