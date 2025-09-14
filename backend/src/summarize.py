import json
import os
import logging
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate

load_dotenv()

def summarize_paper(paper, model="llama-3.1-8b-instant"):
    """
    Summarize a paper's abstract into 3 bullet points using Groq API.
    Returns structured dict: {"summary": ["point1","point2","point3"], "raw": original_abstract}
    """
    try:
        abstract = paper.get("summary", "").strip()
        if not abstract:
            abstract = f"No abstract available. Paper title: {paper.get('title', 'Unknown')}"

        llm = ChatGroq(
            model=model,
            api_key=os.getenv("GROQ_API_KEY"),
            temperature=0.0,
            max_tokens=600  # allow longer summaries
        )

        template = """
        Summarize the following paper abstract in exactly 3 concise bullet points.
        Respond ONLY in valid JSON with this format:

        {
          "summary": [
            "point 1",
            "point 2",
            "point 3"
          ]
        }

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

        # Try parsing JSON
        try:
            parsed = json.loads(response)
            # Ensure 3 bullets, fallback if necessary
            if "summary" not in parsed or not isinstance(parsed["summary"], list) or len(parsed["summary"]) != 3:
                logging.warning(f"Summary for {paper.get('title')} incomplete, using fallback lines")
                lines = [line.strip("- ").strip() for line in abstract.split("\n") if line.strip()]
                parsed["summary"] = lines[:3] if lines else ["No summary available."]
            return {"summary": parsed["summary"], "raw": abstract}
        except json.JSONDecodeError:
            logging.warning(f"Failed to parse JSON for {paper.get('title')}, got raw: {response}")
            lines = [line.strip("- ").strip() for line in abstract.split("\n") if line.strip()]
            return {"summary": lines[:3] if lines else ["No summary available."], "raw": abstract}

    except Exception as e:
        logging.error(f"Error summarizing paper {paper.get('title', 'unknown')}: {e}")
        return {"summary": ["No summary available."], "raw": abstract}
