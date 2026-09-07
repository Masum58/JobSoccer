"""
Batch-convert interview rubric .docx files into a standard JSON schema
using an LLM extraction call.

USAGE:
    1. Put all your rubric .docx files in a folder, e.g. ./rubrics_docx/
    2. Set your OPENAI_API_KEY as an environment variable
    3. Run: python convert_rubrics.py

OUTPUT:
    One JSON file per role in ./rubrics_json/, e.g. attacking_coach.json

You do NOT need to upload files anywhere for this to work — it runs
entirely on your machine and reads docx files from a local folder.
"""

import os
import json
import re
from pathlib import Path

# pyrefly: ignore [missing-import]
from docx import Document          # pip install python-docx
# pyrefly: ignore [missing-import]
from openai import OpenAI          # pip install openai
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv     # pip install python-dotenv

load_dotenv()

client = OpenAI()  # reads OPENAI_API_KEY from env

INPUT_DIR = Path("./rubrics_docx")
OUTPUT_DIR = Path("./rubrics_json")
OUTPUT_DIR.mkdir(exist_ok=True)

# ---- 1. Extract raw text (paragraphs + tables) from a docx ----

def extract_docx_text(path: Path) -> str:
    doc = Document(path)
    lines = []

    for para in doc.paragraphs:
        if para.text.strip():
            lines.append(para.text.strip())

    for table in doc.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            if any(cells):
                lines.append(" | ".join(cells))

    return "\n".join(lines)


# ---- 2. Target JSON schema ----
# Matches the real "Jobsoccer AI Interview Evaluation Rubric" format:
# role-level philosophy + mandatory rules + sectioned questions with
# strong/acceptable/weak criteria + critical human-review flags.
#
# Sections that look IDENTICAL across all 26 roles (scoring scale 0-4,
# consistency labels, required output fields) are captured too, so you
# can diff them across roles later and confirm they're truly shared —
# if so, move them into one constant in your evaluation engine instead
# of repeating them in every JSON file.

SCHEMA_DESCRIPTION = """
{
  "role": "string - job role name, e.g. 'Attacking Coach'",
  "purpose": "string - short purpose line from the doc header",
  "question_count": "number - total questions stated in the doc header",
  "evaluation_approach": "string - the 'Evaluation Approach' section, verbatim",
  "scoring_scale": [
    {
      "score": "number 0-4",
      "classification": "string, e.g. 'Strong', 'Weak'",
      "meaning": "string - description of what this score means"
    }
  ],
  "mandatory_scoring_rules": ["string - each bullet point verbatim"],
  "sections": [
    {
      "section_name": "string, e.g. 'A. Background & Role Definition'",
      "questions": [
        {
          "question": "string - the interview question, verbatim",
          "evaluates": "string - what this question is evaluating",
          "strong_answer_criteria": ["string - each bullet under 'Strong answer demonstrates'"],
          "acceptable": "string - the 'Acceptable' description",
          "weak_or_concerning": "string - the 'Weak or concerning' description"
        }
      ]
    }
  ],
  "score_bands": [
    {
      "range": "string, e.g. '61-72'",
      "percentage": "string, e.g. '84.7-100%'",
      "interpretation": "string"
    }
  ],
  "consistency_classification": [
    {"label": "string, e.g. 'Consistent'", "meaning": "string"}
  ],
  "critical_human_review_flags": ["string - each bullet verbatim"],
  "required_output_fields": [
    {"field": "string, e.g. 'Score'", "description": "string"}
  ],
  "implementation_controls": ["string - each bullet verbatim"]
}
"""

EXTRACTION_PROMPT = """You are given the raw extracted text of a "Jobsoccer AI \
Interview Evaluation Rubric" document for one specific job role.

Extract it into EXACTLY this JSON schema, with no extra commentary, \
no markdown code fences, and no text outside the JSON object:

{schema}

Rules:
- Preserve original wording verbatim wherever the schema says "verbatim" \
  — do not paraphrase or summarize scoring rules, flags, or criteria.
- Keep questions grouped under their lettered sections (A, B, C, ...) in \
  their original order.
- If a field isn't present in this particular document, use an empty \
  string, empty array, or null as appropriate — do not invent content.

RAW DOCUMENT TEXT:
---
{text}
---
"""


def extract_rubric_json(raw_text: str, filename: str) -> dict:
    prompt = EXTRACTION_PROMPT.format(schema=SCHEMA_DESCRIPTION, text=raw_text)

    response = client.chat.completions.create(
        model="gpt-4o-mini",  # cheap + good enough for structured extraction
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0,
        max_tokens=8000,  # these docs are long (18 questions w/ full criteria) - avoid truncation
    )

    content = response.choices[0].message.content

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Fallback: strip stray code fences if the model added them anyway
        cleaned = re.sub(r"^```json|```$", "", content.strip())
        return json.loads(cleaned)


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def main():
    docx_files = sorted(INPUT_DIR.glob("*.docx"))
    if not docx_files:
        print(f"No .docx files found in {INPUT_DIR.resolve()}")
        return

    print(f"Found {len(docx_files)} rubric files.\n")

    for path in docx_files:
        print(f"Processing: {path.name} ...")
        raw_text = extract_docx_text(path)

        if not raw_text.strip():
            print(f"  WARNING: no extractable text found, skipping.")
            continue

        try:
            data = extract_rubric_json(raw_text, path.name)
        except Exception as e:
            print(f"  ERROR extracting {path.name}: {e}")
            continue

        role_name = data.get("role") or path.stem
        out_path = OUTPUT_DIR / f"{slugify(role_name)}.json"

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        n_questions = len(data.get("questions", []))
        print(f"  -> Saved {out_path.name} ({n_questions} questions extracted)")

    print("\nDone. Spot-check a few JSON files against their source docx before trusting all of them.")


if __name__ == "__main__":
    main()