import time
import numpy as np
from app.agent.research_agent import ResearchAgent

TEST_QUERIES = [
    "attention mechanisms in transformers",
    "diffusion models for image generation",
    "graph neural networks",
    "federated learning privacy",
    "reinforcement learning robotics"
]

def run_latency_test():
    latencies = []

    for q in TEST_QUERIES:
        start = time.time()
        ResearchAgent.run(q, max_results=3, generate_pdf=False)
        latency = time.time() - start
        latencies.append(latency)
        print(f"{q} → {latency:.2f}s")

    avg_latency = np.mean(latencies)
    p95_latency = np.percentile(latencies, 95)

    print("\n=== Latency Results ===")
    print(f"Average Latency: {avg_latency:.2f}s")
    print(f"P95 Latency: {p95_latency:.2f}s")

    return avg_latency, p95_latency