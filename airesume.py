import streamlit as st
import PyPDF2
import openai
import json
import os
from dotenv import load_dotenv

load_dotenv()

# -----------------------------
# AI Setup
# -----------------------------
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -----------------------------
# Function: Ask AI
# -----------------------------
def ask_ai(prompt):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content


# -----------------------------
# Function: Extract Text From PDF
# -----------------------------
def extract_pdf(file):
    reader = PyPDF2.PdfReader(file)

    # Extract text from all pages
    all_text = ''.join(
        page.extract_text() or ''
        for page in reader.pages
    )

    return all_text


# -----------------------------
# Streamlit Page Setup
# -----------------------------
st.set_page_config(
    page_title="AI Resume Scanner",
    page_icon="📄",
    layout="wide"
)

st.title("📄 AI Resume ATS Scanner")
st.write("Upload your resume and get ATS analysis using AI")


# -----------------------------
# Create Two Columns
# -----------------------------
left, right = st.columns([1, 1])


# ==================================================
# LEFT COLUMN
# ==================================================
with left:

    st.subheader("Upload Resume")

    # PDF Upload
    resume_file = st.file_uploader(
        "Upload PDF Resume",
        type=["pdf"]
    )

    # Job Role Input
    job_role = st.text_input(
        "Target Job Role",
        placeholder="e.g. Data Scientist"
    )

    # Job Description
    job_desc = st.text_area(
        "Paste Job Description (Optional)",
        height=150
    )

    # Scan Button
    scan_btn = st.button(
        "Scan Resume",
        use_container_width=True
    )


# ==================================================
# RIGHT COLUMN
# ==================================================
with right:

    if scan_btn:

        # Validation
        if not resume_file:
            st.error("Please upload a PDF resume!")

        elif not job_role:
            st.error("Please enter target job role!")

        else:

            with st.spinner("Scanning Resume..."):

                # -----------------------------------
                # Step 1: Extract Resume Text
                # -----------------------------------
                resume_text = extract_pdf(resume_file)

                # -----------------------------------
                # Step 2: Build AI Prompt
                # -----------------------------------
                prompt = f"""
                You are an ATS and HR expert.

                Analyze this resume for the role: {job_role}

                Job Description:
                {job_desc}

                Resume Text:
                {resume_text[:3000]}

                Return ONLY valid JSON with these keys:

                {{
                    "ats_score": number,
                    "overall_rating": "text",
                    "strengths": ["point1", "point2", "point3"],
                    "weaknesses": ["point1", "point2", "point3"],
                    "missing_keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
                    "improvement_tips": ["tip1", "tip2", "tip3"],
                    "summary": "2 sentence summary"
                }}
                """

                # -----------------------------------
                # Step 3: Call AI
                # -----------------------------------
                raw = ask_ai(prompt).strip()

                # -----------------------------------
                # Step 4: Clean AI Response
                # -----------------------------------
                if "```" in raw:

                    raw = raw.split("```")[1]

                    if raw.startswith("json"):
                        raw = raw[4:]

                # -----------------------------------
                # Step 5: Convert JSON String
                # -----------------------------------
                result = json.loads(raw)

                # -----------------------------------
                # Step 6: Display ATS Score Card
                # -----------------------------------
                score = result["ats_score"]

                if score >= 75:
                    color = "green"

                elif score >= 50:
                    color = "orange"

                else:
                    color = "red"

                st.markdown(
                    f"""
                    <div style="
                        text-align:center;
                        padding:20px;
                        background:#1a1a2e;
                        border-radius:12px;
                        border:2px solid {color};
                    ">

                        <h1 style="
                            color:{color};
                            font-size:64px;
                            margin-bottom:0;
                        ">
                            {score}
                        </h1>

                        <p style="font-size:20px;">
                            ATS Score / 100
                        </p>

                        <p style="font-size:18px;">
                            {result["overall_rating"]}
                        </p>

                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # -----------------------------------
                # Step 7: Show Summary
                # -----------------------------------
                st.info(result["summary"])

                # -----------------------------------
                # Step 8: Show Results
                # -----------------------------------
                c1, c2 = st.columns(2)

                # LEFT SIDE RESULTS
                with c1:

                    st.success("Strengths")

                    for s in result["strengths"]:
                        st.write("• " + s)

                    st.error("Weaknesses")

                    for w in result["weaknesses"]:
                        st.write("• " + w)

                # RIGHT SIDE RESULTS
                with c2:

                    st.warning("Missing Keywords")

                    for k in result["missing_keywords"]:
                        st.write("• " + k)

                    st.info("Improvement Tips")

                    for t in result["improvement_tips"]:
                        st.write("• " + t)
