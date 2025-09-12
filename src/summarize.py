# src/summarize.py
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os
import logging

load_dotenv()

def summarize_paper(paper, model="llama-3.1-8b-instant"):
    """
    Summarize a paper's abstract into 3 bullet points using Groq API.
    """
    try:
        abstract = paper.get("summary", "No abstract available.")
        if abstract == "No abstract available.":
            logging.info(f"No abstract for paper: {paper['title']}")
            return abstract

        llm = ChatGroq(
            model=model,
            api_key=os.getenv("GROQ_API_KEY"),
            temperature=0.0,
            max_tokens=200
        )

        template = """
        Summarize the following research paper abstract in exactly 3 concise bullet points, each starting with a dash (-):
        Title: {title}
        Abstract: {summary}
        """
        prompt = ChatPromptTemplate.from_template(template)
        response = llm.invoke(prompt.format_messages(
            title=paper["title"],
            summary=abstract
        )).content.strip()

        # Clean up response
        lines = [line.strip() for line in response.split('\n') if line.strip().startswith('-')]
        if len(lines) != 3:
            logging.warning(f"Summary for {paper['title']} has {len(lines)} bullet points, returning raw abstract")
            return abstract
        return '\n'.join(lines)
    except Exception as e:
        logging.error(f"Error summarizing paper {paper['title']}: {e}")
        return "No abstract available."