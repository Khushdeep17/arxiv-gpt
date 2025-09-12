import streamlit as st
from agent import run_agent
import os
from datetime import datetime
import logging

st.set_page_config(page_title="arXiv-GPT", layout="wide")

st.markdown("""
    <style>
    /* Apply light mode styles */
    [data-theme="light"] .paper {
        background-color: #ffffff;
        color: #111827;
    }
    [data-theme="light"] .paper h3 {
        color: #1d4ed8;
    }
    [data-theme="light"] .paper p, 
    [data-theme="light"] .summary {
        color: #374151;
    }

    /* Apply dark mode styles */
    [data-theme="dark"] .paper {
        background-color: #1f2937; /* dark gray card */
        color: #f9fafb; /* light text */
        border: 1px solid #374151;
    }
    [data-theme="dark"] .paper h3 {
        color: #60a5fa; /* soft blue for headings */
    }
    [data-theme="dark"] .paper p, 
    [data-theme="dark"] .summary {
        color: #e5e7eb; /* light gray text */
    }

    /* General improvements */
    .paper {
        padding: 20px;
        margin-bottom: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    }
    .bullet { margin-left: 20px; }
    </style>
""", unsafe_allow_html=True)


# Initialize session state
if 'history' not in st.session_state:
    st.session_state.history = []

# Sidebar
with st.sidebar:
    st.header("Search History")
    if st.session_state.history:
        for idx, entry in enumerate(st.session_state.history):
            if st.button(f"{entry['query']} ({entry['timestamp']})", key=f"history_{idx}", use_container_width=True):
                st.session_state.current_query = entry['query']
                st.session_state.current_max_results = entry['max_results']
                st.session_state.current_result = entry['result']
                st.session_state.current_pdf = entry['pdf_filename']
            if entry['pdf_filename']:
                with open(entry['pdf_filename'], "rb") as file:
                    st.download_button("📄 PDF", file, file_name=os.path.basename(entry['pdf_filename']), key=f"pdf_{idx}")
    else:
        st.write("No search history yet.")

# Main content
st.title("📚 arXiv-GPT: Research Assistant")
st.markdown("Search for the latest **arXiv papers**, summarized in clean bullet points. (Max 10 results)")

col1, col2 = st.columns(2)
with col1:
    query = st.text_input("🔎 Search query:", value=st.session_state.get('current_query', "self-driving cars"))
with col2:
    max_results = st.slider("📊 Max results:", 1, 10, value=st.session_state.get('current_max_results', 3))

generate_pdf = st.checkbox("📄 Generate PDF", value=True)

if st.button("🚀 Search", type="primary"):
    with st.spinner("Fetching and summarizing latest papers..."):
        logging.info(f"GUI search: query={query}, max_results={max_results}")
        result, pdf_filename = run_agent(query, max_results, generate_pdf_report=generate_pdf)
        
        st.session_state.current_query = query
        st.session_state.current_max_results = max_results
        st.session_state.current_result = result
        st.session_state.current_pdf = pdf_filename

        # Add to history
        st.session_state.history.append({
            'query': query,
            'max_results': max_results,
            'result': result,
            'pdf_filename': pdf_filename,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

# Display results
if 'current_result' in st.session_state and st.session_state.current_result:
    if "No papers found" in st.session_state.current_result or "Unable to process" in st.session_state.current_result:
        st.error(st.session_state.current_result)
    else:
        st.subheader("📑 Latest Papers")
        papers = st.session_state.current_result.split("-" * 50)
        for paper in papers:
            if paper.strip():
                processed_paper = paper.replace("\\n", "<br>").replace("- ", "<br>&bull; ")
                st.markdown(f"<div class='paper'>{processed_paper}</div>", unsafe_allow_html=True)

    if generate_pdf and st.session_state.current_pdf:
        with open(st.session_state.current_pdf, "rb") as file:
            st.download_button("⬇️ Download PDF", file, file_name=os.path.basename(st.session_state.current_pdf))

if not st.session_state.get('current_result'):
    st.info("Enter a query to search the latest arXiv papers.")
