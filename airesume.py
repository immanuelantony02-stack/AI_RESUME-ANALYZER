import streamlit as st
import PyPDF2
import json
from openai import OpenAI

# OPENAI CLIENT
client = OpenAI(
    api_key=st.secrets["OPENAI_API_KEY"]
)

# AI FUNCTION
def ask_ai(prompt):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    return response.choices[0].message.content


# PDF TEXT EXTRACTION
def extract_pdf(file):
    reader = PyPDF2.PdfReader(file)
    return ''.join(page.extract_text() or '' for page in reader.pages)


# PAGE TITLE
st.title("AI Resume ATS Scanner")


# TWO COLUMN LAYOUT
left, right = st.columns([1, 1])


# LEFT SIDE INPUTS
with left:

    st.subheader("Upload Resume")

    resume_file = st.file_uploader(
        "Upload PDF Resume",
        type=["pdf"]
    )

    job_role = st.text_input(
        "Target Job Role",
        placeholder="e.g. Data Scientist"
    )

    job_desc = st.text_area(
        "Paste Job Description (Optional)",
        height=150
    )

    scan_btn = st.button(
        "Scan Resume",
        use_container_width=True
    )


# RIGHT SIDE RESULTS
with right:

    if scan_btn:

        if not resume_file:
            st.error("Please upload a resume PDF")

        elif not job_role:
            st.error("Please enter target job role")

        else:

            with st.spinner("Scanning Resume..."):

                # EXTRACT PDF TEXT
                resume_text = extract_pdf(resume_file)

                # AI PROMPT
                prompt = f"""
                You are an ATS and HR expert.

                Analyze this resume for the role: {job_role}

                Job Description:
                {job_desc}

                Resume Text:
                {resume_text[:3000]}

                Return ONLY valid JSON with keys:
                ats_score,
                overall_rating,
                strengths,
                weaknesses,
                missing_keywords,
                improvement_tips,
                summary

                Rules:
                - ats_score should be between 0 and 100
                - strengths should contain 3 points
                - weaknesses should contain 3 points
                - missing_keywords should contain 5 items
                - improvement_tips should contain 3 points
                - summary should contain 2 sentences
                """

                try:

                    # AI RESPONSE
                    raw = ask_ai(prompt).strip()

                    # REMOVE MARKDOWN JSON BLOCKS
                    if "```" in raw:
                        raw = raw.split("```")[1]

                        if raw.startswith("json"):
                            raw = raw[4:]

                    # CONVERT TO PYTHON DICTIONARY
                    result = json.loads(raw)

                    score = result["ats_score"]

                    # SCORE COLOR
                    if score >= 75:
                        color = "green"

                    elif score >= 50:
                        color = "orange"

                    else:
                        color = "red"

                    # ATS SCORE CARD
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
                            ">
                                {score}
                            </h1>

                            <p style="font-size:20px;">
                                ATS Score / 100
                            </p>

                            <p>
                                {result['overall_rating']}
                            </p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    # SUMMARY
                    st.info(result["summary"])

                    # RESULT COLUMNS
                    c1, c2 = st.columns(2)

                    with c1:

                        st.success("Strengths")

                        for s in result["strengths"]:
                            st.write("- " + s)

                        st.error("Weaknesses")

                        for w in result["weaknesses"]:
                            st.write("- " + w)

                    with c2:

                        st.warning("Missing Keywords")

                        for k in result["missing_keywords"]:
                            st.write("- " + k)

                        st.info("Improvement Tips")

                        for t in result["improvement_tips"]:
                            st.write("- " + t)

                except Exception as e:
                    st.error(f"Error: {e}")