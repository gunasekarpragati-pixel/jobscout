import os
import streamlit as st
from orchestrator import run_pipeline
from agents import resume_to_markdown

st.set_page_config(page_title="JobScout", page_icon="🎯", layout="wide")
st.title("🎯 JobScout v2: Multi-Agent Job-Hunt Assistant")
st.caption("A team of five AI agents analyzes the job, scores your fit, "
           "tailors your resume, writes a cover letter, and fact-checks "
           "everything against your original resume.")

with st.expander("How the agent team works"):
    st.markdown("""
1. **🔍 Job Analyst**: extracts must-have skills, keywords and hidden expectations
2. **📊 Fit Scorer**: scores your fit, with evidence from your resume
3. **📝 Resume Tailor**: rewrites your resume for this job, using only real facts
4. **✉️ Cover Letter Writer**: drafts a tailored cover letter
5. **✅ Fact-Checker**: flags fabrications or exaggerations and sends drafts back for revision
""")

st.info("Privacy: text you paste is sent to OpenAI for processing and is not stored by this app.")

default_resume = ""
if os.path.exists("resume.txt"):
    default_resume = open("resume.txt", encoding="utf-8").read()

col1, col2 = st.columns(2)
resume = col1.text_area("Your resume", default_resume, height=300)
job = col2.text_area("Job description", height=300,
                     placeholder="Paste the job posting here")

if st.button("🚀 Run the agent team", type="primary",
             disabled=not (resume.strip() and job.strip())):
    with st.status("The agent team is working...", expanded=True) as status:
        st.session_state.result = run_pipeline(resume, job, log=st.write)
        status.update(label="Done!", state="complete", expanded=False)

if "result" in st.session_state:
    r = st.session_state.result
    a, rep, review = r["analysis"], r["report"], r["review"]

    st.divider()
    st.subheader(f"{a.role} at {a.company}")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["📊 Fit", "📝 Tailored resume", "✉️ Cover letter",
         "🔍 Job analysis", "✅ Fact-check"])

    with tab1:
        st.metric("Fit score", f"{rep.fit_score}/100")
        st.write(rep.score_reasoning)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### ✅ Matching skills")
            for m in rep.matching_skills:
                st.markdown(f"- **{m.skill}**  \n  _{m.evidence_from_resume}_")
            st.markdown("#### 🔁 Transferable strengths")
            for t in rep.transferable_strengths:
                st.markdown(f"- {t}")
        with c2:
            st.markdown("#### ⚠️ Gaps")
            icons = {"critical": "🔴", "moderate": "🟠", "minor": "🟡"}
            for g in sorted(rep.gaps, key=lambda g: ["critical", "moderate", "minor"].index(g.severity)):
                st.markdown(f"- {icons[g.severity]} **{g.skill}** ({g.severity})  \n  {g.how_to_address}")

    with tab2:
        md = resume_to_markdown(r["tailored"], r["name"])
        st.download_button("⬇️ Download resume (.md)", md, file_name="tailored_resume.md")
        with st.expander("What the Tailor changed, and why"):
            for c in r["tailored"].changes_made:
                st.markdown(f"- {c}")
        st.markdown(md)

    with tab3:
        letter = r["letter"]
        full = f"Subject: {letter.subject_line}\n\n{letter.letter}"
        edited = st.text_area("Edit before sending", full, height=400)
        st.download_button("⬇️ Download cover letter", edited, file_name="cover_letter.txt")

    with tab4:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Must-have skills")
            st.markdown("\n".join(f"- {s}" for s in a.must_have_skills))
            st.markdown("#### Nice-to-have skills")
            st.markdown("\n".join(f"- {s}" for s in a.nice_to_have_skills))
        with c2:
            st.markdown("#### Hidden expectations")
            st.markdown("\n".join(f"- {s}" for s in a.hidden_expectations))
            st.markdown("#### ATS keywords")
            st.write(", ".join(a.ats_keywords))

    with tab5:
        if review and review.approved:
            st.success("Approved: no fabrications, exaggerations or changed facts found.")
        else:
            st.warning("Some issues remain after the revision limit. Review them before sending.")
        if review and review.issues:
            for i in review.issues:
                st.markdown(f"- **[{i.document} · {i.issue_type}]** {i.problem}  \n  _Fix:_ {i.fix}")
