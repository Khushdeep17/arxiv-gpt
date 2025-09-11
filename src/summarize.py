# src/summarize.py
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import os
import logging
import json

load_dotenv()

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

logging.basicConfig(filename='logs/arxiv_gpt.log', level=logging.DEBUG)

def summarize_paper(paper, summary_format="bullet"):
    """
    Summarize the abstract of a paper in the specified format (bullet or paragraph).
    """
    try:
        # Check if abstract exists
        abstract = paper.get('summary', 'No abstract available.')
        if abstract is None or abstract == 'No abstract available.':
            logging.warning(f"No valid abstract for paper {paper['title']}")
            return abstract

        # Verify Groq API key
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            logging.error("GROQ_API_KEY not found in .env")
            return paper.get('raw_summary', abstract)

        # Initialize Groq LLM
        model_name = "llama-3.1-70b-versatile"
        try:
            llm = ChatGroq(
                model=model_name,
                api_key=api_key,
                temperature=0.0,
                max_tokens=200
            )
            logging.info(f"Initialized model {model_name} for summarization")
        except Exception as e:
            logging.warning(f"Failed to load {model_name}: {e}. Falling back to llama-3.1-8b-instant.")
            llm = ChatGroq(
                model="llama-3.1-8b-instant",
                api_key=api_key,
                temperature=0.0,
                max_tokens=200
            )
            model_name = "llama-3.1-8b-instant"

        # Define prompt based on format
        if summary_format == "bullet":
            prompt_template = PromptTemplate(
                input_variables=["abstract"],
                template=(
                    "Summarize the following abstract in exactly 3 concise bullet points. "
                    "Each bullet must start with a dash (-), be clear, distinct, and avoid repetition:\n\n{abstract}"
                )
            )
        else:  # paragraph
            prompt_template = PromptTemplate(
                input_variables=["abstract"],
                template=(
                    "Summarize the following abstract in a single concise paragraph of 50-100 words. "
                    "Capture key points, ensure coherence, and avoid repetition:\n\n{abstract}"
                )
            )

        # Create chain
        chain = prompt_template | llm

        # Run summarization with retry
        for attempt in range(3):  # Retry twice
            try:
                logging.debug(f"Attempt {attempt + 1} to summarize paper {paper['title']} with format {summary_format}")
                summary = chain.invoke({"abstract": abstract}).content.strip()
                logging.debug(f"Raw summary response: {summary[:100]}...")
                # Validate summary format
                if summary_format == "bullet":
                    lines = [line for line in summary.split('\n') if line.strip().startswith('-')]
                    if len(lines) != 3:
                        logging.warning(f"Bullet summary for {paper['title']} has {len(lines)} bullets, retrying")
                        continue
                elif summary_format == "paragraph":
                    word_count = len(summary.split())
                    if word_count < 50 or word_count > 100:
                        logging.warning(f"Paragraph summary for {paper['title']} has {word_count} words, retrying")
                        continue
                logging.info(f"Generated {summary_format} summary for paper {paper['title']}: {summary[:50]}...")
                return summary
            except Exception as e:
                logging.error(f"Summarization attempt {attempt + 1} failed for paper {paper['title']}: {e}")
                if attempt == 2:
                    logging.error(f"Final summarization failure for paper {paper['title']}")
                    return paper.get('raw_summary', abstract)
        return paper.get('raw_summary', abstract)  # Fallback after retries
    except Exception as e:
        logging.error(f"Summarization error for paper {paper['title']}: {e}")
        return paper.get('raw_summary', abstract)  # Fallback to raw abstract