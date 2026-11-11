import os
import json
import random

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUT_DIR = os.path.join(BASE_DIR, "golden_set", "data")

def generate_questions():
    files = []
    for root, dirs, filenames in os.walk(DATA_DIR):
        for file in filenames:
            if file.endswith(".txt") or file.endswith(".md"):
                files.append(os.path.join(root, file))
    
    if len(files) < 10:
        print(f"Not enough files in {DATA_DIR}. Found {len(files)}.")
        return

    random.seed(42)
    random.shuffle(files)
    
    questions = []
    
    for i, filepath in enumerate(files[:10]):
        doc_id = os.path.basename(filepath).split(".")[0]
        
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read().strip()
            
        snippet = text[:150].replace("\n", " ")
        q_text = f"What does this document say about {snippet[:40]}...?"
        
        questions.append({
            "question_id": f"q_{i+1}",
            "question": q_text,
            "stratum": "answerable",
            "gold_doc_ids": [doc_id]
        })
        
    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, "questions.jsonl")
    
    with open(out_path, "w", encoding="utf-8") as f:
        for q in questions:
            f.write(json.dumps(q) + "\n")
            
    print(f"✅ Generated 10 new questions and saved to {out_path}")

if __name__ == "__main__":
    generate_questions()