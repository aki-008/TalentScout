# 🌈 Hirebot – AI-Powered Hiring Assistant

**Hirebot** is an intelligent AI agent that streamlines the first-round technical screening of job candidates. It parses resumes, generates personalized technical questions, evaluates answers, and provides honest feedback using a combination of LLMs, FastAPI, and Streamlit.

---

## 🚀 Features

* ✅ **Resume Parsing** (from PDF)
* ✅ **Personalized Technical Questions** based on tech stack
* ✅ **Ruthless Evaluation** with scoring (0-5 scale)
* ✅ **Beautiful Streamlit Frontend** with custom UI/UX
* ✅ **FastAPI Backend** with session tracking and evaluation API
* ✅ **Multi-threaded CLI Support** for agent logic

---

## 📂 Directory Structure

```
aki-008-talentscout/
├── main.py                 # Starts both backend and frontend concurrently
└── app/
    ├── __init__.py
    ├── agent_logic.py      # CLI-based interactive hiring agent
    ├── fastapi_main.py     # FastAPI backend server
    ├── prompts.py          # Prompt templates for resume parsing and evaluation
    └── streamlit_app.py    # Streamlit frontend with modern UI
```

---

## 🎨 UI Preview

The Streamlit frontend features:

* Gradient headers
* Step indicator UI (Start → Resume → Questions → Evaluation)
* Parsed resume preview
* Interactive question/answer forms
* Evaluation report download

> All styled using custom HTML & CSS within Streamlit.

---

## 🌐 Backend API Overview (FastAPI)

### Key Endpoints:

* `POST /sessions/start` → Create a new session
* `POST /sessions/{id}/upload-resume` → Upload PDF resume
* `GET /sessions/{id}/tech-questions` → Generate tech questions
* `POST /sessions/{id}/submit-answers` → Submit answers for evaluation
* `GET /sessions/{id}/status` → Track progress
* `GET /health` → Health check

---

## 📅 How to Run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### Or use Conda:

```bash
conda env create -f conda.yml
conda activate hirebot-env
```

### 2. Add your `.env`

```
GROQ_API_KEY=your_groq_api_key
```

### 3. Launch the app

```bash
python main.py
```

* FastAPI backend: [http://localhost:8000](http://localhost:8000)
* Streamlit frontend: [http://localhost:8501](http://localhost:8501)

---

## ⚖️ Evaluation Philosophy

The evaluation module acts like a tough CTO:

* Scores every answer on **Technical Correctness**, **Architectural Coherence**, and **Depth & Completeness**
* Brutally honest feedback with zero tolerance for fluff
* Clean structured output with scores and comments

---

## ✨ Tech Stack

* **FastAPI** — Backend API
* **Streamlit** — Frontend UI
* **LangGraph + LangChain** — State machines + LLM chains
* **Groq + LLaMA 3** — Inference engine
* **PyMuPDFLoader** — Resume parsing

---

## ✈️ Future Improvements

* Add authentication + role-based access
* Admin dashboard for tracking candidates
* Scoring history + export to CSV
* Support for voice-based Q\&A

---

## ✨ Credits

---

## ❓ License

This project is licensed under the **MIT License**.

```
MIT License

Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
