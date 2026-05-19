# Free LLM Configuration Guide

To use this SDLC workflow for free or with minimal cost, follow these steps:

## 1. OpenRouter (Free Models)
OpenRouter provides access to several free models. In the n8n `HTTP Request` nodes, you can change the `model` parameter to any of the following (as of now):
- `google/gemini-2.0-flash-001` (Often has a generous free tier)
- `meta-llama/llama-3-8b-instruct:free`
- `mistralai/mistral-7b-instruct:free`
- `microsoft/phi-3-mini-128k-instruct:free`

**How to update in n8n:**
1. Open the "AI Analysis" or "AI Fix Generator" node.
2. In the `Body Parameters`, change the value of `model` to one of the strings above.

## 2. Ollama (100% Local & Free)
If you want to run LLMs on your own hardware:
1. Ensure the `ollama` service is running in Docker.
2. In n8n, use the **Ollama Node** or an **HTTP Request** node pointing to `http://ollama:11434/api/generate`.
3. Recommended models for coding:
   - `codellama`
   - `deepseek-coder`
   - `llama3`

## 3. Groq (High Speed Free Tier)
Groq currently offers a free tier for developers.
1. Get an API key from [console.groq.com](https://console.groq.com/).
2. In n8n, change the API URL to `https://api.groq.com/openai/v1/chat/completions`.
3. Use the model `llama3-70b-8192` or `mixtral-8x7b-32768`.
