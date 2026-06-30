"""CV Optimizer — ATS keyword analysis and STAR-method resume rewriting."""

import io
import os

import streamlit as st
from crewai import Agent, Crew, LLM, Process, Task
from dotenv import load_dotenv
from pypdf import PdfReader

load_dotenv()

GEMINI_MODEL = "gemini/gemini-2.5-flash"


def extract_text_from_pdf(uploaded_file) -> str:
    """Extract plain text from an uploaded PDF using pypdf."""
    reader = PdfReader(io.BytesIO(uploaded_file.read()))
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text.strip())
    if not pages:
        raise ValueError("No text could be extracted from the PDF.")
    return "\n\n".join(pages)


def build_gemini_llm() -> LLM:
    """Configure the Gemini 2.5 Flash LLM using the API key from .env."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY not found. Add it to your .env file "
            "(see README.md for setup instructions)."
        )
    return LLM(
        model=GEMINI_MODEL,
        api_key=api_key,
        temperature=0.4,
    )


def create_crew(cv_text: str, job_description: str) -> Crew:
    """Build the two-agent crew: ATS Specialist → Resume Writer."""
    llm = build_gemini_llm()

    ats_specialist = Agent(
        role="ATS Specialist",
        goal=(
            "Compare a candidate's CV against a job description and identify "
            "keywords, skills, and qualifications that are missing or underrepresented."
        ),
        backstory=(
            "You are an expert Applicant Tracking System (ATS) analyst with deep "
            "knowledge of how recruiters and automated screening tools evaluate resumes. "
            "You excel at extracting must-have and nice-to-have keywords from job "
            "descriptions and spotting gaps in a candidate's CV."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
    )

    resume_writer = Agent(
        role="Resume Writer",
        goal=(
            "Rewrite a CV's Experience and Skills sections using the STAR method "
            "(Situation, Task, Action, Result) while naturally incorporating "
            "missing ATS keywords identified by the ATS Specialist."
        ),
        backstory=(
            "You are a professional resume writer who specializes in turning "
            "generic bullet points into compelling, metrics-driven achievements. "
            "You use the STAR method to structure every experience bullet and "
            "weave in relevant keywords without sounding forced or keyword-stuffed."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
    )

    ats_task = Task(
        description=(
            "Analyze the following CV against the job description.\n\n"
            "Identify:\n"
            "1. Missing hard skills and technical keywords\n"
            "2. Missing soft skills and competencies\n"
            "3. Missing tools, certifications, or qualifications\n"
            "4. Keywords present in the job description but absent or weak in the CV\n\n"
            "Provide a structured report with:\n"
            "- A prioritized list of missing keywords (grouped by category)\n"
            "- Brief notes on why each keyword matters for this role\n"
            "- Which CV sections should be updated to address the gaps\n\n"
            "--- CV ---\n{cv_text}\n\n"
            "--- JOB DESCRIPTION ---\n{job_description}"
        ),
        expected_output=(
            "A structured ATS gap analysis report containing:\n"
            "1. Missing Keywords (grouped: Technical Skills, Soft Skills, Tools/Certifications)\n"
            "2. Priority ranking (High / Medium / Low) for each missing keyword\n"
            "3. Recommended sections to update (Experience, Skills, or both)\n"
            "4. A concise summary of the top 5 most critical gaps"
        ),
        agent=ats_specialist,
    )

    rewrite_task = Task(
        description=(
            "Using the ATS Specialist's gap analysis and the original CV, rewrite "
            "ONLY the Experience and Skills sections of the CV.\n\n"
            "Requirements:\n"
            "- Use the STAR method for every experience bullet "
            "(Situation, Task, Action, Result)\n"
            "- Naturally incorporate the missing keywords from the ATS analysis\n"
            "- Preserve factual accuracy — do not invent employers, dates, or credentials\n"
            "- Keep the candidate's voice professional and concise\n"
            "- Format output with clear headings: ## Experience and ## Skills\n\n"
            "Original CV for reference:\n{cv_text}\n\n"
            "Job description for context:\n{job_description}"
        ),
        expected_output=(
            "Rewritten CV sections in markdown format:\n\n"
            "## Experience\n"
            "(Each role with STAR-method bullet points incorporating missing keywords)\n\n"
            "## Skills\n"
            "(Updated skills list organized by category, including previously missing keywords)\n\n"
            "Plus a brief note listing which keywords were added and where."
        ),
        agent=resume_writer,
        context=[ats_task],
    )

    return Crew(
        agents=[ats_specialist, resume_writer],
        tasks=[ats_task, rewrite_task],
        process=Process.sequential,
        verbose=True,
    )


def run_optimization(cv_text: str, job_description: str) -> tuple[str, str]:
    """Execute the crew and return (ATS analysis, rewritten sections)."""
    crew = create_crew(cv_text, job_description)
    crew.kickoff(
        inputs={
            "cv_text": cv_text,
            "job_description": job_description,
        }
    )
    ats_output = str(crew.tasks[0].output)
    rewrite_output = str(crew.tasks[1].output)
    return ats_output, rewrite_output


def main() -> None:
    st.set_page_config(
        page_title="CV Optimizer",
        page_icon="📄",
        layout="wide",
    )

    st.title("CV Optimizer")
    st.markdown(
        "Upload your CV (PDF) and paste a job description. Two AI agents will "
        "analyze ATS keyword gaps and rewrite your **Experience** and **Skills** "
        "sections using the **STAR method**."
    )

    col_upload, col_job = st.columns(2)

    with col_upload:
        st.subheader("1. Upload CV (PDF)")
        uploaded_file = st.file_uploader(
            "Choose your CV file",
            type=["pdf"],
            help="Your CV will be parsed locally; only extracted text is sent to the AI.",
        )

    with col_job:
        st.subheader("2. Paste Job Description")
        job_description = st.text_area(
            "Job description",
            height=300,
            placeholder="Paste the full job description here…",
        )

    if st.button("Optimize CV", type="primary", use_container_width=True):
        if not uploaded_file:
            st.error("Please upload a CV PDF.")
            return
        if not job_description.strip():
            st.error("Please paste a job description.")
            return

        try:
            with st.spinner("Extracting text from PDF…"):
                cv_text = extract_text_from_pdf(uploaded_file)

            with st.expander("Extracted CV text", expanded=False):
                st.text(cv_text)

            with st.spinner("Running ATS analysis and resume rewrite (this may take a minute)…"):
                ats_output, rewrite_output = run_optimization(
                    cv_text, job_description.strip()
                )

            st.success("Optimization complete!")

            st.subheader("ATS Keyword Gap Analysis")
            st.markdown(ats_output)

            st.subheader("Rewritten Experience & Skills (STAR Method)")
            st.markdown(rewrite_output)

            combined = (
                "# ATS Keyword Gap Analysis\n\n"
                f"{ats_output}\n\n"
                "---\n\n"
                "# Rewritten Experience & Skills (STAR Method)\n\n"
                f"{rewrite_output}"
            )
            st.download_button(
                label="Download results as Markdown",
                data=combined,
                file_name="optimized_cv_sections.md",
                mime="text/markdown",
            )

        except ValueError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"An error occurred: {exc}")


if __name__ == "__main__":
    main()
