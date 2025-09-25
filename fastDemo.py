from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional
import math

app = FastAPI(
    title="Simple FastAPI Demo",
    description="A tiny API exposing a couple of safe, deterministic 'commands'.",
    version="0.1.0",
)

# --------- Schemas ---------
class SumRequest(BaseModel):
    numbers: List[float] = Field(..., description="Numbers to sum and average")

class SumResponse(BaseModel):
    count: int
    sum: float
    average: Optional[float]

class ExtractDomainRequest(BaseModel):
    url: HttpUrl

class ExtractDomainResponse(BaseModel):
    scheme: str
    domain: str
    tld: Optional[str]
    path: str

# --------- Routes ---------
@app.get("/", include_in_schema=False)
async def root():
    return {"message": "FastAPI demo is running", "docs": "/docs", "health": "/health"}

@app.get("/health", tags=["meta"])  
async def health():
    return {"status": "ok"}

@app.post("/commands/sum", response_model=SumResponse, tags=["commands"]) 
async def command_sum(payload: SumRequest):
    if len(payload.numbers) == 0:
        raise HTTPException(400, detail="Provide at least one number")
    total = float(sum(payload.numbers))
    avg = total / len(payload.numbers) if payload.numbers else None
    # Normalize -0.0 to 0.0 for nicer output
    if avg == 0.0:
        avg = 0.0
    if total == 0.0:
        total = 0.0
    return SumResponse(count=len(payload.numbers), sum=total, average=avg)

@app.post("/commands/extract-domain", response_model=ExtractDomainResponse, tags=["commands"]) 
async def command_extract_domain(payload: ExtractDomainRequest):
    # Use stdlib url parsing via pydantic's HttpUrl validation; then pull parts
    parsed = payload.url
    host = parsed.host
    # Attempt to split TLD (naive; avoids external deps)
    tld = None
    if "." in host:
        parts = host.split(".")
        if len(parts) >= 2:
            tld = parts[-1]
    return ExtractDomainResponse(
        scheme=parsed.scheme,
        domain=host,
        tld=tld,
        path=parsed.path or "/",
    )

# --------- Local dev entrypoint ---------
# Run with: uvicorn main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
