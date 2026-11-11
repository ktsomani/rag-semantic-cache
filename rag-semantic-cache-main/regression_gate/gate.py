def evaluate_regression(current_mix: dict[str, float], baseline_mix: dict[str, float], tolerance: float = 0.03) -> bool:
    """
    Evaluates if the current failure mix has regressed compared to the baseline.
    Returns True if the gate PASSES (no regression), False if it FAILS.
    """
    print(f"Comparing against baseline with ±{tolerance*100:.0f}% tolerance...\n")
    gate_passes = True
    
    for stage, baseline_rate in baseline_mix.items():
        current_rate = current_mix.get(stage, 0.0)
        delta = current_rate - baseline_rate
        
        # We only care if a failure category INCREASES beyond tolerance
        if delta > tolerance:
            print(f"❌ FAIL: {stage.replace('_', ' ').title()} increased by {delta*100:.1f}% (Baseline: {baseline_rate*100:.1f}%, Current: {current_rate*100:.1f}%)")
            gate_passes = False
        else:
            print(f"✅ PASS: {stage.replace('_', ' ').title()} stable (Delta: {delta*100:+.1f}%)")
            
    return gate_passes