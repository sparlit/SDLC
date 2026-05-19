# RAG & Context Management Setup (FOSS)

For large projects, it is recommended to use a Vector Database to manage long-term memory and context for the AI agents.

## Recommended Tools:
- **ChromaDB**: (100% FOSS) Easy to run in Docker.
- **Milvus**: (FOSS) High-performance vector search.

## Integration Steps:
1. Add the following to your `docker-compose.yml`:
   ```yaml
   chroma:
     image: chromadb/chroma:latest
     ports:
       - "8000:8000"
   ```
2. In n8n, use the **HTTP Request** node to index project files into Chroma:
   - Endpoint: `http://chroma:8000/api/v1/collections/...`
3. Before the "AI Fixer" or "Orchestrator" nodes, add a **Vector Search** step to retrieve the most relevant code snippets for the current task.

This will significantly reduce token usage and improve the "Architectural Awareness" of the autonomous fixing loop.
