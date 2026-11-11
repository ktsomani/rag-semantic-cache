from dataclasses import dataclass
from eval_harness.taxonomy import FailureStage

@dataclass
class Trace:
    question_id: str
    stratum: str
    gold_doc_ids: list[str]
    retrieved_ids: list[str]
    generated_answer: str
    mode: str

def attribute_failure(trace: Trace, is_evidence_used: bool) -> FailureStage:
    """
    Evaluates a single trace and attributes it to the correct pipeline stage.
    Note: 'is_evidence_used' would normally be evaluated by an NLI model in production, 
    but we pass it in manually here to test the logic.
    """
    
    # 1. Handle Unanswerable Questions (Abstention)
    if trace.stratum == "unanswerable":
        # If the model generated a substantive answer instead of saying "I don't know"
        if "I don't know" not in trace.generated_answer.lower():
            return FailureStage.ABSTENTION_FAILURE
        return FailureStage.SUCCESS

    # 2. Handle Answerable/Ambiguous Questions
    # Check if the gold document was even retrieved
    retrieved_gold_docs = [doc for doc in trace.gold_doc_ids if doc in trace.retrieved_ids]
    
    if not retrieved_gold_docs:
        # The gold doc is not in the top-k
        return FailureStage.RETRIEVAL_GAP
        
    # Check the rank of the first relevant document
    first_relevant_rank = None
    for rank, doc_id in enumerate(trace.retrieved_ids, start=1):
        if doc_id in trace.gold_doc_ids:
            first_relevant_rank = rank
            break
            
    # For this example, we define Top-1 as the cutoff for optimal rank
    if first_relevant_rank > 1:
        return FailureStage.RANK_INVERSION

    # 3. Handle Generation/Evidence Use
    # If we get here, the gold doc was at Rank 1.
    if not is_evidence_used:
        return FailureStage.EVIDENCE_UNDER_USE

    # In a real system, we would also check for FABRICATION here 
    # (e.g., claims in the answer not supported by the gold doc).
    # For this step, if the evidence was used and it's rank 1, it's a success.
    
    return FailureStage.SUCCESS