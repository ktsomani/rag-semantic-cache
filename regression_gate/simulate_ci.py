from regression_gate.gate import evaluate_regression

def run_simulation():
    print("--- Scenario A: Stable System ---")
    baseline = {
        "retrieval_gap": 0.10,
        "rank_inversion": 0.08,
        "evidence_under_use": 0.15,
        "fabrication": 0.05
    }
    # Current is identical to baseline
    current_stable = {
        "retrieval_gap": 0.10,
        "rank_inversion": 0.08,
        "evidence_under_use": 0.15,
        "fabrication": 0.05
    }
    
    gate_passed = evaluate_regression(current_stable, baseline)
    print(f"\nGate Decision: {'PASS ✅' if gate_passed else 'FAIL ❌'}\n")
    print("-" * 40 + "\n")

    print("--- Scenario B: The Silent Regression ---")
    print("(Aggregate accuracy is flat, but fabrication spiked and evidence under-use dropped)")
    
    # Total failures are the same, but the mix shifted. 
    # We accidentally fixed evidence under-use, but introduced hallucinations.
    current_regressed = {
        "retrieval_gap": 0.10,
        "rank_inversion": 0.08,
        "evidence_under_use": 0.05, # Improved!
        "fabrication": 0.15       # REGRESSION! (Spiked by 10%)
    }
    
    gate_passed = evaluate_regression(current_regressed, baseline)
    print(f"\nGate Decision: {'PASS ✅' if gate_passed else 'FAIL ❌'}")
    if not gate_passed:
        print("CI/CD Build Blocked. Fix fabrication before merging.")

if __name__ == "__main__":
    run_simulation()