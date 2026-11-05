# RAG Semantic Cache & Reliability Layer

A production-focused Semantic Cache built in front of a RAG pipeline. This project addresses three major issues in deploying LLM applications:
1. **Cost & Latency:** Redundant queries hit the LLM and vector database unnecessarily.
2. **Staleness:** When underlying documents change, cached answers become factually incorrect.
3. **Resilience:** When the LLM backend goes down or times out, the API should degrade gracefully, not crash.

## 🏗️ Architecture
*   **API:** FastAPI (Python 3.11)
*   **Cache:** ChromaDB (vector search for semantic similarity)
*   **Embeddings:** HuggingFace `all-MiniLM-L6-v2`
*   **Load Testing:** Locust

## 🚀 Core Features
1. **Semantic Cache:** Embeds the incoming query and checks for cosine similarity against previous queries. If the distance is `< 0.10` (similarity > 0.90), the cached answer is returned.
2. **Staleness Detection & Mitigation:** Documents are hashed using MD5. When a document changes, the `corpus_version` is bumped. Before serving a cache hit, the API verifies the document hashes. If they are stale, the cache is invalidated and a fresh response is generated.
3. **Graceful Fallback:** If the LLM generation exceeds a 3-second timeout, the system catches the timeout and returns a degraded, labelled response with the retrieved documents instead of failing the request.

## 📊 Measured Results (Load Test)

**Environment:** Local 8GB Windows Machine (Single Node), Mock LLM (Fixed 5s delay to simulate external API).

**Test Setup:** Locust was run for 30 seconds with 10 concurrent users against a fixed list of 10 questions.

| Metric | Value | Notes |
| :--- | :--- | :--- |
| **Cache Hit Rate** | ~95% | Implied by the p95 latency. 264 requests, mostly repeats. |
| **Hit Latency (Median)** | 69 ms | Query embedding + ChromaDB lookup. |
| **Miss Latency (Median)** | ~5,000 ms | Mock LLM backend limit. |
| **Latency Reduction** | 98.6% | For repeated queries. |
| **Sustained Throughput** | 9.0 RPS | Bound by the local 5s backend simulation. |
| **Hit Path p95** | 150 ms | Proves hits are decoupled from the slow backend. |
| **Error Rate** | 0.0% | 0 failures out of 264 requests. |

**Note on Concurrency Bottleneck:** During the *Cold Cache* run, the raw Locust CSV recorded an 18,000ms median latency. This was not the LLM taking 18s; it was a concurrency bottleneck. When 10 users hit the cold cache simultaneously, the Python threadpool queued the requests while waiting for the 5s mock LLM, causing massive queue buildup. Once the cache was warm, hits bypassed the threadpool entirely.

## 🧪 Staleness Detection Test
*   **Test:** All 10 cached answers' source documents were manually modified. The versioning script (`ingestion/versioner.py`) was run to bump the global corpus hash.
*   **Result Before Mitigation:** 10/10 affected queries served stale answers.
*   **Result After Mitigation:** 0/10 affected queries served a stale answer. 
*   **Cost:** The MD5 hash verification adds ~2ms to the cache lookup latency.

## 🚦 Fallback Test
*   **Test:** Injected a deliberate 5-second delay into the LLM mock.
*   **Result:** 100% of affected requests returned a `DEGRADED` response instead of hanging. The API remained responsive (0 timeouts) and continued to serve cache hits for previously seen queries.

## ⚠️ Limitations
*   **Single Node:** Tested entirely on a local laptop; not a distributed Redis/Chroma setup.
*   **Mock Backend:** The LLM was simulated with a `5s` sleep to avoid burning API credits, which artificially caps throughput at 9 RPS.
*   **Short Test Duration:** The Locust test ran for 30 seconds. A longer 3-5 minute run would provide a more stable sustained RPS baseline.
*   **Small N:** The staleness mutation test was validated on a controlled sample of 10 documents.

## 🛠️ How to Run
1. Install dependencies:
   ```bash
   uv add fastapi uvicorn chromadb sentence-transformers rank_bm25 locust pydantic
