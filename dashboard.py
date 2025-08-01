import os
import sys
import tempfile
import warnings
import streamlit as st

# Suppress Pydantic field deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module='pydantic.fields')

# Add root/src to sys.path for importing fact_checker
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from crew_engine import get_url_crew, crew_from_topic

# Page config
st.set_page_config(page_title="Verifact AI · Fact Verification", layout="wide", page_icon="🧠")

# Sidebar branding
with st.sidebar:
    st.markdown("## 🔍 Verifact AI")
    st.markdown("### Autonomous AI Fact-Checking")
    st.markdown("---")
    st.markdown("Use Verifact to verify factual claims, URLs or uploaded documents using CrewAI agents.")
    st.markdown("Powered by [CrewAI](https://github.com/joaomdmoura/crewai) 🚀")

# Page title and intro
st.markdown("<h1 style='text-align:center;'>🧠 Verifact: Autonomous Fact-Checker</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:gray;'>Enter a claim, URL, or upload a file to verify facts using intelligent agents.</p>", unsafe_allow_html=True)

# Input options
input_tabs = st.tabs(["🗣 Claim", "🌐 URL", "📄 Upload Document"])

uploaded_file = None
claim = ""
url = ""
text = ""

# Tab 1: Claim
with input_tabs[0]:
    st.markdown("### 🗣 Enter a Factual Claim")
    claim = st.text_area("Type the claim you'd like to verify:", height=100)

# Tab 2: URL
with input_tabs[1]:
    st.markdown("### 🌐 Enter a Web URL")
    url = st.text_input("Paste the URL you want to fact-check:")

# Tab 3: Upload file
with input_tabs[2]:
    st.markdown("### 📄 Upload a Document")
    uploaded_file = st.file_uploader("Supported formats: PDF, DOCX, TXT", type=["pdf", "docx", "txt"])

# Run Verifact
st.markdown("---")
st.markdown("### 🚀 Launch Fact-Check")
if st.button("✅ Run Fact Check", use_container_width=True):
    if not uploaded_file and not claim and not url:
        st.error("⚠ Please enter a claim, a URL, or upload a document.")
        st.stop()

    with st.spinner("🔍 Running CrewAI agents..."):
        try:
            # File upload logic
            if uploaded_file:
                from pathlib import Path
                suffix = Path(uploaded_file.name).suffix.lower()

                if suffix == ".pdf":
                    import fitz
                    pdf = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                    text = "\n".join([page.get_text() for page in pdf])

                elif suffix == ".docx":
                    import docx
                    doc = docx.Document(uploaded_file)
                    text = "\n".join([p.text for p in doc.paragraphs])

                elif suffix == ".txt":
                    raw = uploaded_file.read()
                    for enc in ["utf-8", "utf-16", "latin-1", "cp1252"]:
                        try:
                            text = raw.decode(enc)
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        st.error("❌ Could not decode file. Try saving as UTF-8.")
                        st.stop()
                else:
                    st.error("❌ Unsupported file format.")
                    st.stop()

                crew = crew_from_topic(text)
                result = crew.kickoff(inputs={"topic": text})

            # Claim or URL input logic
            else:
                crew = get_url_crew(claim=claim, url=url)
                result = crew.kickoff(inputs={"claim": claim or "", "url": url or ""})

        except Exception as e:
            st.error(f"❌ Error running CrewAI: {e}")
            st.stop()

    # Format & display result
    result = str(result)
    st.success("✅ Fact-check completed!")

    st.markdown("### 🧾 Verdict")
    verdict_line = next((line for line in result.lower().splitlines() if "verdict:" in line), "")

    if "true" in verdict_line:
        st.success("🟢 The claim appears to be *TRUE*.")
    elif "false" in verdict_line:
        st.error("🔴 The claim appears to be *FALSE*.")
    elif "misleading" in verdict_line:
        st.warning("🟠 The claim appears to be *MISLEADING*.")
    else:
        st.info("⚪ No clear verdict detected.")

    # Full output
    st.markdown("### 📄 Full Report")
    st.code(result, language="markdown")

    # Download button
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as f:
        f.write(result)
        temp_path = f.name

    with open(temp_path, "rb") as f:
        st.download_button(
            label="📥 Download Report",
            data=f,
            file_name="verifact_report.txt",
            mime="text/plain"
        )

    # Restart
    st.markdown("---")
    if st.button("🔁 Start New Check", use_container_width=True):
        st.session_state.clear()
        st.rerun()