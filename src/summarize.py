# src/summarize.py
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import os
import logging

load_dotenv()

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

logging.basicConfig(filename='logs/arxiv_gpt.log', level=logging.INFO)

def summarize_paper(paper, summary_format="bullet"):
    """
    Summarize the abstract of a paper in the specified format (bullet or paragraph).
    """
    try:
        # Initialize Groq LLM
        llm = ChatGroq(
            model="llama-3.1-70b-versatile",
            api_key=os.getenv("GROQ_API_KEY")
        )

        # Define prompt based on format
        if summary_format == "bullet":
            prompt_template = PromptTemplate(
                input_variables=["abstract"],
                template="Summarize the following abstract in 3 concise bullet points:\n\n{abstract}"
            )
        else:  # paragraph
            prompt_template = PromptTemplate(
                input_variables=["abstract"],
                template="Summarize the following abstract in a single concise paragraph (50-100 words):\n\n{abstract}"
            )

        # Create chain
        chain = prompt_template | llm

        # Run summarization
        summary = chain.invoke({"abstract": paper['summary']}).content
        return summary
    except Exception as e:
        logging.error(f"Summarization error for paper {paper['title']}: {e}")
        return paper['summary']  # Return raw abstract on error