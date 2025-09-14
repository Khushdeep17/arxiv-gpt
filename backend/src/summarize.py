import json
import os
import logging
import re
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate

load_dotenv()

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/summarize.log"),
        logging.StreamHandler()
    ]
)

def summarize_paper(paper, model="llama-3.1-8b-instant"):
    """
    Summarize a paper's abstract into 3 bullet points using Groq API.
    Returns structured dict: {"summary": ["point1", "point2", "point3"], "raw": original_abstract}
    """
    try:
        abstract = paper.get("summary", "").strip()
        if not abstract:
            abstract = f"No abstract available. Paper title: {paper.get('title', 'Unknown')}"
            logging.info(f"No abstract for {paper.get('title', 'Unknown')}, returning default")
            return {
                "summary": [
                    "No summary available.",
                    "Please check the paper for details.",
                    "Contact support if issue persists."
                ],
                "raw": abstract
            }

        llm = ChatGroq(
            model=model,
            api_key=os.getenv("GROQ_API_KEY"),
            temperature=0.2,
            max_tokens=200
        )

        template = """
        Summarize the following research paper abstract in exactly 3 concise bullet points, each starting with a dash (-). Each bullet point must be a complete sentence, max 30 words. Ensure the summary captures key findings or contributions.

        Title: {title}
        Abstract: {summary}
        """
        prompt = ChatPromptTemplate.from_template(template)
        response = llm.invoke(
            prompt.format_messages(
                title=paper.get("title", "No title"),
                summary=abstract
            )
        ).content.strip()

        # Log raw response for debugging
        logging.debug(f"Raw LLM response for {paper.get('title', 'Unknown')}: {repr(response)}")

        # Try parsing as JSON first
        try:
            parsed = json.loads(response)
            if "summary" in parsed and isinstance(parsed["summary"], list) and len(parsed["summary"]) == 3:
                logging.debug(f"JSON parsed successfully for {paper.get('title', 'Unknown')}")
                return {"summary": parsed["summary"], "raw": abstract}
        except json.JSONDecodeError:
            logging.warning(f"JSON parse failed for {paper.get('title', 'Unknown')}, attempting text parsing")

        # Parse as text (like Streamlit)
        # Remove introductory text
        response = re.sub(r'Here are (3|three) bullet points.*?:', '', response, flags=re.IGNORECASE)
        response = re.sub(r'.*Unfortunately,.*provided:\n*', '', response, flags=re.IGNORECASE)
        # Extract lines starting with - or *
        lines = [line.strip() for line in response.split('\n') if line.strip().startswith(('-', '*'))]
        # Clean bullet points (remove - or * prefix)
        cleaned_lines = [re.sub(r'^[-*]\s*', '', line).strip() for line in lines]

        if len(cleaned_lines) >= 3:
            logging.debug(f"Text parsed successfully for {paper.get('title', 'Unknown')}: {cleaned_lines[:3]}")
            return {"summary": cleaned_lines[:3], "raw": abstract}

        # Fallback prompt if text parsing fails
        logging.warning(f"Text parsing yielded {len(cleaned_lines)} bullet points for {paper.get('title', 'Unknown')}, attempting fallback")
        fallback_template = """
        Summarize the following abstract into exactly 3 concise bullet points, each starting with a dash (-), max 30 words each:
        {summary}
        """
        fallback_prompt = ChatPromptTemplate.from_template(fallback_template)
        fallback_response = llm.invoke(fallback_prompt.format_messages(summary=abstract)).content.strip()
        logging.debug(f"Fallback response for {paper.get('title', 'Unknown')}: {repr(fallback_response)}")

        # Parse fallback response
        fallback_lines = [line.strip() for line in fallback_response.split("\n") if line.strip().startswith(('-', '*'))]
        cleaned_fallback_lines = [re.sub(r'^[-*]\s*', '', line).strip() for line in fallback_lines]

        if len(cleaned_fallback_lines) >= 3:
            logging.debug(f"Fallback parsed successfully for {paper.get('title', 'Unknown')}: {cleaned_fallback_lines[:3]}")
            return {"summary": cleaned_fallback_lines[:3], "raw": abstract}

        # Final fallback
        logging.error(f"Fallback failed for {paper.get('title', 'Unknown')}: {len(cleaned_fallback_lines)} bullet points")
        return {
            "summary": [
                "No summary available.",
                "Please check the paper for details.",
                "Contact support if issue persists."
            ],
            "raw": abstract
        }

    except Exception as e:
        logging.error(f"Error summarizing paper {paper.get('title', 'unknown')}: {str(e)}")
        return {
            "summary": [
                f"Summary unavailable due to error: {str(e)}",
                "Please try again later.",
                "Contact support if issue persists."
            ],
            "raw": abstract
        }