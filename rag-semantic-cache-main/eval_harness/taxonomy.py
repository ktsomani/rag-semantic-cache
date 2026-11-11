from enum import Enum

class FailureStage(Enum):
    SUCCESS = "success"
    INGESTION = "ingestion"
    RETRIEVAL_GAP = "retrieval_gap"
    RANK_INVERSION = "rank_inversion"
    EVIDENCE_UNDER_USE = "evidence_under_use"
    FABRICATION = "fabrication"
    ABSTENTION_FAILURE = "abstention_failure"