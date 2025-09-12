# src/summarize.py
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os

load_dotenv()

def summarize_paper(paper, model="llama-3.1-8b-instant"):
    """
    Summarize a paper's abstract into 3 bullet points using Groq API.
    """
    try:
        llm = ChatGroq(
            model=model,
            api_key=os.getenv("GROQ_API_KEY")
        )

        template = """
        Summarize the following research paper abstract in 3 concise bullet points:
        Title: {title}
        Abstract: {summary}
        """
        prompt = ChatPromptTemplate.from_template(template)
        response = llm.invoke(prompt.format_messages(
            title=paper["title"],
            summary=paper["summary"]
        ))
        return response.content
    except Exception as e:
        print(f"Error summarizing paper: {e}")
        return "Summary unavailable."
