# Resilient RAG Semantic Cache & Reliability Layer

A production-focused Semantic Cache built in front of a RAG pipeline. This project addresses three major issues in deploying LLM applications:
1. **Cost & Latency:** Redundant queries hit the LLM and vector database unnecessarily.
2. **Staleness:** When underlying documents change, cached answers become factually incorrect.
3. **Resilience:** When the LLM backend goes down or times out, the API should degrade gracefully, not crash.

## 🏗️ Architecture
*   **API:** FastAPI (Python 3.11)
*   **Cache:** Redis Stack (Distributed Vector Search)
*   **Embeddings:** HuggingFace `all-MiniLM-L6-v2` (CPU-optimized)
*   **LLM:** Groq API (`openai/gpt-oss-20b`)
*   **Deployment:** Docker Compose

## 🚀 Core Features
1. **Semantic Cache:** Embeds the incoming query and checks for cosine similarity against previous queries using Redis Stack. If the distance is `< 0.20`, the cached answer is returned.
2. **Staleness Detection & Mitigation:** Documents are hashed using MD5. When a document changes, the `corpus_version` is bumped. Before serving a cache hit, the API verifies the document hashes. If they are stale, the cache is invalidated and a fresh response is generated.
3. **Graceful Fallback:** If the LLM generation exceeds a 3-second timeout, the system catches the timeout and returns a degraded, labelled response with the retrieved documents instead of failing the request.

## 📊 Measured Results (Locust Load Test)

**Environment:** Local 8GB Windows Machine, Docker Compose (FastAPI + Redis Stack).

**Test Setup:** Locust was run with 10 concurrent users against a fixed list of questions.

| Metric | Value | Notes |
| :--- | :--- | :--- |
| **Cache Hit Rate** | ~85% | Estimated based on latency distribution. |
| **Hit Latency (Median)** | 84 ms | Query embedding + Redis vector lookup. |
| **Miss Latency (Min)** | 3,200 ms | Real Groq API call and generation. |
| **Sustained Throughput** | 5.35 RPS | Peak burst was 9.40 RPS. |
| **Error Rate** | 0.00% | 0 failures. |
| **p95 Latency** | 6,000 ms | Dominated by cold misses hitting the threadpool queue. |

## 🧪 Staleness Detection Test
*   **Test:** All cached answers' source documents were manually modified. The versioning script (`ingestion/versioner.py`) was run to bump the global corpus hash.
*   **Result Before Mitigation:** 10/10 affected queries served stale answers.
*   **Result After Mitigation:** 0/10 affected queries served a stale answer. 
*   **Cost:** The MD5 hash verification adds ~2ms to the cache lookup latency.

## 🐳 Docker Substrate Optimization
*   **The CUDA Trap:** The initial Docker build failed because PyTorch attempted to download 4GB of NVIDIA CUDA drivers, causing a network timeout.
*   **The Fix:** Modified the Dockerfile to force a CPU-only PyTorch installation (`--index-url https://download.pytorch.org/whl/cpu`), reducing the container size by over 80% and drastically speeding up CI builds.

## ⚠️ Limitations & Trade-offs (Honest Assessment)
*   **Single-Node Prototype:** This is a containerized single-node deployment. While the interfaces are designed to support a Redis Cluster, it is not currently deployed in a distributed environment.
*   **Thundering Herd (Cache Stampede):** In the current implementation, if 100 requests hit a cold cache simultaneously, they will all queue at the threadpool and hit the LLM. In production, I would implement a Redis distributed lock (`SETNX`) so only the first request calls the LLM, while the others wait asynchronously for the cache to populate.
*   **Retry Semantics:** I intentionally did not implement automatic retries for the LLM call. If the LLM times out, I immediately return the degraded response. Retrying a non-deterministic LLM call can result in state inconsistency (the user sees two different answers). In a production system, I would implement controlled retries with exponential backoff and idempotency keys on the LLM request.

## 🛠️ How to Run
1. Ensure Docker Desktop is running.
2. Export your Groq API key:
   ```bash
   export GROQ_API_KEY="gsk_your_key_here"