FROM ubuntu:22.04

# 环境变量设置
ENV PATH=/lib/llvm-18/bin:/root/.cargo/bin:$PATH \
    LD_LIBRARY_PATH=/lib/llvm-18/lib \
    RUSTUP_HOME=/usr/local/rustup \
    CARGO_HOME=/usr/local/cargo \
    DEBIAN_FRONTEND=noninteractive \
    DOCKER_CONTAINER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=UTF-8

# 安装系统依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    software-properties-common \
    wget \
    curl \
    gnupg \
    build-essential \
    cmake \
    git \
    unzip \
    patchelf \
    graphviz \
    python3 \
    python3-dev \
    python3-distutils \
    python3-pip \
    lsb-release \
    file \
    libssl-dev \
    openssl \
    pkg-config \
    libfontconfig \
    libfontconfig1-dev \
    zip \
    libpsl-dev \
    libgl1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 安装wllvm
RUN pip3 install --no-cache-dir wllvm

# 安装LLVM 18
RUN wget https://apt.llvm.org/llvm.sh && \
    chmod +x llvm.sh && \
    ./llvm.sh 18 && \
    ln -s /usr/bin/clang-18 /usr/bin/clang && \
    ln -s /usr/bin/clang++-18 /usr/bin/clang++ && \
    rm llvm.sh

# 设置工作目录
WORKDIR /workspace

# 安装Python依赖管理工具
RUN python3 -m pip install --no-cache-dir --upgrade pip

# 安装CPU版本的PyTorch
RUN pip install --no-cache-dir \
    torch==2.6.0 \
    torchvision==0.21.0 \
    torchaudio==2.6.0

# 复制requirements.txt并安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制项目代码（最后一步以最大化利用缓存）
COPY . .