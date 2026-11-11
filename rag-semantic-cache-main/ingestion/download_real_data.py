import os
import json
from datasets import load_dataset

def download_and_save():
    print("Downloading full SciFact dataset...")
    corpus = load_dataset("BeIR/scifact", "corpus", split="corpus")
    queries = load_dataset("BeIR/scifact", "queries", split="queries")
    qrels = load_dataset("BeIR/scifact-qrels", split="test") # Use the official test split

    os.makedirs("data", exist_ok=True)
    for f in os.listdir("data"):
        if f.endswith(".txt"):
            os.remove(os.path.join("data", f))
            
    valid_doc_ids = set()
    print(f"Saving all {len(corpus)} real documents...")
    for doc in corpus:
        doc_id = str(doc['_id'])
        valid_doc_ids.add(doc_id)
        content = f"{doc.get('title', '')} {doc.get('text', '')}".strip()
        with open(f"data/{doc_id}.txt", "w", encoding="utf-8") as f:
            f.write(content)

    print("Saving official test queries...")
    questions = []
    query_map = {str(q['_id']): q['text'] for q in queries}
    
    for qrel in qrels:
        query_id = str(qrel['query-id'])
        corpus_id = str(qrel['corpus-id'])
        
        # BEIR qrels might have multiple docs per query, but we'll take the first gold doc for simplicity
        if query_id in query_map:
            # Check if we already added this query
            if not any(q['question_id'] == query_id for q in questions):
                questions.append({
                    "question_id": query_id,
                    "question": query_map[query_id],
                    "stratum": "answerable",
                    "gold_doc_ids": [corpus_id]
                })

    os.makedirs("golden_set/data", exist_ok=True)
    with open("golden_set/data/questions.jsonl", "w", encoding="utf-8") as f:
        for q in questions:
            f.write(json.dumps(q) + "\n")

    print(f"✅ Downloaded {len(valid_doc_ids)} docs and {len(questions)} official test queries.")

if __name__ == "__main__":
    download_and_save()