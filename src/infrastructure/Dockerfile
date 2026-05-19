FROM n8nio/n8n:latest
USER root
RUN apk add --no-cache python3 py3-pip git curl unzip bash
RUN curl --proto '=https' --tlsv1.2 -fsSL https://get.opentofu.org/install-opentofu.sh -o install-opentofu.sh && chmod +x install-opentofu.sh && ./install-opentofu.sh --install-method standalone && rm install-opentofu.sh
RUN curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
RUN pip3 install --no-cache-dir --break-system-packages semgrep radon bandit pytest
USER node
