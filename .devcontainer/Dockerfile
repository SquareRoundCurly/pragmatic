FROM ubuntu:latest

RUN apt-get update && apt-get install -y \
    curl \
    git \
    nodejs \
    npm \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Install Claude Code
RUN npm install -g @anthropic-ai/claude-code

# Create non-root devcontainer user (ubuntu:latest may already have uid/gid 1000)
RUN userdel -r ubuntu 2>/dev/null || true \
    && groupadd --gid 1000 devcontainer 2>/dev/null || true \
    && useradd --uid 1000 --gid 1000 -m -s /bin/bash devcontainer

USER devcontainer
