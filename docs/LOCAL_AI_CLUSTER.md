# Local FOSS AI Cluster Guide

To achieve **IQ500 Sovereignty**, move your AI processing to a local cluster.

## 1. Deploy LocalAI
Add to `docker-compose.yml`:
```yaml
local-ai:
  image: localai/localai:latest
  ports:
    - "8080:8080"
  volumes:
    - ./models:/models
```

## 2. Update n8n Nodes
Change the base URL in all `HTTP Request` nodes from `https://openrouter.ai/api/v1` to `http://local-ai:8080/v1`.

## 3. Recommended Models
- **DeepSeek-Coder-33B**: (FOSS) For high-end code generation.
- **Phind-CodeLlama-34B**: (FOSS) For architectural reasoning.

This removes all external API dependencies and costs.
