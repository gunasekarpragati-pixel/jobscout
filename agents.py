from typing import Literal
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
import os
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    try:
        import streamlit as st
        api_key = st.secrets.get("OPENAI_API_KEY")
    except Exception:
        pass
client = OpenAI(api_key=api_key)
MODEL = "gpt-5.4-mini"


# ============ Agent 1: Job Analyst ============

class JobAnalysis(BaseModel):
    company: str
    role: str
    seniority: str
    must_have_skills: list[str]
    nice_to_have_skills: list[str]
    ats_keywords: list[str]
    key_responsibilities: list[str]
    hidden_expectations: list[str]


JOB_ANALYST_INSTRUCTIONS = """You are an expert recruiter and job analyst.
Read the job description and extract:
- company and role title (use "Unknown" if not stated)
- seniority level (e.g. Junior, Mid, Senior, Lead)
- must-have skills (clearly required)
- nice-to-have skills (preferred, a plus, bonus)
- ATS keywords: exact words and phrases an applicant tracking system
  would scan for
- key responsibilities, in short phrases
- hidden expectations: things implied but not stated
Be concise. Do not invent anything that is not in or clearly implied by the text."""


def job_analyst(job_text: str) -> JobAnalysis:
    response = client.responses.parse(
        model=MODEL,
        instructions=JOB_ANALYST_INSTRUCTIONS,
        input=job_text,
        text_format=JobAnalysis,
    )
    return response.output_parsed


# ============ Agent 2: Fit Scorer ============

class SkillMatch(BaseModel):
    skill: str
    evidence_from_resume: str


class Gap(BaseModel):
    skill: str
    severity: Literal["critical", "moderate", "minor"]
    how_to_address: str


class FitReport(BaseModel):
    fit_score: int
    score_reasoning: str
    matching_skills: list[SkillMatch]
    transferable_strengths: list[str]
    gaps: list[Gap]


FIT_SCORER_INSTRUCTIONS = """You are an honest, experienced hiring manager.
Compare the candidate's resume to the job analysis.

fit_score: 0 to 100. Must-have skills carry most of the weight.
score_reasoning: 2-3 sentences.

STRICT RULES:
1. matching_skills: only skills with DIRECT evidence in the resume.
   Give a short quote or close paraphrase as evidence.
2. If experience is only related or adjacent (not a direct match),
   put it in transferable_strengths, NOT in matching_skills.
3. A skill can appear in only ONE list. If there is any direct evidence,
   it is a match, never a gap.
4. Gap severity:
   - critical = a must-have skill with no evidence at all
   - moderate = a must-have skill with only partial or adjacent evidence
   - minor = any nice-to-have skill
   Nice-to-have skills must ALWAYS be "minor".
5. For each gap, suggest a realistic way to address it (a short course,
   a small project, or how to frame it honestly in an interview).
Never assume skills that are not in the resume."""


def fit_scorer(resume_text: str, analysis: JobAnalysis) -> FitReport:
    prompt = (
        "JOB ANALYSIS:\n" + analysis.model_dump_json(indent=2)
        + "\n\nCANDIDATE RESUME:\n" + resume_text
    )
    response = client.responses.parse(
        model=MODEL,
        instructions=FIT_SCORER_INSTRUCTIONS,
        input=prompt,
        text_format=FitReport,
    )
    return response.output_parsed


# ============ Agent 3: Resume Tailor ============

class Role(BaseModel):
    title: str
    organization: str
    dates: str
    bullets: list[str]


class TailoredResume(BaseModel):
    headline: str
    summary: str
    key_skills: list[str]
    experience: list[Role]
    projects: list[Role]
    education: list[str]
    tools: list[str]
    changes_made: list[str]


RESUME_TAILOR_INSTRUCTIONS = """You are an expert resume writer.
Rewrite the candidate's BASE RESUME so it is tailored to the job.

The BASE RESUME is the ONLY source of truth about the candidate.
The fit report is guidance on priorities; do not treat it as evidence.

YOU MAY:
- Rewrite the headline and summary to target this role
- Reorder skills, roles' bullets, and sections to put the most relevant first
- Rephrase bullets to be clearer and use the job's keywords, ONLY where
  the base resume genuinely supports them
- Shorten or drop bullets that are irrelevant to this job

YOU MUST NOT:
- Add any skill, tool, certification, domain or responsibility that is
  not in the base resume (e.g. if Postman, OAuth or Jira are not in the
  base resume, they must not appear)
- Change job titles, employers, dates, degrees, scores or numbers
- Exaggerate scope (e.g. "worked with" must not become "led")

In changes_made, list each meaningful change in one line, saying what
you changed and why (e.g. "Moved API project higher: job requires REST
API knowledge")."""


def resume_tailor(resume_text: str, analysis: JobAnalysis,
                  report: FitReport) -> TailoredResume:
    prompt = (
        "JOB ANALYSIS:\n" + analysis.model_dump_json(indent=2)
        + "\n\nFIT REPORT:\n" + report.model_dump_json(indent=2)
        + "\n\nBASE RESUME:\n" + resume_text
    )
    response = client.responses.parse(
        model=MODEL,
        instructions=RESUME_TAILOR_INSTRUCTIONS,
        input=prompt,
        text_format=TailoredResume,
    )
    return response.output_parsed


def resume_to_markdown(r: TailoredResume, name: str = "") -> str:
    lines = []
    if name:
        lines.append(f"# {name}")
    lines += [f"**{r.headline}**", "", "## Summary", r.summary, "",
              "## Key Skills", " | ".join(r.key_skills), "",
              "## Professional Experience"]
    for role in r.experience:
        lines.append(f"\n### {role.title}, {role.organization}  ({role.dates})")
        lines += [f"- {b}" for b in role.bullets]
    if r.projects:
        lines.append("\n## Projects")
        for p in r.projects:
            lines.append(f"\n### {p.title} | {p.organization}" + (f"  ({p.dates})" if p.dates else ""))
            lines += [f"- {b}" for b in p.bullets]
    lines.append("\n## Education")
    lines += [f"- {e}" for e in r.education]
    lines.append("\n## Tools")
    lines.append(", ".join(r.tools))
    return "\n".join(lines)


# ============ Agent 4: Cover Letter Writer ============

class CoverLetter(BaseModel):
    subject_line: str
    letter: str
    key_points_used: list[str]


COVER_LETTER_INSTRUCTIONS = """You are an expert cover letter writer.
Write a cover letter for this job using ONLY facts from the BASE RESUME.

Style:
- Under 250 words, warm, confident and specific; no cliches
  ("I am writing to express my interest", "team player", "passionate")
- Open with a strong, specific hook about the role or company
- Use 2-3 concrete achievements from the resume that match the
  job's most important requirements, with their real numbers
- If the candidate ran their own business or took a non-traditional
  path, frame it positively as ownership and client management;
  never apologize for it or call it a gap
- Do not mention missing skills. Optionally show eagerness to learn
  one key tool or domain from the job, in one short sentence
- End with a clear, polite call to action
- Sign off with the candidate's name from the resume

Never invent skills, tools, numbers, employers or experience.
In key_points_used, list the resume facts you relied on."""


def cover_letter_writer(resume_text: str, analysis: JobAnalysis,
                        report: FitReport) -> CoverLetter:
    prompt = (
        "JOB ANALYSIS:\n" + analysis.model_dump_json(indent=2)
        + "\n\nFIT REPORT:\n" + report.model_dump_json(indent=2)
        + "\n\nBASE RESUME:\n" + resume_text
    )
    response = client.responses.parse(
        model=MODEL,
        instructions=COVER_LETTER_INSTRUCTIONS,
        input=prompt,
        text_format=CoverLetter,
    )
    return response.output_parsed


# ============ Agent 5: Fact-Checker ============

class Issue(BaseModel):
    document: Literal["resume", "cover_letter"]
    issue_type: Literal["fabrication", "exaggeration", "changed_fact",
                        "missed_opportunity"]
    problem: str
    fix: str


class ReviewResult(BaseModel):
    approved: bool
    issues: list[Issue]


FACT_CHECKER_INSTRUCTIONS = """You are a strict fact-checker and senior recruiter.
Compare the TAILORED RESUME and COVER LETTER against the BASE RESUME
(the only source of truth) and the JOB ANALYSIS.

Flag these issue types:
- fabrication: any skill, tool, domain, employer, certification or
  responsibility that is not in the base resume
- exaggeration: inflated scope ("worked with" became "led"), adjacent
  experience presented as direct, or years of experience blended
  across unrelated roles
- changed_fact: any title, date, number, degree or score that differs
  from the base resume
- missed_opportunity: evidence that IS written in the base resume and
  matches a MUST-HAVE skill, but was left out (at most 2). NEVER suggest
  adding a skill or tool that is not in the base resume (e.g. if Postman
  is not in the base resume, never suggest it).

For each issue, say exactly what to change.
approved = true only if there are NO fabrication, exaggeration or
changed_fact issues.
Do not flag rewording that keeps the same meaning.
Anything stated ANYWHERE in the base resume (including the Projects
section) may appear anywhere in the tailored resume or cover letter;
that is NOT a fabrication. Do not flag formatting or layout.
Only flag real, meaningful problems. If unsure, do not flag it."""


def fact_checker(resume_text: str, analysis: JobAnalysis,
                 tailored_md: str, letter_text: str) -> ReviewResult:
    prompt = (
        "JOB ANALYSIS:\n" + analysis.model_dump_json(indent=2)
        + "\n\nBASE RESUME:\n" + resume_text
        + "\n\nTAILORED RESUME:\n" + tailored_md
        + "\n\nCOVER LETTER:\n" + letter_text
    )
    response = client.responses.parse(
        model=MODEL,
        instructions=FACT_CHECKER_INSTRUCTIONS,
        input=prompt,
        text_format=ReviewResult,
    )
    return response.output_parsed


# ============ Revision helpers (writers fix reviewer issues) ============

REVISION_NOTE = """

You are now REVISING your previous draft. Fix every issue the reviewer
listed, exactly as suggested, and keep everything else unchanged."""


def _issues_json(issues):
    return "[" + ",\n".join(i.model_dump_json() for i in issues) + "]"


def revise_resume(resume_text: str, analysis: JobAnalysis,
                  tailored: TailoredResume, issues: list) -> TailoredResume:
    prompt = (
        "JOB ANALYSIS:\n" + analysis.model_dump_json(indent=2)
        + "\n\nBASE RESUME:\n" + resume_text
        + "\n\nYOUR PREVIOUS DRAFT:\n" + tailored.model_dump_json(indent=2)
        + "\n\nREVIEWER ISSUES TO FIX:\n" + _issues_json(issues)
    )
    response = client.responses.parse(
        model=MODEL,
        instructions=RESUME_TAILOR_INSTRUCTIONS + REVISION_NOTE,
        input=prompt,
        text_format=TailoredResume,
    )
    return response.output_parsed


def revise_cover_letter(resume_text: str, analysis: JobAnalysis,
                        letter: CoverLetter, issues: list) -> CoverLetter:
    prompt = (
        "JOB ANALYSIS:\n" + analysis.model_dump_json(indent=2)
        + "\n\nBASE RESUME:\n" + resume_text
        + "\n\nYOUR PREVIOUS DRAFT:\n" + letter.model_dump_json(indent=2)
        + "\n\nREVIEWER ISSUES TO FIX:\n" + _issues_json(issues)
    )
    response = client.responses.parse(
        model=MODEL,
        instructions=COVER_LETTER_INSTRUCTIONS + REVISION_NOTE,
        input=prompt,
        text_format=CoverLetter,
    )
    return response.output_parsed
