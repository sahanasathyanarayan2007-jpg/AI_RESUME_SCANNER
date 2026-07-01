import streamlit as st
import PyPDF2
import json
import os
from groq import Groq
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Groq setup
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def ask_ai(prompt):
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",  # ✅ updated working model
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content


# -----------------------------
# PDF TEXT EXTRACTION
# -----------------------------
def extract_pdf(file):
    reader = PyPDF2.PdfReader(file)
    return "".join(page.extract_text() or "" for page in reader.pages)


# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="AI Resume Scanner", page_icon="📄", layout="wide")
st.title("📄 AI Resume Scanner (ATS Checker)")


# -----------------------------
# UI LAYOUT
# -----------------------------
left, right = st.columns([1, 1])

with left:
    st.subheader("Upload Resume")

    resume_file = st.file_uploader("Upload PDF Resume", type=["pdf"])

    job_role = st.text_input("Target Job Role", placeholder="e.g. Data Scientist")

    job_desc = st.text_area("Job Description (optional)", height=150)

    scan_btn = st.button("Scan Resume", use_container_width=True)


# -----------------------------
# AI PROCESSING
# -----------------------------
with right:

    if scan_btn:

        if not resume_file:
            st.error("Please upload a resume PDF")
        elif not job_role:
            st.error("Please enter target job role")
        else:

            with st.spinner("Analyzing Resume..."):

                resume_text = extract_pdf(resume_file)

                prompt = f"""
You are an ATS (Applicant Tracking System) expert and HR specialist.

Analyze this resume for the role: {job_role}

Resume Text:
{resume_text[:3000]}

Return ONLY valid JSON with this format:
{{
  "ats_score": 0-100,
  "overall_rating": "string",
  "strengths": ["", "", ""],
  "weaknesses": ["", "", ""],
  "missing_keywords": ["", "", "", "", ""],
  "improvement_tips": ["", "", ""],
  "summary": "2 sentence summary"
}}
"""

                raw = ask_ai(prompt).strip()

                # Clean markdown if present
                if "```" in raw:
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]

                result = json.loads(raw)


                # -----------------------------
                # ATS SCORE DISPLAY
                # -----------------------------
                score = result["ats_score"]

                if score >= 75:
                    color = "green"
                elif score >= 50:
                    color = "orange"
                else:
                    color = "red"

                st.markdown(
                    f"""
                    <div style="text-align:center;
                                padding:25px;
                                border-radius:12px;
                                border:2px solid {color};
                                background:#111;">
                        <h1 style="color:{color}; font-size:60px;">
                            {score}
                        </h1>
                        <h3>ATS Score / 100</h3>
                        <p>{result['overall_rating']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                st.info(result["summary"])


                # -----------------------------
                # DETAILS SECTION
                # -----------------------------
                c1, c2 = st.columns(2)

                with c1:
                    st.success("Strengths")
                    for s in result["strengths"]:
                        st.write("•", s)

                    st.error("Weaknesses")
                    for w in result["weaknesses"]:
                        st.write("•", w)

                with c2:
                    st.warning("Missing Keywords")
                    for k in result["missing_keywords"]:
                        st.write("•", k)

                    st.info("Improvement Tips")
                    for t in result["improvement_tips"]:
                        st.write("•", t)