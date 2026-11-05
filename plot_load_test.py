import pandas as pd
import matplotlib.pyplot as plt

def plot_results():
    try:
        df = pd.read_csv("warm_run_stats_history.csv")
        
        # Drop the initial 5 seconds to ignore the ramp-up spike
        min_time = df["Timestamp"].min()
        df = df[df["Timestamp"] > min_time + 5]
        
        plt.figure(figsize=(10, 6))
        
        # Plot p95 Latency vs Requests per Second (RPS)
        plt.plot(df["Requests/s"], df["95%"], label="p95 Latency (Warm Cache)", color="green", linewidth=2, marker='o')
        
        plt.xlabel("Requests per Second (RPS)")
        plt.ylabel("Response Time (ms)")
        plt.title("RAG API Load Test: p95 Latency vs RPS (Warm Cache)")
        plt.grid(True)
        plt.legend()
        plt.savefig("load_test_chart.png")
        print("✅ Saved chart to load_test_chart.png")
        
    except FileNotFoundError:
        print("❌ Error: Could not find warm_run_stats_history.csv")

if __name__ == "__main__":
    plot_results()