# ⚽ JobSoccer AI Service

> **AI-Powered Speech-to-Text & Role-Specific Interview Evaluation Microservice for the JobSoccer Football Recruitment Platform.**

---

## 📌 Project Overview

**JobSoccer** is a football recruitment ecosystem connecting clubs, agents, players, and specialized football staff across the globe.

This repository hosts the standalone **AI Evaluation Microservice**. It is designed to evaluate candidate pre-recorded video/audio interviews through a structured, objective, and rubric-governed pipeline:
1. **Audio Transcription:** Converts uploaded interview audio/video into clean text using **OpenAI Whisper-1** (supporting English, French, and Spanish).
2. **Role-Specific Rubric Evaluation:** Evaluates the candidate's answers against strict, position-specific scoring rubrics using **GPT-4o-mini**.
3. **Structured Decision Support:** Returns detailed question-by-question scoring (0–4 scale), quote-backed evidence, confidence metrics, missing evidence, and critical red flags for human review.

---

## 🏗️ Architecture & Workflow

```text
       Candidate Audio / Video (.mp3, .mp4, .m4a, .wav)
                              │
                              ▼
                ┌───────────────────────────┐
                │   Speech-to-Text (STT)    │  <-- OpenAI Whisper-1
                └─────────────┬─────────────┘
                              │
                       Text Transcript
                              │
                              ▼
                ┌───────────────────────────┐
                │    Role Rubric Loader     │  <-- Dynamic JSON Rubrics
                └─────────────┬─────────────┘
                              │
                              ▼
                ┌───────────────────────────┐
                │   LLM Evaluation Engine   │  <-- GPT-4o-mini (Deterministic)
                └─────────────┬─────────────┘
                              │
                              ▼
                ┌───────────────────────────┐
                │    Deterministic Math     │  <-- Strict Python Recalculation
                └─────────────┬─────────────┘
                              │
                              ▼
             Structured Evaluation Result (JSON)
       (Question Breakdown, Evidence, Score / Max Score, Red Flags)
```

---

## ✨ Key Features

* **Complete End-to-End Pipeline:** One single endpoint (`POST /evaluate-audio`) receives an audio file, transcribes it, and evaluates it against the specified role.
* **16+ Football Roles Supported:**
  * **Field Staff:** Head Coach, Goalkeeper Coach, Attacking Coach, Defensive Coach, Scout, Technical Director, Video Analyst, etc.
  * **Office Staff:** Administrative Director, Data Analyst, Community Manager, Digital Marketing, etc.
* **Rubric-Driven Precision:** Evaluates candidates strictly against role-specific criteria rather than generic AI grading.
* **Guaranteed Math Accuracy:** Total scores and maximum possible scores are recalculated directly in Python code to prevent LLM arithmetic errors.
* **Self-Documenting API:** Fully documented interactive Swagger UI at `/docs`.

---

## 📂 Project Structure

```text
jobsoccer_ai/
├── app/
│   ├── main.py                   # FastAPI Application Entry Point
│   ├── api/
│   │   └── endpoints.py          # API Routes (Transcribe, Evaluate, Roles)
│   ├── core/
│   │   └── config.py             # Environment Configuration & API Keys
│   ├── services/
│   │   ├── audio_service.py      # OpenAI Whisper Speech-to-Text Pipeline
│   │   └── interview_scorer.py   # LLM Rubric Evaluation Engine & Math
│   ├── models/
│   │   └── schemas.py            # Pydantic Schemas with Rich API Descriptions
│   └── data/
│       └── rubrics/              # 16 Position Rubric JSON Files
├── scripts/
│   ├── convert_rubrics.py        # Utility to convert source .docx to .json
│   └── rubrics_docx/             # Original rubric documents
├── requirements.txt              # Production dependencies
├── .env                          # Secret API Keys (Git ignored)
└── README.md                     # Project documentation
```

---

## 🛠️ Quick Start & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/jobsoccer-ai-service.git
cd jobsoccer-ai-service
```

### 2. Create and Activate a Virtual Environment
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the project root:
```env
OPENAI_API_KEY=sk-proj-your-actual-openai-api-key-here
```

### 5. Start the Server
```bash
uvicorn app.main:app --reload --port 8001
```

Once running, access the interactive API docs:
* **Swagger UI:** [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)
* **ReDoc:** [http://127.0.0.1:8001/redoc](http://127.0.0.1:8001/redoc)
* **Health Check:** [http://127.0.0.1:8001/](http://127.0.0.1:8001/)

---

## 📡 API Reference

### 1. `GET /api/v1/roles`
Returns all active role slugs and display names available in the system.

### 2. `POST /api/v1/transcribe-audio`
Upload an audio file to extract raw text transcript via OpenAI Whisper.
* **Content-Type:** `multipart/form-data`
* **Fields:** `candidate_id` (string), `audio_file` (file), `language` (optional string, e.g. `en`, `fr`, `es`).

### 3. `POST /api/v1/evaluate-interview`
Evaluate a text transcript against a specific role rubric.
* **Content-Type:** `application/json`
* **Body:**
```json
{
  "candidate_id": "cand_1025",
  "role_slug": "head_coach",
  "transcript": "In my previous club, I structured training around weekly match demands..."
}
```

### 4. `POST /api/v1/evaluate-audio` ⭐ *(Primary End-to-End Endpoint)*
Upload candidate interview audio and receive transcript + structured scoring evaluation in a single call.
* **Content-Type:** `multipart/form-data`
* **Fields:** 
  * `candidate_id` (e.g. `cand_1025`)
  * `role_slug` (e.g. `head_coach`)
  * `audio_file` (`.mp3`, `.mp4`, `.m4a`, `.wav`, max 25 MB)
  * `language` (optional, auto-detected if empty)

---

## 🧪 Demo Verification Profiles

The system has been verified end-to-end with the following benchmark candidates:

| Candidate | Role | Category | Input Format | Result | Score Band |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **Jesse Montana** | Head Coach (`head_coach`) | Field Staff | Audio File (`.mp3`) | **50 / 72** | Good (Moderate evidence) |
| **Sarah Jenkins** | Administrative Director (`administrative_director`) | Office Staff | Transcript (`.json`) | **58 / 60** | Strong (Metrics-backed) |
| **Alex Rivera** | Video Analyst (`video_analyst`) | Technical Staff | Transcript (`.json`) | **~64 / 72** | Strong (Workflow & tools) |

---

## 📊 Evaluation Standard (0–4 Scale)

Each rubric question is evaluated against four criteria levels:
* **4 (Strong):** Role-specific, clear, and supported by a relevant concrete example or measurable process.
* **3 (Good):** Relevant and developed, but missing specific depth, verification, or measurable outcome.
* **2 (Acceptable):** Demonstrates basic understanding but remains generic or incomplete.
* **1 (Weak):** Vague, minimally relevant, impractical, or unsupported.
* **0 (Concerning):** Off-topic, contradictory to the role, or reveals unsafe/unprofessional judgment.

---

## 🛡️ Governance & Anti-Bias Principles

* **Human-in-the-Loop:** AI provides structured decision-support for recruiters and clubs; it does not make automated hiring decisions.
* **Critical Flags:** Ethical, safeguarding, privacy, or legal concerns are escalated to human review via the `red_flags` array.
* **Anti-Bias Policy:** Accent, pronunciation speed, age, gender, ethnicity, or video production quality are explicitly excluded from scoring.

---

Developed for the **JOBSOCCER Platform**.