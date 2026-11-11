from eval_harness.attribute import Trace, attribute_failure

def test_attribution():
    print("--- Testing Failure Attribution ---\n")

    # SCENARIO 1: Dense Mode (Retrieved doc_1, but generated wrong answer)
    trace_1 = Trace(
        question_id="q_sky_01",
        stratum="answerable",
        gold_doc_ids=["doc_1"],
        retrieved_ids=["doc_1", "doc_2", "doc_4"],
        generated_answer="The sky is green.",
        mode="dense"
    )
    # We know the model ignored the evidence because it said "green" instead of "blue"
    label_1 = attribute_failure(trace_1, is_evidence_used=False)
    print(f"Scenario 1 (Dense): {label_1.value.upper()}")

    # SCENARIO 2: Lexical Mode (Retrieved doc_1, but at Rank 3)
    trace_2 = Trace(
        question_id="q_sky_01",
        stratum="answerable",
        gold_doc_ids=["doc_1"],
        retrieved_ids=["doc_2", "doc_4", "doc_1"],
        generated_answer="The sky is green.",
        mode="lexical"
    )
    label_2 = attribute_failure(trace_2, is_evidence_used=False)
    print(f"Scenario 2 (Lexical): {label_2.value.upper()}")

    # SCENARIO 3: Hybrid Mode (Missed doc_1 entirely)
    trace_3 = Trace(
        question_id="q_sky_01",
        stratum="answerable",
        gold_doc_ids=["doc_1"],
        retrieved_ids=["doc_2", "doc_4", "doc_3"],
        generated_answer="The sky is purple and made of cheese.",
        mode="hybrid_rerank"
    )
    label_3 = attribute_failure(trace_3, is_evidence_used=False)
    print(f"Scenario 3 (Hybrid): {label_3.value.upper()}")

    # SCENARIO 4: Unanswerable Question answered incorrectly
    trace_4 = Trace(
        question_id="q_unans_01",
        stratum="unanswerable",
        gold_doc_ids=[],
        retrieved_ids=["doc_2", "doc_4"],
        generated_answer="The sky on Mars is red.",
        mode="dense"
    )
    label_4 = attribute_failure(trace_4, is_evidence_used=False)
    print(f"Scenario 4 (Unanswerable): {label_4.value.upper()}")

if __name__ == "__main__":
    test_attribution()