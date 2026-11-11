from typing import Any
from eval_harness.adapter import RAGPipelineAdapter

class MockPipeline:
    """
    A fake RAG pipeline used to test the evaluation harness.
    It intentionally simulates different failure modes based on the retrieval mode.
    """
    
    def __init__(self):
        # A tiny fake corpus
        self.corpus = {
            "doc_1": "The sky is blue.",
            "doc_2": "Water is wet.",
            "doc_3": "The capital of France is Paris.",
            "doc_4": "Python is a programming language."
        }
        
    def retrieve(self, query: str, k: int, mode: str) -> list[str]:
        """Simulates different retrieval behaviors based on the mode."""
        if "sky" in query.lower():
            if mode == "dense":
                # Success: Gold doc is rank 1
                return ["doc_1", "doc_2", "doc_4"][:k]
            elif mode == "lexical":
                # Rank Inversion: Gold doc is retrieved, but pushed down to rank 3
                return ["doc_2", "doc_4", "doc_1"][:k]
            elif mode == "hybrid_rerank":
                # Retrieval Gap: Gold doc is completely missed
                return ["doc_2", "doc_4", "doc_3"][:k]
                
        elif "capital" in query.lower():
             # Always succeeds for this query
            return ["doc_3", "doc_1", "doc_2"][:k]
            
        return ["doc_4", "doc_2", "doc_1"][:k]

    def generate(self, query: str, chunk_ids: list[str]) -> str:
        """Simulates generation and evidence use/fabrication."""
        if "sky" in query.lower():
            if "doc_1" in chunk_ids:
                # Evidence Under-use: The right doc is there, but the model ignores it
                return "The sky is green." 
            else:
                # Fabrication: The model makes something up without evidence
                return "The sky is purple and made of cheese."
                
        elif "capital" in query.lower() and "doc_3" in chunk_ids:
            # Success: Uses the evidence
            return "The capital of France is Paris [doc_3]."
            
        return "I don't know."

    def get_metadata(self) -> dict[str, Any]:
        return {"model": "mock-llm-v1", "embedding": "mock-embed-v1"}