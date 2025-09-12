# src/app.py
import streamlit as st
import os
from datetime import datetime
from agent import run_agent
import logging

# Setup logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(filename='logs/arxiv_gpt.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Streamlit configuration
st.set_page_config(page_title="arXiv-GPT", layout="wide")

# Custom CSS for styling
st.markdown("""
    <style>
    .main { background-color: #f9fafb; padding: 20px; }
    .stButton>button { background-color: #1e40af; color: white; border-radius: 5px; padding: 10px 20px; }
    .stButton>button:hover { background-color: #1e3a8a; }
    .stTextInput>div>input { border-radius: 5px; padding: 10px; }
    .paper { background-color: #ffffff; padding: 15px; margin-bottom: 15px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .paper h3 { color: #1e40af; margin-bottom: 10px; }
    .paper p { color: #374151; margin: 5px 0; }
    .summary { color: #4b5563; }
    .sidebar .stSelectbox { margin-bottom: 15px; }
    .sidebar h3 { color: #1e40af; }
    .history-item { cursor: pointer; color: #374151; padding: 5px; }
    .history-item:hover { background-color: #e5e7eb; }
    </style>
""", unsafe_allow_html=True)

# Initialize session state for history
if 'history' not in st.session_state:
    st.session_state.history = []

# Sidebar
with st.sidebar:
    st.header("Search History")
    if st.session_state.history:
        for idx, entry in enumerate(st.session_state.history):
            if st.button(f"{entry['query']} ({entry['timestamp']})", key=f"history_{idx}", help="Click to revisit query"):
                st.session_state.current_query = entry['query']
                st.session_state.current_sources = entry['sources']
                st.session_state.current_result = entry['result']
                st.session_state.current_pdf = entry['pdf_filename']
    else:
        st.write("No search history yet.")

# Main content
st.title("arXiv-GPT: Research Paper Search")
st.markdown("Search for research papers on arXiv and Semantic Scholar, summarized in bullet points.")

query = st.text_input("Enter your search query:", value=st.session_state.get('current_query', "self-driving cars"))
sources = st.multiselect("Select sources:", ["arXiv", "Semantic Scholar"], default=st.session_state.get('current_sources', ["arXiv", "Semantic Scholar"]))
max_results = st.slider("Number of results:", 1, 10, value=3)

if st.button("Search"):
    with st.spinner("Fetching and summarizing papers..."):
        logging.info(f"Starting search for query: {query}, sources: {sources}")
        result, pdf_filename = run_agent(query, max_results=max_results, generate_pdf_report=True, sources=sources)
        st.session_state.current_query = query
        st.session_state.current_sources = sources
        st.session_state.current_result = result
        st.session_state.current_pdf = pdf_filename

        # Add to history
        st.session_state.history.append({
            'query': query,
            'sources': sources,
            'result': result,
            'pdf_filename': pdf_filename,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

# Display results
if 'current_result' in st.session_state and st.session_state.current_result:
    if "No papers found" in st.session_state.current_result or "Unable to process" in st.session_state.current_result:
        st.error(st.session_state.current_result)
    else:
        papers = st.session_state.current_result.split("-" * 50)
        for paper in papers:
            if paper.strip():
                st.markdown(f"<div class='paper'>{paper.replace('\n', '<br>').replace('• ', '• ')}</div>", unsafe_allow_html=True)
    
    if st.session_state.current_pdf:
        with open(st.session_state.current_pdf, "rb") as file:
            st.download_button("Download PDF", file, file_name=os.path.basename(st.session_state.current_pdf))

if not st.session_state.get('current_result'):
    st.info("Enter a query and select sources to start searching.")