from datetime import datetime, timezone
from pymongo import MongoClient, ASCENDING, DESCENDING
from langmem import create_memory_manager
from langchain_openai import ChatOpenAI

# ----- Mongo -----
client = MongoClient("mongodb://localhost:27017")
db = client["langmem_demo"]
mem_col = db["memories"]

# Helpful indexes
mem_col.create_index([("user_id", ASCENDING), ("updated_at", DESCENDING)])
mem_col.create_index([("user_id", ASCENDING), ("fingerprint", ASCENDING)], unique=True)

def load_memories(user_id: str, limit: int = 12) -> list[dict]:
    return list(
        mem_col.find({"user_id": user_id}, {"_id": 0})
               .sort("updated_at", DESCENDING)
               .limit(limit)
    )

def format_memories_for_prompt(memories: list[dict]) -> str:
    if not memories:
        return "None yet."
    lines = []
    for m in memories[::-1]:  # oldest->newest for readability
        lines.append(f"- {m['text']}")
    return "\n".join(lines)

# Simple stable key so we upsert rather than endlessly append duplicates.
# (You can make this smarter later.)
import hashlib
def fingerprint(text: str) -> str:
    return hashlib.sha256(text.strip().lower().encode("utf-8")).hexdigest()

def upsert_memory(user_id: str, text: str):
    now = datetime.now(timezone.utc)
    fp = fingerprint(text)
    mem_col.update_one(
        {"user_id": user_id, "fingerprint": fp},
        {"$set": {"user_id": user_id, "text": text, "updated_at": now}},
        upsert=True,
    )

# ----- LangMem extractor -----
# This returns a list of "ExtractedMemory" items; docs show you can access content as item[1]. :contentReference[oaicite:0]{index=0}
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
manager = create_memory_manager(
    llm,
    instructions="Extract durable user preferences and stable facts. "
                 "Avoid one-off requests and transient details."
)

def extract_and_store(user_id: str, recent_messages: list[dict], existing_texts: list[str]):
    # Existing needs to match the manager's expected structure; simplest is pass extracted memory tuples back in.
    # We'll just pass strings as "existing" since unstructured memories are allowed. :contentReference[oaicite:1]{index=1}
    extracted = manager.invoke({"messages": recent_messages, "existing": existing_texts})

    # extracted elements behave like tuples; content is at [1] per docs example. :contentReference[oaicite:2]{index=2}
    for item in extracted:
        content = item[1]
        if hasattr(content, "model_dump"):
            text = str(content.model_dump())
        else:
            text = str(content)
        upsert_memory(user_id, text)

def chat_turn(user_id: str, user_text: str, history: list[dict]) -> tuple[str, list[dict]]:
    # 1) Retrieve (simple: last N)
    memories = load_memories(user_id, limit=12)
    memory_block = format_memories_for_prompt(memories)

    # 2) Ask model, injecting memory
    system = (
        "You are a helpful assistant.\n\n"
        "User memories (may be relevant):\n"
        f"{memory_block}\n"
    )

    messages = [{"role": "system", "content": system}] + history + [{"role": "user", "content": user_text}]
    resp = llm.invoke(messages).content

    # 3) Persist new/updated memories (LangMem decides)
    new_history = history + [{"role": "user", "content": user_text}, {"role": "assistant", "content": resp}]
    existing_texts = [m["text"] for m in memories]
    extract_and_store(user_id, recent_messages=new_history[-6:], existing_texts=existing_texts)

    return resp, new_history

# ----- Demo -----
user_id = "demo"
history = []

resp, history = chat_turn(user_id, "Hey I'm Sam. Keep answers short. Also I'm allergic to peanuts.", history)
print(resp)

resp, history = chat_turn(user_id, "Suggest a snack idea.", history)
print(resp)

print("\nStored memories:")
for m in load_memories(user_id, limit=50)[::-1]:
    print("-", m["text"])
