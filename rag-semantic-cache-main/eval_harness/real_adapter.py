import os
from eval_harness.adapter import RAGPipelineAdapter
from sentence_transformers import SentenceTransformer, CrossEncoder
import chromadb
from rank_bm25 import BM25Okapi

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

class LocalPipeline(RAGPipelineAdapter):
    def __init__(self):
        print("Loading local models...")
        self.embed_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.rerank_model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        
        self.documents = []
        self.ids = []
        
        filepaths = []
        for root, dirs, files in os.walk(DATA_DIR):
            for file in files:
                if file.endswith(".txt") or file.endswith(".md"):
                    filepaths.append(os.path.join(root, file))
                    
        print(f"🔍 DEBUG: Found {len(filepaths)} files in {DATA_DIR}")
        
        for filepath in filepaths:
            doc_id = os.path.basename(filepath).split(".")[0] 
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    text = f.read().strip()
                    if text: 
                        self.documents.append(text)
                        self.ids.append(doc_id)
            except Exception:
                pass
                
        self.client = chromadb.Client()
        try:
            self.client.delete_collection(name="rag_docs")
        except:
            pass
        self.collection = self.client.create_collection(name="rag_docs")
        
        if self.documents:
            embeddings = self.embed_model.encode(self.documents).tolist()
            self.collection.add(embeddings=embeddings, documents=self.documents, ids=self.ids)
            
            tokenized_corpus = [doc.lower().split(" ") for doc in self.documents]
            self.bm25 = BM25Okapi(tokenized_corpus)
        else:
            self.bm25 = None

    def retrieve(self, query: str, k: int, mode: str) -> list[str]:
        if not self.documents:
            return []

        if mode == "dense":
            query_embedding = self.embed_model.encode([query]).tolist()
            results = self.collection.query(query_embeddings=query_embedding, n_results=min(k, len(self.documents)))
            if results and results.get('ids') and results['ids'][0]:
                return results['ids'][0]
            return []

        elif mode == "lexical":
            if not self.bm25: 
                return []
            tokenized_query = query.lower().split(" ")
            scores = self.bm25.get_scores(tokenized_query)
            ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
            return [self.ids[i] for i in ranked_indices]

        elif mode == "hybrid_rerank":
            query_embedding = self.embed_model.encode([query]).tolist()
            dense_results = self.collection.query(query_embeddings=query_embedding, n_results=min(10, len(self.documents)))
            dense_ids = dense_results['ids'][0] if dense_results and dense_results.get('ids') and dense_results['ids'][0] else []
            
            lexical_ids = []
            if self.bm25:
                tokenized_query = query.lower().split(" ")
                scores = self.bm25.get_scores(tokenized_query)
                lexical_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:10]
                lexical_ids = [self.ids[i] for i in lexical_indices]
            
            rrf_scores = {}
            for rank, doc_id in enumerate(dense_ids):
                rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + (1.0 / (60 + rank + 1))
            for rank, doc_id in enumerate(lexical_ids):
                rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + (1.0 / (60 + rank + 1))
                
            fused_docs = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)[:10]
            if not fused_docs:
                return []
                
            doc_text_map = {self.ids[i]: self.documents[i] for i in range(len(self.ids))}
            pairs = [[query, doc_text_map[doc_id]] for doc_id in fused_docs if doc_id in doc_text_map]
            
            if not pairs:
                return []
                
            rerank_scores = self.rerank_model.predict(pairs)
            reranked = sorted(zip([p[1] for p in pairs], rerank_scores), key=lambda x: x[1], reverse=True)
            
            text_to_id = {text: doc_id for doc_id, text in doc_text_map.items()}
            return [text_to_id[text] for text, score in reranked[:k]]

        return []

    def generate(self, query: str, chunk_ids: list[str]) -> str:
        return f"Based on {chunk_ids}, the answer is found."