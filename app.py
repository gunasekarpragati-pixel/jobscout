import json, os
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()
MODEL = "gpt-5.4-mini"

st.set_page_config(page_title="JobScout", page_icon="🎯", layout="wide")
st.title("🎯 JobScout: AI Job-Hunt Agent")
st.caption("Paste a resume and a job description. The agent scores the fit, "
           "finds gaps, and writes a tailored cover letter.")

default_resume = open("resume.txt", encoding="utf-8").read() if os.path.exists("resume.txt") else ""
col1, col2 = st.columns(2)
resume = col1.text_area("Your resume", default_resume, height=350)
job = col2.text_area("Job description", height=350, placeholder="Paste the job posting here")

result = {}

def read_resume():
    return resume

def read_job():
    return job

def save_application(company, role, fit_score, matching_skills, gaps, cover_letter):
    result.update(company=company, role=role, fit_score=fit_score,
                  matching_skills=matching_skills, gaps=gaps, cover_letter=cover_letter)
    return "Saved."

available = {"read_resume": read_resume, "read_job": read_job,
             "save_application": save_application}

S = {"type": "string"}
tools = [
    {"type": "function", "name": "read_resume", "description": "Read the candidate's resume.",
     "parameters": {"type": "object", "properties": {}}},
    {"type": "function", "name": "read_job", "description": "Read the job description.",
     "parameters": {"type": "object", "properties": {}}},
    {"type": "function", "name": "save_application",
     "description": "Save the fit analysis and cover letter.",
     "parameters": {"type": "object",
        "properties": {"company": S, "role": S, "fit_score": {"type": "integer"},
                       "matching_skills": S, "gaps": S, "cover_letter": S},
        "required": ["company", "role", "fit_score", "matching_skills", "gaps", "cover_letter"]}},
]

INSTRUCTIONS = """You are a job-hunt assistant.
1. Read the resume and the job description using your tools.
2. Give a fit score from 0 to 100. Write matching skills and honest gaps
   as markdown bullet lists (one "- " item per line).
3. Write a tailored cover letter (under 250 words) using only real experience
   from the resume. Never invent experience, degrees or skills.
4. Save everything with save_application."""

if st.button("🔍 Analyze", type="primary", disabled=not (resume and job)):
    messages = [{"role": "user", "content": "Analyze this job for me."}]
    with st.status("Agent is working...", expanded=True) as status:
        while True:
            response = client.responses.create(
                model=MODEL, instructions=INSTRUCTIONS, input=messages, tools=tools)
            messages += response.output
            calls = [i for i in response.output if i.type == "function_call"]
            if not calls:
                break
            for call in calls:
                st.write(f"🛠️ Using tool: `{call.name}`")
                args = json.loads(call.arguments or "{}")
                output = available[call.name](**args)
                messages.append({"type": "function_call_output",
                                 "call_id": call.call_id, "output": str(output)})
        status.update(label="Done!", state="complete")

    if result:
        st.subheader(f"{result['role']} at {result['company']}")
        st.metric("Fit score", f"{result['fit_score']}/100")
        c1, c2 = st.columns(2)
        c1.markdown("#### ✅ Matching skills\n" + result["matching_skills"])
        c2.markdown("#### ⚠️ Gaps\n" + result["gaps"])
        st.markdown("#### ✉️ Cover letter")
        st.text_area("Edit before sending", result["cover_letter"], height=300)
        st.download_button("Download cover letter", result["cover_letter"],
                           file_name="cover_letter.txt")
