!pip -q install -U langmem langchain-openai
from datetime import datetime, timezone
import hashlib
from langmem import create_memory_manager
from langchain_openai import ChatOpenAI

# -------- LLM --------
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    openai_api_key="" #add openAI key here
)

# -------- LangMem extractor --------
manager = create_memory_manager(
    llm,
    instructions=(
        "Extract durable user preferences and stable facts that will be useful later. "
        "Avoid transient or one-off requests. "
        "Write each memory as a short, standalone sentence."
    )
)

# -------- In-notebook memory store --------
# Each item: {fingerprint, text, updated_at}
MEMORY = []

def _fp(text: str) -> str:
    return hashlib.sha256(text.strip().lower().encode("utf-8")).hexdigest()

def upsert_memory(text: str):
    now = datetime.now(timezone.utc)
    fp = _fp(text)
    for m in MEMORY:
        if m["fingerprint"] == fp:
            m["text"] = text
            m["updated_at"] = now
            return
    MEMORY.append({"fingerprint": fp, "text": text, "updated_at": now})

def load_memories(limit: int = 12) -> list[str]:
    return [
        m["text"]
        for m in sorted(MEMORY, key=lambda x: x["updated_at"], reverse=True)[:limit]
    ]

def format_memories(mem_texts: list[str]) -> str:
    if not mem_texts:
        return "None yet."
    return "\n".join(f"- {t}" for t in reversed(mem_texts))

def extract_and_store(recent_messages: list[dict]):
    existing = load_memories(limit=50)
    extracted = manager.invoke({"messages": recent_messages, "existing": existing})

    for item in extracted:
        content = item[1]
        if hasattr(content, "model_dump"):
            d = content.model_dump()
            text = d.get("content") or d.get("text") or str(d)
        else:
            text = str(content)

        text = text.strip()
        if len(text) >= 6:
            upsert_memory(text)

def chat(user_text: str, history: list[dict]) -> tuple[str, list[dict]]:
    mems = load_memories(limit=12)
    system = (
        "You are a helpful assistant.\n\n"
        "User memories (may be relevant):\n"
        f"{format_memories(mems)}\n"
    )

    messages = (
        [{"role": "system", "content": system}]
        + history
        + [{"role": "user", "content": user_text}]
    )

    resp = llm.invoke(messages).content

    new_history = history + [
        {"role": "user", "content": user_text},
        {"role": "assistant", "content": resp},
    ]

    # Only extract from last few turns for speed
    extract_and_store(new_history[-6:])
    return resp, new_history

history = []

print("Commands: mem | reset | exit\n")

while True:
    user_text = input("you> ").strip()
    if not user_text:
        continue
    if user_text.lower() == "exit":
        break
    if user_text.lower() == "mem":
        print("\n[MEMORY]")
        for t in load_memories(limit=50)[::-1]:
            print("-", t)
        print()
        continue
    if user_text.lower() == "reset":
        history = []
        print("(history cleared, memory kept)\n")
        continue

    resp, history = chat(user_text, history)
    print("bot>", resp, "\n")



