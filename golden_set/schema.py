from pydantic import BaseModel, Field
from typing import Literal, Optional

class GoldenQuestion(BaseModel):
    question_id: str = Field(..., description="Unique ID, e.g., 'q_001'")
    question: str = Field(..., description="The user's question text")
    stratum: Literal["answerable", "unanswerable", "ambiguous"]
    
    # Required for 'answerable' and 'ambiguous'
    gold_doc_ids: list[str] = Field(default_factory=list, description="The correct document IDs")
    gold_answer: Optional[str] = Field(None, description="The expected answer text")
    
    # Required for 'unanswerable'
    reason_absent: Optional[str] = Field(None, description="Why the corpus cannot answer this")
    
    # Required for 'ambiguous'
    intent_notes: Optional[str] = Field(None, description="Why the question is ambiguous")