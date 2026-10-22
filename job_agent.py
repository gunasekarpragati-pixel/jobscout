import json, os, re
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()
MODEL = "gpt-5.4-mini"

# ---------- Tools (real Python functions) ----------
def read_resume():
    with open("resume.txt", encoding="utf-8") as f:
        return f.read()

def list_jobs():
    return json.dumps([f for f in os.listdir("jobs") if f.endswith(".txt")])

def read_job(filename):
    with open(os.path.join("jobs", filename), encoding="utf-8") as f:
        return f.read()

def fetch_job_url(url):
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        text = BeautifulSoup(r.text, "html.parser").get_text(" ", strip=True)
        return text[:8000] if text else "Page was empty."
    except Exception as e:
        return f"Could not fetch page: {e}"

def save_application(company, role, fit_score, matching_skills, gaps, cover_letter):
    safe = re.sub(r"[^A-Za-z0-9]+", "_", f"{company}_{role}").strip("_")
    path = os.path.join("output", f"{safe}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# {role} at {company}\n\n**Fit score:** {fit_score}/100\n\n")
        f.write(f"## Matching skills\n{matching_skills}\n\n## Gaps\n{gaps}\n\n")
        f.write(f"## Cover letter\n\n{cover_letter}\n")
    return f"Saved to {path}"

available = {
    "read_resume": read_resume, "list_jobs": list_jobs, "read_job": read_job,
    "fetch_job_url": fetch_job_url, "save_application": save_application,
}

# ---------- Tool descriptions for the model ----------
def fn(name, desc, props=None, required=None):
    return {"type": "function", "name": name, "description": desc,
            "parameters": {"type": "object", "properties": props or {},
                           "required": required or []}}

S = {"type": "string"}
tools = [
    fn("read_resume", "Read the candidate's resume."),
    fn("list_jobs", "List job description files in the jobs folder."),
    fn("read_job", "Read one job description file.", {"filename": S}, ["filename"]),
    fn("fetch_job_url", "Download the text of a job posting from a URL.", {"url": S}, ["url"]),
    fn("save_application", "Save the analysis and cover letter for one job.",
       {"company": S, "role": S, "fit_score": {"type": "integer"},
        "matching_skills": S, "gaps": S, "cover_letter": S},
       ["company", "role", "fit_score", "matching_skills", "gaps", "cover_letter"]),
]

INSTRUCTIONS = """You are a job-hunt assistant.
For each job the user asks about:
1. Read the resume and the job description using your tools.
2. Give a fit score from 0 to 100, list matching skills, and list honest gaps.
3. Write a tailored cover letter (under 250 words) using only real experience
   from the resume. Never invent experience, degrees or skills.
4. Save the result with save_application.
Then give the user a short summary."""

# ---------- The agent loop ----------
def run_agent(messages):
    while True:
        response = client.responses.create(
            model=MODEL, instructions=INSTRUCTIONS, input=messages, tools=tools)
        messages += response.output
        calls = [i for i in response.output if i.type == "function_call"]
        if not calls:
            return response.output_text
        for call in calls:
            args = json.loads(call.arguments or "{}")
            print(f"  [tool] {call.name}")
            try:
                result = available[call.name](**args)
            except Exception as e:
                result = f"Error: {e}"
            messages.append({"type": "function_call_output",
                             "call_id": call.call_id, "output": str(result)})

print("Job-Hunt Agent ready. Type 'exit' to quit.")
history = []
while True:
    q = input("\nYou: ")
    if q.lower() in ("exit", "quit"):
        break
    history.append({"role": "user", "content": q})
    print("\nAgent:", run_agent(history))
