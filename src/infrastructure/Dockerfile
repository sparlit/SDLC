FROM n8nio/n8n:latest

USER root

# Install FOSS SDLC Tools + Whisper dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    git \
    curl \
    unzip \
    bash \
    ffmpeg

# Install OpenTofu
RUN curl --proto '=https' --tlsv1.2 -fsSL https://get.opentofu.org/install-opentofu.sh -o install-opentofu.sh && \
    chmod +x install-opentofu.sh && \
    ./install-opentofu.sh --install-method standalone && \
    rm install-opentofu.sh

# Install Trivy
RUN curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin

# Install Python-based FOSS Audit & AI Tools
RUN pip3 install --no-cache-dir --break-system-packages \
    semgrep \
    radon \
    bandit \
    pytest \
    chromadb \
    openai-whisper \
    scancode-toolkit

USER node
