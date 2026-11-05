import os
import time
import json
import asyncio
from functools import partial
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from eval_harness.real_adapter import LocalPipeline
import chromadb

app = FastAPI()

# Add CORS middleware to fix Swagger UI connection issues
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the RAG pipeline
pipeline = LocalPipeline()

# Initialize ChromaDB for Semantic Cache
cache_client = chromadb.Client()
try: 
    cache_client.delete_collection(name="semantic_cache")
except: 
    pass
cache_collection = cache_client.create_collection(name="semantic_cache")

class QueryRequest(BaseModel):
    question: str

def get_current_versions():
    """Safely read versions, returning empty defaults if file is missing."""
    try:
        with open("data/corpus_versions.json", "r") as f:
            data = json.load(f)
        return data.get("corpus_version", "v0"), data.get("document_hashes", {})
    except (FileNotFoundError, json.JSONDecodeError):
        print("⚠️ Warning: corpus_versions.json missing or invalid. Run ingestion.versioner!")
        return "v0", {}

@app.get("/metrics")
def get_metrics():
    return {"cache_size": cache_collection.count()}

@app.post("/query")
async def query_endpoint(request: QueryRequest):
    start_time = time.time()
    
    current_corpus_version, current_doc_hashes = get_current_versions()
    
    # 1. Embed query in a threadpool (prevents blocking the server)
    query_embedding_tensor = await run_in_threadpool(pipeline.embed_model.encode, [request.question])
    # This returns a list of lists: [[0.1, 0.2, ...]]
    query_embedding = query_embedding_tensor.tolist() 
    
    # 2. Semantic Cache Lookup
    cache_results = cache_collection.query(query_embeddings=query_embedding, n_results=1)
    
    cache_hit = False
    answer = ""
    
    if cache_results['distances'] and cache_results['distances'][0]:
        # 0.10 distance = 0.90 cosine similarity threshold
        if cache_results['distances'][0][0] < 0.10:
            cached_meta = cache_results['metadatas'][0][0]
            source_doc_ids = cached_meta['source_doc_ids'].split(",")
            
            is_stale = False
            
            # Check global corpus version
            if cached_meta.get('corpus_version') != current_corpus_version:
                is_stale = True
                
            # Check individual doc hashes
            cached_doc_hashes = json.loads(cached_meta.get('doc_hashes', '{}'))
            for doc_id in source_doc_ids:
                if current_doc_hashes.get(doc_id) != cached_doc_hashes.get(doc_id):
                    is_stale = True
                    break
            
            if not is_stale:
                cache_hit = True
                answer = cached_meta['answer']
            else:
                print(f"⚠️ STALE CACHE DETECTED. Version mismatch.")
                cache_collection.delete(ids=[cache_results['ids'][0][0]])

    # 3. Cache Miss: Retrieve and Generate
    if not cache_hit:
        # Wrap retrieval function with partial so we don't pass kwargs directly to threadpool
        retrieve_fn = partial(pipeline.retrieve, request.question, k=5, mode="hybrid_rerank")
        retrieved_ids = await run_in_threadpool(retrieve_fn)
        
        # --- COMPONENT 5: FALLBACK PATH ---
        async def mock_llm_call():
            # Inject a 5-second delay to simulate a slow LLM
            await asyncio.sleep(5) 
            return f"Generated answer based on {retrieved_ids}"
            
        try:
            # Wait max 3 seconds for the LLM
            answer = await asyncio.wait_for(mock_llm_call(), timeout=3.0)
        except asyncio.TimeoutError:
            print("🚨 FALLBACK TRIGGERED: LLM timed out. Returning degraded response.")
            answer = "DEGRADED: System under high load. Here are the top documents found: " + ", ".join(retrieved_ids)
        # --------------------------------------

        # Store in cache (notice we pass query_embedding directly, not [query_embedding])
        doc_hashes = {doc_id: current_doc_hashes.get(doc_id) for doc_id in retrieved_ids}
        
        cache_collection.add(
            embeddings=query_embedding, 
            documents=[request.question],
            metadatas=[{
                "answer": answer, 
                "source_doc_ids": ",".join(retrieved_ids),
                "doc_hashes": json.dumps(doc_hashes),
                "corpus_version": current_corpus_version
            }],
            ids=[str(hash(request.question))]
        )
        
    ttfb_ms = (time.time() - start_time) * 1000
    print(f"Log: cache_hit={cache_hit}, ttfb_ms={ttfb_ms:.2f}, corpus_version={current_corpus_version[:8]}")
    
    # Return standard JSON so Swagger UI doesn't hang
    return {
        "answer": answer,
        "cache_hit": cache_hit,
        "ttfb_ms": round(ttfb_ms, 2)
    }