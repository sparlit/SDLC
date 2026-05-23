import asyncio, json, os, sys, random, time, aiohttp, base64, chromadb
from typing import List, Dict, Any

# Hardened Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
# Dynamic project path detection for better portability
PROJECT_PATH = os.getenv("PROJECT_PATH", os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
PROMPTS_FILE = os.path.join(PROJECT_PATH, "src/prompts/prompts.json")

# High-availability free models from OpenRouter
MODELS = [
    "google/gemini-2.0-flash-001",
    "mistralai/mistral-7b-instruct:free",
    "openchat/openchat-7b:free",
    "huggingfaceh4/zephyr-7b-beta:free"
]

# Resilient ChromaDB Persistence
CHROMA_PATH = os.path.join(PROJECT_PATH, ".chroma_db")
if not os.path.exists(CHROMA_PATH):
    try:
        os.makedirs(CHROMA_PATH, exist_ok=True)
    except Exception:
        # Fallback to temp if project path is read-only
        import tempfile
        CHROMA_PATH = os.path.join(tempfile.gettempdir(), "iq400_chroma_db")
        os.makedirs(CHROMA_PATH, exist_ok=True)

chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = chroma_client.get_or_create_collection(name="swarm_debates")

def load_system_prompt(role: str) -> str:
    try:
        with open(PROMPTS_FILE, 'r') as f:
            prompts = json.load(f)
            return prompts.get("system_prompts", {}).get(role, prompts["system_prompts"].get("development", ""))
    except Exception:
        return "You are a professional software engineer."

async def call_llm(model: str, messages: List[Dict[str, str]], temperature=0.7) -> str:
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {"model": model, "messages": messages, "temperature": temperature}

    async with aiohttp.ClientSession() as session:
        for attempt in range(5):
            try:
                async with session.post(url, headers=headers, json=payload, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data['choices'][0]['message']['content']
                    elif response.status == 429:
                        # Exponential backoff on rate limits
                        await asyncio.sleep(2 ** attempt)
            except Exception:
                pass
            # Model rotation on failure
            model = random.choice(MODELS)
            payload["model"] = model
    return "Error: LLM call failed after multiple attempts."

class FractalSwarm:
    def __init__(self, stage: str, context: Dict[str, Any]):
        self.stage = stage
        self.context = context
        self.breadth = 5 if stage == "error_fixing" else 3
        self.prompt = load_system_prompt(stage)

    async def run_swarm(self):
        # 1. Memory Query (Omniscient match)
        query_text = f"stage: {self.stage}, context: {json.dumps(self.context)}"
        results = collection.query(query_texts=[query_text], n_results=1)
        if results['documents'] and len(results['documents'][0]) > 0 and results['distances'][0][0] < 0.05:
            return results['documents'][0][0]

        # 2. Parallel Reasoning (Swarm Branches)
        branches = [self.run_branch(i) for i in range(self.breadth)]
        branch_results = await asyncio.gather(*branches)

        # 3. Final Tournament Synthesis
        final_consensus = await self.synthesize(branch_results)

        # 4. Persistence
        collection.add(
            documents=[final_consensus],
            metadatas=[{"stage": self.stage, "timestamp": time.time()}],
            ids=[f"{self.stage}_{int(time.time())}"]
        )
        return final_consensus

    async def run_branch(self, branch_id: int) -> str:
        prompt = f"{self.prompt}\nContext: {json.dumps(self.context)}\nSimulate 6 levels of recursive debate. Return final synthesized solution."
        return await call_llm(MODELS[branch_id % len(MODELS)], [{"role": "user", "content": prompt}])

    async def synthesize(self, proposals: List[str]) -> str:
        prompt = f"{self.prompt}\nProposals: {json.dumps(proposals)}\nSynthesize the absolute best solution. Ensure 'Zero Stub Guarantee'."
        return await call_llm(random.choice(MODELS), [{"role": "user", "content": prompt}])

async def main():
    if not OPENROUTER_API_KEY:
        print("Error: OPENROUTER_API_KEY not set.")
        sys.exit(1)
    if len(sys.argv) < 3:
        sys.exit(1)

    stage = sys.argv[1]
    try:
        # Prevent shell injection by using base64 for complex context
        context_json = base64.b64decode(sys.argv[2]).decode('utf-8')
        context = json.loads(context_json)
    except Exception:
        sys.exit(1)

    result = await FractalSwarm(stage, context).run_swarm()
    print("\n--- FINAL SWARM CONSENSUS ---")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
