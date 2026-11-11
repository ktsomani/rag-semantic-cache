from typing import Protocol, Any

class RAGPipelineAdapter(Protocol):
    """
    The standard interface any RAG pipeline must implement to be evaluated 
    by the Failure Attribution Protocol.
    """

    def retrieve(self, query: str, k: int, mode: str) -> list[str]:
        """
        Retrieve the top-k chunk IDs for a given query.
        
        Args:
            query: The user's question.
            k: The number of chunks to return.
            mode: The retrieval strategy to use. Must be one of:
                  "dense", "lexical", or "hybrid_rerank".
                  
        Returns:
            A list of unique string IDs representing the chunks, ordered 
            by relevance (highest first).
        """
        ...

    def generate(self, query: str, chunk_ids: list[str]) -> str:
        """
        Generate an answer using the provided chunks.
        
        Args:
            query: The user's question.
            chunk_ids: The list of chunk IDs retrieved in the previous step.
            
        Returns:
            The generated answer string. 
            If generating citations, format them as [chunk_id] inline.
        """
        ...

    def get_metadata(self) -> dict[str, Any]:
        """
        Optional method to expose pipeline configuration.
        Useful for logging what model/embedding was used during this eval run.
        """
        return {}