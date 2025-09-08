# 使用更稳定的 NVIDIA CUDA 基础镜像（包含 CUDA toolkit）
FROM nvidia/cuda:12.3.0-devel-ubuntu22.04

# 环境变量设置
ENV PATH=/lib/llvm-18/bin:/usr/local/cuda/bin:/usr/local/cargo/bin:/root/.cargo/bin:$PATH \
    LD_LIBRARY_PATH=/lib/llvm-18/lib:/usr/local/cuda/lib64 \
    RUSTUP_HOME=/usr/local/rustup \
    CARGO_HOME=/usr/local/cargo \
    DEBIAN_FRONTEND=noninteractive \
    DOCKER_CONTAINER=1 \
    CUDA_VISIBLE_DEVICES=1,2,3,4,5,6,7 \
    NCCL_DEBUG=INFO \
    NCCL_SOCKET_IFNAME=^lo,docker0 \
    MASTER_PORT=29501 \
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
    python3.10 \
    python3.10-dev \
    python3.10-distutils \
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

# 添加Python PPA并安装Python 3.10（如果上面的安装失败）
RUN add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y python3.10 python3.10-distutils && \
    apt-get clean \
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
WORKDIR /app

# 安装Python依赖管理工具
RUN python3.10 -m pip install --no-cache-dir --upgrade pip

# 安装特定版本的PyTorch和依赖（确保CUDA 12.3兼容）
RUN pip install --no-cache-dir \
    torch==2.6.0+cu124 \
    torchvision==0.21.0+cu124 \
    torchaudio==2.6.0+cu124 \
    --index-url https://download.pytorch.org/whl/cu124

# 复制requirements.txt并安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制项目代码（最后一步以最大化利用缓存）
COPY . .