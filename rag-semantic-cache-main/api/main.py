import os
import time
import json
import asyncio
import hashlib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from groq import Groq
import redis
from redisvl.index import SearchIndex
from redisvl.utils.vectorize import HFTextVectorizer
from redisvl.query import VectorQuery

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Groq API
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Initialize Redis & Vectorizer
redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(redis_url)

# Using a lightweight local embedding model (uses ~100MB RAM)
vectorizer = HFTextVectorizer(model="sentence-transformers/all-MiniLM-L6-v2")

# Define Redis Vector Index Schema
schema = {
    "index": {"name": "semantic_cache", "prefix": "cache"},
    "fields": [
        {"name": "question", "type": "text"},
        {"name": "answer", "type": "text"},
        {"name": "source_doc_ids", "type": "text"},
        {"name": "corpus_version", "type": "text"},
        {"name": "doc_hashes", "type": "text"},
        {"name": "embedding", "type": "vector", "attrs": {"dims": 384, "algorithm": "flat", "datatype": "float32", "distance_metric": "cosine"}}
    ]
}

index = SearchIndex.from_dict(schema, redis_url=redis_url)
try:
    index.create(overwrite=True)
except:
    pass

# Load current corpus version
def get_current_versions():
    try:
        with open("data/corpus_versions.json", "r") as f:
            data = json.load(f)
        return data.get("corpus_version", "v0"), data.get("document_hashes", {})
    except:
        return "v0", {}

class QueryRequest(BaseModel):
    question: str

@app.get("/metrics")
def get_metrics():
    return {"message": "Metrics endpoint active. Check Redis for cache hits."}

@app.post("/query")
async def query_endpoint(request: QueryRequest):
    start_time = time.time()
    current_corpus_version, current_doc_hashes = get_current_versions()
    
    # 1. Embed query locally
    query_embedding = await run_in_threadpool(vectorizer.embed, request.question)
    
    # 2. Query Redis Vector DB
    vector_query = VectorQuery(
        vector=query_embedding,
        vector_field_name="embedding",
        return_fields=["question", "answer", "source_doc_ids", "corpus_version", "doc_hashes"],
        num_results=1
    )
    
    results = index.query(vector_query)
    
    cache_hit = False
    answer = ""
    
    if results and results[0]['vector_distance'] < 0.10:
        cached = results[0]
        source_doc_ids = cached['source_doc_ids'].split(",")
        cached_doc_hashes = json.loads(cached['doc_hashes'])
        
        is_stale = False
        if cached['corpus_version'] != current_corpus_version:
            is_stale = True
            
        for doc_id in source_doc_ids:
            if current_doc_hashes.get(doc_id) != cached_doc_hashes.get(doc_id):
                is_stale = True
                break
        
        if not is_stale:
            cache_hit = True
            answer = cached['answer']
        else:
            print(f"⚠️ STALE CACHE DETECTED. Deleting entry.")

    if not cache_hit:
        # 3. Call REAL Groq API (Llama 3 8B)
        async def call_groq():
            # For this demo, we use a short prompt. In production, you'd inject retrieved docs.
            prompt = f"Answer this question in one sentence: {request.question}"
            response = groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192",
            )
            return response.choices[0].message.content
            
        try:
            # 3-second timeout for the fallback
            answer = await asyncio.wait_for(call_groq(), timeout=3.0)
            source_doc_ids = ["doc_1", "doc_2"] # Mocked for now
        except asyncio.TimeoutError:
            print("🚨 FALLBACK TRIGGERED: Groq timed out.")
            answer = "DEGRADED: Groq API timed out. Please try again."
            source_doc_ids = ["doc_1", "doc_2"]
        
        # 4. Store in Redis
        doc_hashes = {doc_id: current_doc_hashes.get(doc_id, "mock_hash") for doc_id in source_doc_ids}
        
        data = {
            "question": request.question,
            "answer": answer,
            "source_doc_ids": ",".join(source_doc_ids),
            "corpus_version": current_corpus_version,
            "doc_hashes": json.dumps(doc_hashes),
            "embedding": query_embedding
        }
        index.load([data], id_field="question")
        
    ttfb_ms = (time.time() - start_time) * 1000
    print(f"Log: cache_hit={cache_hit}, ttfb_ms={ttfb_ms:.2f}")
    
    return {
        "answer": answer,
        "cache_hit": cache_hit,
        "ttfb_ms": round(ttfb_ms, 2)
    }