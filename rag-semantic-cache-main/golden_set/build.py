import json
from pathlib import Path
from golden_set.schema import GoldenQuestion

def build_sample_golden_set():
    # We create a small sample representing the 60/20/20 split
    questions = [
        # --- ANSWERABLE ---
        GoldenQuestion(
            question_id="q_sky_01",
            question="What color is the sky?",
            stratum="answerable",
            gold_doc_ids=["doc_1"],
            gold_answer="The sky is blue."
        ),
        GoldenQuestion(
            question_id="q_capital_01",
            question="What is the capital of France?",
            stratum="answerable",
            gold_doc_ids=["doc_3"],
            gold_answer="Paris is the capital of France."
        ),
        
        # --- UNANSWERABLE ---
        GoldenQuestion(
            question_id="q_unans_01",
            question="What color is the sky on Mars?",
            stratum="unanswerable",
            gold_doc_ids=[],
            reason_absent="The corpus only discusses Earth's sky, not Mars."
        ),
        
        # --- AMBIGUOUS ---
        GoldenQuestion(
            question_id="q_ambig_01",
            question="What is Python?",
            stratum="ambiguous",
            gold_doc_ids=["doc_4"], # In our mock, it's a programming language
            intent_notes="Could mean the programming language or the snake. Corpus only has programming."
        )
    ]
    
    out_dir = Path("golden_set/data")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "questions.jsonl"
    
    with open(out_file, "w", encoding="utf-8") as f:
        for q in questions:
            # model_dump_json() converts the Pydantic model to a JSON string
            f.write(q.model_dump_json() + "\n")
            
    print(f"Successfully wrote {len(questions)} questions to {out_file}")

if __name__ == "__main__":
    build_sample_golden_set()