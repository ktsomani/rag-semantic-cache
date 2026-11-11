import math
from collections import defaultdict

class LocalPipeline(RAGPipelineAdapter):
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.client = chromadb.Client()
        try:
            self.client.delete_collection(name="rag_docs")
        except:
            pass
        self.collection = self.client.create_collection(name="rag_docs")
        documents = []
        ids = []
        for filepath in glob.glob("data/*.txt"):
            doc_id = os.path.basename(filepath).replace(".txt", "")
            with open(filepath, "r") as f:
                text = f.read().strip()
                documents.append(text)
                ids.append(doc_id)
        if documents:
            embeddings = self.model.encode(documents).tolist()
            self.collection.add(
                embeddings=embeddings,
                documents=documents,
                ids=ids
            )

    def _bm25_score(self, query_tokens, tokenized_docs):
        N = len(tokenized_docs)
        df = defaultdict(int)
        for doc in tokenized_docs:
            unique_terms = set(doc)
            for term in unique_terms:
                df[term] += 1
        idf = {}
        for term, freq in df.items():
            idf[term] = math.log(1 + (N - freq + 0.5) / (freq + 0.5))
        scores = []
        avgdl = sum(len(doc) for doc in tokenized_docs) / N
        k1 = 1.5
        b = 0.75
        for doc in tokenized_docs:
            score = 0.0
            term_freq = defaultdict(int)
            for term in doc:
                term_freq[term] += 1
            for term in query_tokens:
                if term in term_freq:
                    tf = term_freq[term]
                    denom = tf + k1 * (1 - b + b * len(doc) / avgdl)
                    score += idf.get(term, 0) * (tf * (k1 + 1)) / denom
            scores.append(score)
        return scores

    def retrieve(self, query: str, k: int, mode: str) -> list[str]:
        query_embedding = self.model.encode([query]).tolist()
        # Increase candidate pool for reranking
        candidate_k = min(k * 2, 1000)
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=candidate_k
        )
        if not results or not results.get('ids'):
            return []
        candidate_ids = results['ids'][0]
        # Fetch documents for candidate ids
        docs_res = self.collection.get(ids=candidate_ids)
        candidate_docs = docs_res.get('documents', [])
        # Tokenize query and documents
        query_tokens = query.lower().split()
        tokenized_docs = [doc.lower().split() for doc in candidate_docs]
        # Compute BM25 scores
        scores = self._bm25_score(query_tokens, tokenized_docs)
        # Pair ids with scores and sort
        id_score_pairs = list(zip(candidate_ids, scores))
        id_score_pairs.sort(key=lambda x: x[1], reverse=True)
        # Return top-k ids after reranking
        reranked_ids = [pair[0] for pair in id_score_pairs[:k]]
        return reranked_ids

    def generate(self, query: str, chunk_ids: list[str]) -> str:
        return f"Based on {chunk_ids}, the answer is found."