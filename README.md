# CV Optimizer

A Python app that uses **CrewAI** and **Google Gemini 2.5 Flash** to optimize your CV for a specific job posting.

Upload a CV PDF, paste a job description, and two AI agents work together:

1. **ATS Specialist** — Compares your CV against the job description and identifies missing keywords, skills, and qualifications.
2. **Resume Writer** — Rewrites your **Experience** and **Skills** sections using the **STAR method** (Situation, Task, Action, Result) while naturally incorporating the missing keywords.

## Prerequisites

- Python 3.10 or later
- A [Google AI Studio](https://aistudio.google.com/apikey) API key for Gemini

## Setup

1. **Clone or download this project**, then open a terminal in the project folder.

2. **Create a virtual environment** (recommended):

   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # macOS / Linux
   source venv/bin/activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure your API key** — create a `.env` file in the project root:

   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

   Replace `your_gemini_api_key_here` with your actual key from [Google AI Studio](https://aistudio.google.com/apikey).

## Usage

Start the Streamlit app:

```bash
streamlit run app.py
```

Your browser will open automatically. Then:

1. **Upload** your CV as a PDF (text is extracted locally with `pypdf`).
2. **Paste** the full job description into the text area.
3. Click **Optimize CV** and wait for the agents to finish.
4. Review the ATS gap analysis and rewritten Experience / Skills sections.
5. Optionally **download** the results as a Markdown file.

## How It Works

```
PDF Upload  →  pypdf text extraction  →  CrewAI sequential crew
                                              │
                                              ├─ ATS Specialist (keyword gap analysis)
                                              │
                                              └─ Resume Writer (STAR-method rewrite)
```

- **Model**: `gemini/gemini-2.5-flash` via CrewAI's LLM integration
- **PDF parsing**: `pypdf` (runs locally; only extracted text is sent to Gemini)
- **API key**: Loaded from `.env` using `python-dotenv`

## Project Structure

```
CV-Trailer/
├── app.py              # Streamlit UI + CrewAI agents
├── requirements.txt    # Python dependencies
├── README.md           # This file
└── .env                # Your Gemini API key (not committed to git)
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `GEMINI_API_KEY not found` | Create a `.env` file with `GEMINI_API_KEY=...` in the project root |
| No text extracted from PDF | The PDF may be image-only; try a text-based PDF or OCR it first |
| Slow response | Gemini API calls can take 30–90 seconds for long CVs; this is normal |
| Import errors | Ensure your virtual environment is activated and dependencies are installed |

## License

MIT
