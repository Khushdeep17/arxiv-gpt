# backend/src/test_summarize.py
from summarize import summarize_paper

if __name__ == "__main__":
    paper = {
        "title": "Transformers are All You Need",
        "summary": (
            "Transformers are a novel neural network architecture based on self-attention mechanisms "
            "that achieve state-of-the-art results on sequence transduction tasks, "
            "without using recurrence or convolution."
        )
    }

    result = summarize_paper(paper)
    print("\n=== FINAL SUMMARY RESULT ===")
    print(result)
