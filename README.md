# 🎯 JobScout v2: Multi-Agent Job-Hunt Assistant

A team of five AI agents that analyzes a job, scores a candidate's fit,
tailors their resume, writes a cover letter, and fact-checks everything
against the original resume, so nothing is invented.

🔗 **Live demo:** https://jobscout-pragati.streamlit.app

## The agent team
| Agent | Role |
|---|---|
| 🔍 Job Analyst | Extracts must-have skills, ATS keywords and hidden expectations |
| 📊 Fit Scorer | Scores fit (0-100) with evidence quoted from the resume |
| 📝 Resume Tailor | Rewrites the resume for the job using only real facts |
| ✉️ Cover Letter Writer | Drafts a tailored, specific cover letter |
| ✅ Fact-Checker | Flags fabrications, exaggerations and changed facts |

An **orchestrator** runs the agents in sequence and manages a
**review-and-revise loop**: the Fact-Checker sends flagged drafts back to
the writers, up to two rounds, until there are no blocking issues.

## Key design decisions
- **Structured outputs:** each agent returns a typed schema (Pydantic),
  so agents pass reliable data to each other
- **Single source of truth:** the base resume is the only allowed source
  of facts; the fit report is guidance, not evidence
- **Calibrated reviewer:** the Fact-Checker can only suggest using facts
  already in the resume, which prevents it from causing fabrications
- **Code-based checks** alongside AI review (e.g. keyword checks for
  skills the candidate does not have)

## Tech stack
Python · OpenAI API (structured outputs, tool calling) · Pydantic · Streamlit

## Run locally
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo "OPENAI_API_KEY=your-key" > .env
streamlit run app.py
```

## Files
- `agents.py`: the five agents and their instructions
- `orchestrator.py`: runs the team and the revision loop
- `app.py`: Streamlit web interface
- `job_agent.py`: v1, a single tool-calling agent (terminal version)
