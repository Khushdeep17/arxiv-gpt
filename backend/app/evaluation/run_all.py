from app.evaluation.benchmark import run_latency_test
from app.evaluation.completeness import run_completeness_test
from app.evaluation.compression import run_compression_test

def main():
    print("Running arXiv-GPT Evaluation...\n")

    avg_latency, p95_latency = run_latency_test()
    completeness, schema_valid = run_completeness_test()
    compression = run_compression_test()

    print("\n=== FINAL RESULTS ===")
    print(f"Avg Latency: {avg_latency:.2f}s")
    print(f"P95 Latency: {p95_latency:.2f}s")
    print(f"Summary Completeness: {completeness:.1f}%")
    print(f"Schema Validity: {schema_valid}")
    print(f"Compression Ratio: {compression:.2f}x")

if __name__ == "__main__":
    main()