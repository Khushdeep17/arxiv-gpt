from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os
import logging
import re

load_dotenv()

def summarize_paper(paper, model="llama-3.1-8b-instant"):
    """
    Summarize a paper's abstract into 3 concise bullet points using Groq API.
    """
    try:
        abstract = paper.get("summary", "No abstract available.")
        if abstract == "No abstract available.":
            return abstract

        llm = ChatGroq(
            model=model,
            api_key=os.getenv("GROQ_API_KEY"),
            temperature=0.2,  # Slightly increased for better creativity
            max_tokens=200  # Increased to allow complete summaries
        )

        template = """
        Summarize the following research paper abstract in exactly 3 concise bullet points, each starting with a dash (-). Each bullet point should be a complete sentence and no longer than 30 words. Ensure the summary captures the key findings or contributions of the paper.
        Title: {title}
        Abstract: {summary}
        """
        prompt = ChatPromptTemplate.from_template(template)
        response = llm.invoke(prompt.format_messages(
            title=paper["title"],
            summary=abstract
        )).content.strip()

        # Clean up response
        response = re.sub(r'Here are (3|three) concise bullet points.*?:', '', response, flags=re.IGNORECASE)
        lines = [line.strip() for line in response.split('\n') if line.strip().startswith('-')]
        
        # Validate and adjust bullet points
        if len(lines) != 3:
            logging.warning(f"Summary for {paper['title']} has {len(lines)} bullet points, attempting to rephrase")
            # Fallback: Rephrase the abstract manually if possible
            fallback_prompt = """
            Rephrase the following abstract into exactly 3 concise bullet points, each starting with a dash (-), max 30 words each:
            {summary}
            """
            fallback_response = llm.invoke(fallback_prompt.format(summary=abstract)).content.strip()
            fallback_lines = [line.strip() for line in fallback_response.split('\n') if line.strip().startswith('-')]
            if len(fallback_lines) == 3:
                return '\n'.join(fallback_lines)
            logging.error(f"Failed to generate 3 bullet points for {paper['title']}")
            return abstract  # Fallback to raw abstract
        
        return '\n'.join(lines)
    except Exception as e:
        logging.error(f"Error summarizing paper {paper['title']}: {e}")
        return f"Summary unavailable due to error: {str(e)}"