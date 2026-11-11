    def retrieve(self, query: str, k: int, mode: str) -> list[str]:
        # Return empty if no documents
        if not self.documents:
            return []

        # Helper to get top N ids from a list of ids with optional scores
        def top_n_ids(ids_list, scores=None, n=10):
            if scores is None:
                return ids_list[:n]
            ranked = sorted(zip(ids_list, scores), key=lambda x: x[1], reverse=True)
            return [i for i, _ in ranked[:n]]

        # Dense retrieval
        if mode == "dense":
            query_emb = self.embed_model.encode([query]).tolist()
            res = self.collection.query(query_embeddings=query_emb, n_results=min(k, len(self.documents)))
            if res and res.get("ids") and res["ids"][0]:
                return res["ids"][0][:k]
            return []

        # Lexical retrieval
        if mode == "lexical":
            if not self.bm25:
                return []
            tokenized = query.lower().split()
            scores = self.bm25.get_scores(tokenized)
            ranked_ids = top_n_ids(self.ids, scores, n=k)
            return ranked_ids

        # Hybrid retrieval with reranking
        if mode == "hybrid_rerank":
            # 1. Dense top 20
            dense_top = 20
            query_emb = self.embed_model.encode([query]).tolist()
            dense_res = self.collection.query(query_embeddings=query_emb,
                                              n_results=min(dense_top, len(self.documents)))
            dense_ids = dense_res["ids"][0] if dense_res and dense_res.get("ids") else []

            # 2. Lexical top 20
            lexical_ids = []
            if self.bm25:
                tokenized = query.lower().split()
                scores = self.bm25.get_scores(tokenized)
                lexical_ids = top_n_ids(self.ids, scores, n=dense_top)

            # 3. RRF fusion
            rrf_scores = {}
            for rank, doc_id in enumerate(dense_ids):
                rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1.0 / (rank + 1)
            for rank, doc_id in enumerate(lexical_ids):
                rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1.0 / (rank + 1)
            fused_ids = sorted(rrf_scores, key=rrf_scores.get, reverse=True)[:dense_top]

            if not fused_ids:
                return []

            # 4. Rerank with cross-encoder
            id_to_text = {doc_id: text for doc_id, text in zip(self.ids, self.documents)}
            pairs = [[query, id_to_text[doc_id]] for doc_id in fused_ids if doc_id in id_to_text]
            if not pairs:
                return []

            rerank_scores = self.rerank_model.predict(pairs)
            reranked = sorted(zip(fused_ids, rerank_scores), key=lambda x: x[1], reverse=True)
            return [doc_id for doc_id, _ in reranked[:k]]

        # Fallback
        return []
