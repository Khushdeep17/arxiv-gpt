import streamlit as st
from agent import run_agent
import os
import re

st.set_page_config(page_title="arXiv-GPT", layout="wide")

# Custom CSS for enhanced formatting
st.markdown("""
    <style>
    /* Main container */
    .paper-container {
        border: 1px solid #d1d5db;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 15px;
        background-color: #ffffff;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s;
    }
    .paper-container:hover {
        transform: translateY(-2px);
    }
    /* Title */
    .paper-title {
        font-size: 1.3em;
        font-weight: 600;
        color: #1e40af;
        margin-bottom: 10px;
    }
    /* Details */
    .paper-details {
        font-size: 0.95em;
        color: #374151;
        margin-bottom: 8px;
        line-height: 1.5;
    }
    .paper-details a {
        color: #2563eb;
        text-decoration: none;
    }
    .paper-details a:hover {
        text-decoration: underline;
    }
    /* Summary */
    .paper-summary {
        font-size: 0.95em;
        color: #4b5563;
        margin-top: 12px;
        line-height: 1.6;
    }
    /* Divider */
    .paper-divider {
        border-top: 1px solid #e5e7eb;
        margin: 15px 0;
    }
    /* Sidebar */
    .sidebar .sidebar-content {
        background-color: #f8fafc;
        padding: 15px;
        border-radius: 8px;
    }
    .sidebar .stButton>button {
        width: 100%;
        text-align: left;
        color: #1e40af;
        background-color: #e2e8f0;
        border: none;
        border-radius: 6px;
        padding: 10px;
        margin-bottom: 5px;
    }
    .sidebar .stButton>button:hover {
        background-color: #bfdbfe;
    }
    /* Form */
    .stForm {
        background-color: #f8fafc;
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #e5e7eb;
    }
    .stButton>button {
        background-color: #1e40af;
        color: white;
        border-radius: 6px;
        padding: 10px 20px;
    }
    .stButton>button:hover {
        background-color: #1e3a8a;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📚 arXiv-GPT: Research Assistant")

# Initialize session state for history
if "history" not in st.session_state:
    st.session_state.history = []

# Sidebar for query history
with st.sidebar:
    st.subheader("Query History", help="Click to view past searches")
    if st.session_state.history:
        for i, item in enumerate(st.session_state.history):
            if st.button(f"Query {i+1}: {item['query']} ({', '.join(item['sources'])})", key=f"history_{i}"):
                st.session_state.selected_history = i
    else:
        st.markdown("<p style='color: #6b7280;'>No queries yet.</p>", unsafe_allow_html=True)

# Input form
with st.form(key="research_form"):
    st.markdown("<h3 style='color: #1e40af; margin-bottom: 15px;'>Search Papers</h3>", unsafe_allow_html=True)
    query = st.text_input("Enter a research topic:", "self-driving cars", help="e.g., machine learning, quantum computing")
    max_results = st.slider("Number of papers to fetch:", 1, 10, 3, help="Adjust the number of results")
    sources = st.multiselect("Select sources:", ["arXiv", "Semantic Scholar"], default=["arXiv", "Semantic Scholar"], help="Choose one or both sources")
    summary_format = st.selectbox("Summary format:", ["Bullet Points", "Paragraph"], help="Choose how summaries are displayed")
    generate_pdf = st.checkbox("Generate PDF report", value=True, help="Download results as a PDF")
    submit_button = st.form_submit_button("Fetch & Summarize")

# Handle form submission
if submit_button and query and sources:
    with st.spinner("Processing your request..."):
        result, pdf_filename = run_agent(
            query,
            max_results,
            generate_pdf_report=generate_pdf,
            sources=[s.lower().replace(" ", "_") for s in sources],
            summary_format=summary_format.lower().replace(" ", "_")
        )
        if result.startswith("Unable to process"):
            st.error(result)
        else:
            # Save to history
            st.session_state.history.append({
                "query": query,
                "sources": sources,
                "result": result,
                "pdf_filename": pdf_filename,
                "summary_format": summary_format
            })

            # Display results
            st.subheader("Results", help="Expand to view paper details")
            papers = result.split("-" * 50)
            for i, paper_text in enumerate(papers, 1):
                if not paper_text.strip():
                    continue
                title_match = re.search(r"Title: (.+?)\n", paper_text)
                authors_match = re.search(r"Authors: (.+?)\n", paper_text)
                published_match = re.search(r"Published: (.+?)\n", paper_text)
                url_match = re.search(r"URL: (.+?)\n", paper_text)
                source_match = re.search(r"Source: (.+?)\n", paper_text)
                summary_match = re.search(r"Summary:\n(.+)", paper_text, re.DOTALL)

                title = title_match.group(1) if title_match else f"Paper {i}"
                authors = authors_match.group(1) if authors_match else "Unknown"
                published = published_match.group(1) if published_match else "Unknown"
                url = url_match.group(1) if url_match else "#"
                source = source_match.group(1) if source_match else "Unknown"
                summary = summary_match.group(1).strip() if summary_match else "Summary unavailable."

                with st.expander(f"Paper {i}: {title}", expanded=(i == 1)):
                    st.markdown(
                        f"""
                        <div class="paper-container">
                            <div class="paper-title">{title}</div>
                            <div class="paper-details"><b>Authors:</b> {authors}</div>
                            <div class="paper-details"><b>Published:</b> {published}</div>
                            <div class="paper-details"><b>URL:</b> <a href="{url}" target="_blank">{url}</a></div>
                            <div class="paper-details"><b>Source:</b> {source}</div>
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
                        mime="application/pdf",
                        help="Download the results as a PDF"
                    )

# Display selected history item
if "selected_history" in st.session_state:
    item = st.session_state.history[st.session_state.selected_history]
    st.subheader(f"History: {item['query']} ({', '.join(item['sources'])})", help="Viewing past search")
    papers = item["result"].split("-" * 50)
    for i, paper_text in enumerate(papers, 1):
        if not paper_text.strip():
            continue
        title_match = re.search(r"Title: (.+?)\n", paper_text)
        authors_match = re.search(r"Authors: (.+?)\n", paper_text)
        published_match = re.search(r"Published: (.+?)\n", paper_text)
        url_match = re.search(r"URL: (.+?)\n", paper_text)
        source_match = re.search(r"Source: (.+?)\n", paper_text)
        summary_match = re.search(r"Summary:\n(.+)", paper_text, re.DOTALL)

        title = title_match.group(1) if title_match else f"Paper {i}"
        authors = authors_match.group(1) if authors_match else "Unknown"
        published = published_match.group(1) if published_match else "Unknown"
        url = url_match.group(1) if url_match else "#"
        source = source_match.group(1) if source_match else "Unknown"
        summary = summary_match.group(1).strip() if summary_match else "Summary unavailable."

        with st.expander(f"Paper {i}: {title}", expanded=(i == 1)):
            st.markdown(
                f"""
                <div class="paper-container">
                    <div class="paper-title">{title}</div>
                    <div class="paper-details"><b>Authors:</b> {authors}</div>
                    <div class="paper-details"><b>Published:</b> {published}</div>
                    <div class="paper-details"><b>URL:</b> <a href="{url}" target="_blank">{url}</a></div>
                    <div class="paper-details"><b>Source:</b> {source}</div>
                    <hr class="paper-divider">
                    <div class="paper-summary"><b>Summary:</b><br>{summary.replace('•', '<br>•')}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

    if item["pdf_filename"] and os.path.exists(item["pdf_filename"]):
        with open(item["pdf_filename"], "rb") as f:
            st.download_button(
                label="Download PDF Report (History)",
                data=f,
                file_name=os.path.basename(item["pdf_filename"]),
                mime="application/pdf",
                help="Download the past search as a PDF"
            )