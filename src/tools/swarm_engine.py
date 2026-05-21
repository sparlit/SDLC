import asyncio
import json
import os
import sys
import random
import time
import aiohttp
import base64
from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings

# --- CONFIGURATION ---
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
PROJECT_PATH = os.getenv("PROJECT_PATH", "/data/project")
PROMPTS_FILE = os.path.join(PROJECT_PATH, "src/prompts/prompts.json")

MODELS = [
    "baidu/cobuddy:free",
    "arcee-ai/trinity-large-thinking:free",
    "deepseek/deepseek-v4-flash:free",
    "google/gemma-4-31b-it:free",
    "liquid/lfm-2.5-1.2b-thinking:free",
]

# --- CHROMADB SETUP ---
# Use a project-relative path for persistence
CHROMA_PATH = os.path.join(PROJECT_PATH, ".chroma_db")
if not os.path.exists(CHROMA_PATH):
    try:
        os.makedirs(CHROMA_PATH, exist_ok=True)
    except:
        # Fallback to home if project path is not writable
        CHROMA_PATH = os.path.expanduser("~/.chroma_db")
        os.makedirs(CHROMA_PATH, exist_ok=True)

chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = chroma_client.get_or_create_collection(name="swarm_debates")

def load_system_prompt(role: str) -> str:
    """Loads the specialized system prompt for the given role."""
    try:
        with open(PROMPTS_FILE, 'r') as f:
            prompts = json.load(f)
            return prompts.get("system_prompts", {}).get(role, prompts["system_prompts"].get("development", ""))
    except Exception as e:
        print(f"Warning: Could not load specialized prompt for {role}: {e}")
        return "You are a professional software engineer."

async def call_llm(model: str, messages: List[Dict[str, str]], temperature=0.7) -> str:
    """Wrapper for OpenRouter API calls with robust retry, model rotation, and backoff."""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }

    async with aiohttp.ClientSession() as session:
        for attempt in range(10):
            try:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data['choices'][0]['message']['content']
                    elif response.status == 429:
                        wait = (attempt + 1) * 15
                        print(f"Rate limited ({model}). Waiting {wait}s...")
                        await asyncio.sleep(wait)
                    else:
                        error_text = await response.text()
                        print(f"Error {response.status} ({model}): {error_text}")
            except Exception as e:
                print(f"Request failed: {e}")

            # Rotate model
            model = random.choice(MODELS)
            payload["model"] = model
            await asyncio.sleep(2)

    return "Error: LLM call failed after 10 attempts."

class FractalSwarm:
    def __init__(self, stage: str, context: Dict[str, Any]):
        self.stage = stage
        self.context = context
        self.is_error_fixing = stage == "error_fixing"
        self.breadth = 5 if self.is_error_fixing else 3
        self.specialized_prompt = load_system_prompt(stage)

    async def run_swarm(self):
        print(f"Initiating {self.stage} Fractal Swarm (Breadth: {self.breadth}, Depth: 6)...")

        # Check memory
        query_text = f"stage: {self.stage}, context: {json.dumps(self.context)}"
        results = collection.query(query_texts=[query_text], n_results=1)
        if results['documents'] and len(results['documents'][0]) > 0 and results['distances'][0][0] < 0.05:
            print("Omniscient Match Found! Retrieving consensus from long-term memory.")
            return results['documents'][0][0]

        # Phase 1: Parallel Hierarchical Reasoning
        branches = []
        for i in range(self.breadth):
            branches.append(self.run_branch(i))

        branch_results = await asyncio.gather(*branches)

        # Check for irreconcilable conflicts
        if self.detect_conflict(branch_results):
            return "CONFLICT: The swarm has reached an irreconcilable disagreement. Falling back to Planning for re-evaluation."

        # Phase 2: Final Tournament Synthesis
        print("Commencing Final Tournament Synthesis...")
        final_consensus = await self.synthesize("Final Orchestrator", branch_results)

        # Save to memory
        collection.add(
            documents=[final_consensus],
            metadatas=[{"stage": self.stage, "timestamp": time.time()}],
            ids=[f"{self.stage}_{int(time.time())}"]
        )

        return final_consensus

    def detect_conflict(self, results: List[str]) -> bool:
        """Heuristic to detect if branches are completely polarized."""
        # Check for deep divergence by comparing response lengths and error presence
        errors = [r for r in results if "Error:" in r]
        if 0 < len(errors) < len(results):
            return True

        # If lengths vary wildly, it might indicate a lack of consensus on complexity
        lengths = [len(r) for r in results]
        if max(lengths) > min(lengths) * 10:
            return True

        return False

    async def run_branch(self, branch_id: int) -> str:
        """Simulates one entire hierarchy tree using the specialized stage prompt."""
        print(f"Branch {branch_id}: Reasoning through hierarchy levels...")

        prompt = f"""{self.specialized_prompt}

You are the Lead Model for Branch {branch_id} in the {self.stage} stage.
Context: {json.dumps(self.context)}

Your hierarchy consists of 6 levels (Model down to Sub-agent).
Task: Simulate a recursive debate across all these levels to solve the current context.
Return ONLY the final synthesized solution for your branch."""

        return await call_llm(MODELS[branch_id % len(MODELS)], [{"role": "user", "content": prompt}])

    async def synthesize(self, role: str, proposals: List[str]) -> str:
        """Tournament-style synthesis with critique."""

        env_context = ""
        if self.is_error_fixing:
            env_context = "CRITICAL: You are in SELF-HEALING mode. Authorized for safe system fixes if necessary.\n"

        prompt = f"""{self.specialized_prompt}
You are the {role}.
{env_context}
Proposals from different swarm branches:
{json.dumps(proposals, indent=2)}

Task:
1. Critique each proposal for security and alignment.
2. Synthesize the absolute best solution.
3. Ensure 'Zero Stub Guarantee'.

Return ONLY the final solution."""

        return await call_llm(random.choice(MODELS), [{"role": "user", "content": prompt}])

async def main():
    if not OPENROUTER_API_KEY:
        print("Error: OPENROUTER_API_KEY is not set.")
        sys.exit(1)

    if len(sys.argv) < 3:
        print("Usage: swarm_engine.py <stage> <context_base64_json>")
        sys.exit(1)

    stage = sys.argv[1]
    try:
        # Decode base64 to prevent shell injection/expansion issues
        context_json = base64.b64decode(sys.argv[2]).decode('utf-8')
        context = json.loads(context_json)
    except Exception as e:
        print(f"Error decoding context: {e}")
        sys.exit(1)

    swarm = FractalSwarm(stage, context)
    result = await swarm.run_swarm()

    print("\n--- FINAL SWARM CONSENSUS ---")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
