# 🎯 JobScout: AI Job-Hunt Agent

An AI agent that reads a resume and a job description, scores the fit,
identifies skill gaps, and writes a tailored cover letter.

## How it works
The agent uses the OpenAI API with **tool calling**. Instead of answering
in one shot, it runs in a loop and decides which tools to use:

- `read_resume`: reads the candidate's resume
- `read_job`: reads the job description
- `save_application`: saves the fit score, skills, gaps and cover letter

The instructions forbid inventing experience, so cover letters only use
what's really in the resume.

## Tech stack
Python · OpenAI API (tool calling) · Streamlit

## Run it locally
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo "OPENAI_API_KEY=your-key" > .env
streamlit run app.py
```
