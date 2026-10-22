from agents import (job_analyst, fit_scorer, resume_tailor,
                    cover_letter_writer, fact_checker, revise_resume,
                    revise_cover_letter, resume_to_markdown)


def run_pipeline(resume_text, job_text, log=print, max_revisions=2):
    name = resume_text.strip().splitlines()[0]

    log("🔍 Agent 1 · Job Analyst is reading the job...")
    analysis = job_analyst(job_text)

    log("📊 Agent 2 · Fit Scorer is comparing your resume...")
    report = fit_scorer(resume_text, analysis)

    log("📝 Agent 3 · Resume Tailor is rewriting your resume...")
    tailored = resume_tailor(resume_text, analysis, report)

    log("✉️ Agent 4 · Cover Letter Writer is drafting...")
    letter = cover_letter_writer(resume_text, analysis, report)

    review = None
    for round_no in range(1, max_revisions + 2):
        log(f"✅ Agent 5 · Fact-Checker, round {round_no}...")
        review = fact_checker(resume_text, analysis,
                              resume_to_markdown(tailored, name), letter.letter)
        if review.approved and (round_no > 1 or not review.issues):
            log("   No blocking issues. Approved!")
            break
        for i in review.issues:
            log(f"   ⚠️ [{i.document} · {i.issue_type}] {i.problem}")
        if round_no > max_revisions:
            log("   Revision limit reached. Remaining issues are listed above.")
            break
        resume_issues = [i for i in review.issues if i.document == "resume"]
        letter_issues = [i for i in review.issues if i.document == "cover_letter"]
        if resume_issues:
            log("   ↩️ Sending resume back to the Tailor...")
            tailored = revise_resume(resume_text, analysis, tailored, resume_issues)
        if letter_issues:
            log("   ↩️ Sending cover letter back to the Writer...")
            letter = revise_cover_letter(resume_text, analysis, letter, letter_issues)

    return {"name": name, "analysis": analysis, "report": report,
            "tailored": tailored, "letter": letter, "review": review}


if __name__ == "__main__":
    resume_text = open("resume.txt", encoding="utf-8").read()
    job_text = open("jobs/job1.txt", encoding="utf-8").read()

    result = run_pipeline(resume_text, job_text)

    md = resume_to_markdown(result["tailored"], result["name"])
    with open("output/tailored_resume.md", "w", encoding="utf-8") as f:
        f.write(md)
    letter = result["letter"]
    with open("output/cover_letter.txt", "w", encoding="utf-8") as f:
        f.write(f"Subject: {letter.subject_line}\n\n{letter.letter}")

    print(f"\nFit score: {result['report'].fit_score}/100")
    print("Saved: output/tailored_resume.md and output/cover_letter.txt")
