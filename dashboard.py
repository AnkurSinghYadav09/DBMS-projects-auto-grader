import streamlit as st
import sys
import time
from pathlib import Path
from datetime import datetime
import traceback

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Page configuration MUST come before any other Streamlit commands
st.set_page_config(
    page_title="AAG 🔥",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Wrap everything in try-except for better error reporting
try:
    # Now import other modules and libraries
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go

    from src.config import Config
    from src.sheet_processor import SheetProcessor
    from src.google_api import GoogleAPIHandler
    
except Exception as e:
    st.error(f"❌ **Initialization Error**")
    st.error(f"Error: {str(e)}")
    st.code(traceback.format_exc())
    st.stop()

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
        font-size: 1.2rem;
        padding: 0.75rem;
        border-radius: 0.5rem;
    }
    .stButton>button:hover {
        background-color: #145a8c;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">🔥 AAG 🔥</div>', unsafe_allow_html=True)
st.markdown('<div style="text-align: center; font-style: italic; font-size: 1.2rem; color: #666; margin-top: -1.5rem; margin-bottom: 2rem;">DBMS Auto Grader</div>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    st.subheader("📋 Google Sheet")
    sheet_id_display = f"{Config.SPREADSHEET_ID[:10]}...{Config.SPREADSHEET_ID[-10:]}"
    st.code(sheet_id_display, language=None)
    st.caption(f"Sheet Name: **{Config.SHEET_NAME}**")
    
    st.markdown("---")
    
    st.subheader("🤖 AI Provider")
    provider_emoji = {"gemini": "🔮", "openai": "🧠", "deepseek": "🔍"}
    st.write(f"{provider_emoji.get(Config.AI_PROVIDER, '🤖')} **{Config.AI_PROVIDER.upper()}**")
    
    if Config.AI_PROVIDER == "gemini":
        st.caption(f"Model: {Config.GEMINI_MODEL}")
    else:
        st.caption(f"Model: {Config.OPENAI_MODEL}")
    
    st.markdown("---")
    
    st.subheader("⚡ Processing Settings")
    st.write(f"🔄 Max Workers: **{Config.MAX_WORKERS}**")
    st.write(f"🔁 Retry Attempts: **{Config.RETRY_ATTEMPTS}**")
    st.write(f"📦 Batch Size: **{Config.BATCH_SIZE}**")
    
    st.markdown("---")
    
    st.subheader("🔗 Quick Links")
    sheet_url = f"https://docs.google.com/spreadsheets/d/{Config.SPREADSHEET_ID}"
    st.markdown(f"[📄 Open Google Sheet]({sheet_url})")

# Main content area
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.subheader("🎯 Evaluation Control Center")
    
    # Status indicator
    status_placeholder = st.empty()
    progress_bar = st.progress(0)
    log_area = st.empty()
    
    # Run button
    if st.button("🚀 Start Evaluation", use_container_width=True):
        try:
            # Validate configuration
            with status_placeholder:
                st.info("🔍 Validating configuration...")
            Config.validate()
            time.sleep(0.5)
            
            # Initialize processor
            with status_placeholder:
                st.info("🔧 Initializing evaluation system...")
            progress_bar.progress(10)
            processor = SheetProcessor()
            time.sleep(0.5)
            
            # Get document count
            with status_placeholder:
                st.info("📊 Reading Google Sheet...")
            progress_bar.progress(20)
            
            google_api = GoogleAPIHandler()
            range_name = f"{Config.DOC_LINK_COLUMN}2:{Config.STUDENT_NAME_COLUMN}"
            rows = google_api.read_sheet_rows(range_name)
            doc_count = len(rows)
            
            with status_placeholder:
                st.info(f"📚 Found **{doc_count}** documents to evaluate")
            progress_bar.progress(30)
            time.sleep(1)
            
            # Start evaluation
            with status_placeholder:
                st.warning(f"⚡ Evaluating {doc_count} documents... (This may take a few minutes)")
            progress_bar.progress(40)
            
            # Run evaluation (this is the actual processing)
            start_time = time.time()
            processor.process_all_documents()
            end_time = time.time()
            
            elapsed_time = round(end_time - start_time, 2)
            avg_time = round(elapsed_time / doc_count, 2) if doc_count > 0 else 0
            
            progress_bar.progress(100)
            
            # Success message
            with status_placeholder:
                st.success(f"✅ Evaluation Complete!")
            
            # Show statistics
            st.balloons()
            
            st.markdown("---")
            st.subheader("📈 Evaluation Statistics")
            
            stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
            
            with stat_col1:
                st.metric("📚 Total Documents", doc_count)
            
            with stat_col2:
                st.metric("⏱️ Total Time", f"{elapsed_time}s")
            
            with stat_col3:
                st.metric("⚡ Avg Time/Doc", f"{avg_time}s")
            
            with stat_col4:
                st.metric("✅ Status", "Success")
            
            # Link to results
            st.markdown("---")
            st.info(f"📊 **View Results:** [Open Google Sheet]({sheet_url})")
            
        except Exception as e:
            with status_placeholder:
                st.error(f"❌ Error: {str(e)}")
            progress_bar.progress(0)
            st.exception(e)

# Footer section
st.markdown("---")

# Instructions
with st.expander("📖 How to Use This Dashboard"):
    st.markdown("""
    ### Step-by-Step Instructions:
    
    1. **Prepare Your Google Sheet:**
       - Column A: Google Doc links (student submissions)
       - Column B: Student names
       - Columns C & D: Will be auto-filled with scores and feedback
    
    2. **Click "Start Evaluation":**
       - The system will read all document links from your sheet
       - Each document will be evaluated using AI
       - Scores and feedback will be written back to the sheet
    
    3. **Monitor Progress:**
       - Watch the progress bar and status messages
       - Evaluation typically takes 2-5 seconds per document
    
    4. **View Results:**
       - Click "Open Google Sheet" to see the results
       - Scores will appear in Column C
       - Detailed feedback will appear in Column D
    
    ### Scoring Breakdown:
    - **SQL Implementation (25 pts):** Table design, data quality, indexes, code quality
    - **ER Model (20 pts):** Diagram completeness, relationships, normalization
    - **Query Design (25 pts):** Query complexity, correctness, optimization
    - **Documentation (20 pts):** Design rationale, explanations, justifications
    - **Originality (10 pts):** Human authenticity, creative problem-solving
    
    ### Tips:
    - Process in batches if you have 100+ documents
    - Check logs folder for detailed processing information
    - Rerun evaluation will overwrite existing scores
    """)

# System Information
with st.expander("ℹ️ System Information"):
    st.markdown(f"""
    - **Base Directory:** `{Config.BASE_DIR}`
    - **Credentials:** `{Config.SERVICE_ACCOUNT_FILE}`
    - **Logs Directory:** `{Config.LOGS_DIR}`
    - **Rubrics Directory:** `{Config.RUBRICS_DIR}`
    - **Document Link Column:** `{Config.DOC_LINK_COLUMN}`
    - **Score Column:** `{Config.SCORE_COLUMN}`
    - **Feedback Column:** `{Config.FEEDBACK_COLUMN}`
    """)

# Credits
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>"
    "🔥 AAG - Ankur Assignment Grader | Built with ❤️ using Streamlit"
    "</div>",
    unsafe_allow_html=True
)
