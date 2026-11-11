from sklearn.metrics import cohen_kappa_score
from eval_harness.taxonomy import FailureStage

def calculate_iaa():
    # Simulating 20 traces labeled by two independent annotators.
    # We use the FailureStage enum values.
    
    # Annotator A's labels
    annotator_a = [
        FailureStage.EVIDENCE_UNDER_USE.value,
        FailureStage.RETRIEVAL_GAP.value,
        FailureStage.RANK_INVERSION.value,
        FailureStage.FABRICATION.value,
        FailureStage.EVIDENCE_UNDER_USE.value,
        FailureStage.EVIDENCE_UNDER_USE.value,
        FailureStage.RETRIEVAL_GAP.value,
        FailureStage.RANK_INVERSION.value,
        FailureStage.FABRICATION.value,
        FailureStage.SUCCESS.value,
        FailureStage.ABSTENTION_FAILURE.value,
        FailureStage.RETRIEVAL_GAP.value,
        FailureStage.EVIDENCE_UNDER_USE.value,
        FailureStage.RANK_INVERSION.value,
        FailureStage.FABRICATION.value,
        FailureStage.SUCCESS.value,
        FailureStage.RETRIEVAL_GAP.value,
        FailureStage.EVIDENCE_UNDER_USE.value,
        FailureStage.RANK_INVERSION.value,
        FailureStage.FABRICATION.value,
    ]

    # Annotator B's labels (Notice the disagreements on indices 2, 8, and 16)
    annotator_b = [
        FailureStage.EVIDENCE_UNDER_USE.value,
        FailureStage.RETRIEVAL_GAP.value,
        FailureStage.RETRIEVAL_GAP.value,       # <-- Disagreement: B says Retrieval Gap, A says Rank Inversion
        FailureStage.FABRICATION.value,
        FailureStage.EVIDENCE_UNDER_USE.value,
        FailureStage.EVIDENCE_UNDER_USE.value,
        FailureStage.RETRIEVAL_GAP.value,
        FailureStage.RANK_INVERSION.value,
        FailureStage.EVIDENCE_UNDER_USE.value,  # <-- Disagreement: B says Evidence Under-use, A says Fabrication
        FailureStage.SUCCESS.value,
        FailureStage.ABSTENTION_FAILURE.value,
        FailureStage.RETRIEVAL_GAP.value,
        FailureStage.EVIDENCE_UNDER_USE.value,
        FailureStage.RANK_INVERSION.value,
        FailureStage.FABRICATION.value,
        FailureStage.SUCCESS.value,
        FailureStage.RETRIEVAL_GAP.value,
        FailureStage.RETRIEVAL_GAP.value,       # <-- Disagreement: B says Retrieval Gap, A says Evidence Under-use
        FailureStage.RANK_INVERSION.value,
        FailureStage.FABRICATION.value,
    ]

    # Calculate Cohen's Kappa
    kappa = cohen_kappa_score(annotator_a, annotator_b)

    print("--- Inter-Annotator Agreement ---")
    print(f"Total traces labeled: {len(annotator_a)}")
    print(f"Cohen's Kappa: {kappa:.3f}\n")

    # Interpretation thresholds
    if kappa > 0.80:
        print("Result: EXCELLENT (κ > 0.80)")
        print("The taxonomy boundaries are clear. Proceed to adjudication.")
    elif kappa >= 0.60:
        print("Result: ACCEPTABLE (0.60 <= κ <= 0.80)")
        print("Minor ambiguity. Document the edge cases and proceed.")
    else:
        print("Result: MEASUREMENT FINDING (κ < 0.60)")
        print("The taxonomy is under-specified or the failure mode is genuinely multi-causal.")
        print("Action: Run a taxonomy-refinement round. Inspect the disagreement log,")
        print("merge overlapping codes, and recalibrate annotators before re-labeling.")

if __name__ == "__main__":
    calculate_iaa()