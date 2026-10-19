# src/app.py
import streamlit as st
from agent import run_agent
import os
import re

st.set_page_config(page_title="arXiv-GPT", layout="wide")

# Custom CSS for better formatting
st.markdown("""
    <style>
    .paper-container {
        border: 1px solid #e0e0e0;
        border-radius: 5px;
        padding: 15px;
        margin-bottom: 10px;
        background-color: #f9f9f9;
    }
    .paper-title {
        font-size: 1.2em;
        font-weight: bold;
        color: #1f77b4;
    }
    .paper-details {
        font-size: 0.9em;
        color: #333;
    }
    .paper-summary {
        font-size: 0.95em;
        margin-top: 10px;
        color: #333;
    }
    .paper-divider {
        border-top: 1px solid #e0e0e0;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📚 arXiv-GPT: Research Assistant")

# Input section
with st.form(key="research_form"):
    query = st.text_input("Enter a research topic:", "self-driving cars")
    max_results = st.slider("Number of papers to fetch:", 1, 10, 3)
    generate_pdf = st.checkbox("Generate PDF report", value=True)
    submit_button = st.form_submit_button("Fetch & Summarize")

if submit_button:
    if query:
        with st.spinner("Processing your request..."):
            result, pdf_filename = run_agent(query, max_results, generate_pdf_report=generate_pdf)
            if result.startswith("Unable to process"):
                st.error(result)
            else:
                # Parse the result into individual papers
                papers = result.split("-" * 50)
                for i, paper_text in enumerate(papers, 1):
                    if not paper_text.strip():
                        continue
                    # Extract paper details using regex
                    title_match = re.search(r"Title: (.+?)\n", paper_text)
                    authors_match = re.search(r"Authors: (.+?)\n", paper_text)
                    published_match = re.search(r"Published: (.+?)\n", paper_text)
                    url_match = re.search(r"URL: (.+?)\n", paper_text)
                    summary_match = re.search(r"Summary:\n(.+)", paper_text, re.DOTALL)

                    title = title_match.group(1) if title_match else f"Paper {i}"
                    authors = authors_match.group(1) if authors_match else "Unknown"
                    published = published_match.group(1) if published_match else "Unknown"
                    url = url_match.group(1) if url_match else "#"
                    summary = summary_match.group(1).strip() if summary_match else "Summary unavailable."

                    # Display each paper in an expander
                    with st.expander(f"Paper {i}: {title}", expanded=(i == 1)):
                        st.markdown(
                            f"""
                            <div class="paper-container">
                                <div class="paper-title">{title}</div>
                                <div class="paper-details"><b>Authors:</b> {authors}</div>
                                <div class="paper-details"><b>Published:</b> {published}</div>
                                <div class="paper-details"><b>URL:</b> <a href="{url}" target="_blank">{url}</a></div>
                                <hr class="paper-divider">
                                <div class="paper-summary"><b>Summary:</b><br>{summary.replace('•', '<br>•')}</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                # PDF download button
                if generate_pdf and pdf_filename and os.path.exists(pdf_filename):
                    with open(pdf_filename, "rb") as f:
                        st.download_button(
                            label="Download PDF Report",
                            data=f,
                            file_name=os.path.basename(pdf_filename),
                            mime="application/pdf"
                        )
    else:
        st.warning("Please enter a query.")