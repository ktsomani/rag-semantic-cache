import json
import math
from pathlib import Path
from eval_harness.real_adapter import LocalPipeline

def calculate_metrics(retrieved_ids, gold_ids, k):
    if not retrieved_ids or not gold_ids:
        return 0.0, 0.0, 0.0
        
    top_k = retrieved_ids[:k]
    recall = sum(1 for d in gold_ids if d in top_k) / len(gold_ids)
    
    mrr = 0.0
    for i, d in enumerate(top_k):
        if d in gold_ids:
            mrr = 1.0 / (i + 1)
            break
            
    # nDCG calculation
    dcg = 0.0
    idcg = 0.0
    for i, d in enumerate(top_k):
        rel = 1.0 if d in gold_ids else 0.0
        dcg += rel / math.log2(i + 2)
    for i in range(min(len(gold_ids), k)):
        idcg += 1.0 / math.log2(i + 2)
    ndcg = dcg / idcg if idcg > 0 else 0.0
    
    return recall, mrr, ndcg

def run_retrieval_eval():
    with open("golden_set/data/questions.jsonl", "r", encoding="utf-8") as f:
        questions = [json.loads(line) for line in f]
            
    pipeline = LocalPipeline()
    
    modes = ["dense", "lexical", "hybrid_rerank"]
    k = 10 # Evaluate at top-10
    
    print(f"\nEvaluating Retrieval Modes at k={k} (SciFact Test Split)...\n")
    print(f"{'Mode':<15} | {'Recall@10':<10} | {'MRR':<10} | {'nDCG@10':<10}")
    print("-" * 55)

    for mode in modes:
        total_recall, total_mrr, total_ndcg = 0.0, 0.0, 0.0
        count = 0
        
        for q in questions:
            if q["stratum"] != "answerable": continue
            count += 1
            
            retrieved = pipeline.retrieve(q["question"], k=k, mode=mode)
            r, m, n = calculate_metrics(retrieved, q["gold_doc_ids"], k)
            
            total_recall += r
            total_mrr += m
            total_ndcg += n
            
        if count > 0:
            print(f"{mode:<15} | {total_recall/count:<10.3f} | {total_mrr/count:<10.3f} | {total_ndcg/count:<10.3f}")

if __name__ == "__main__":
    run_retrieval_eval()