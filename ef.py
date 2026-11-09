"""
EFFORTSWILL ACADEMY CBT
Teacher-issued access codes, student login, MCQ & theory questions, timer, marking.
"""

from __future__ import annotations

import base64
import hashlib
import json
import random
import re
import string
import uuid
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# ---------------------------------------------------------------------------
# Page & branding configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="EFFORTSWILL ACADEMY CBT",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Asset Discovery & Background Encoding
# ---------------------------------------------------------------------------
_APP_DIR = Path(__file__).parent
_ASSETS = _APP_DIR / "assets"
_DATA_DIR = _APP_DIR / "data"

def _find_image_file(names: list[str], fallback_keyword: str | None = None) -> Path | None:
    """Find an image file across assets, root, and data folders."""
    search_dirs = [_ASSETS, _APP_DIR, _DATA_DIR / "images"]
    for d in search_dirs:
        if not d.is_dir():
            continue
        for name in names:
            p = d / name
            if p.is_file() and p.stat().st_size > 0:
                return p
        if fallback_keyword:
            try:
                for p in d.iterdir():
                    if p.is_file() and p.suffix.lower() in {".jpeg", ".jpg", ".png", ".webp"}:
                        if fallback_keyword in p.stem.lower():
                            return p
            except OSError:
                pass
    return None

def _img_to_data_uri(path: Path | None) -> str:
    """Convert an image file to a base64 data URI."""
    if not path or not path.exists():
        return ""
    suffix = path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        mime = "image/jpeg"
    elif suffix == ".png":
        mime = "image/png"
    elif suffix == ".webp":
        mime = "image/webp"
    else:
        mime = "image/jpeg"
    try:
        data = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:{mime};base64,{data}"
    except OSError:
        return ""

_LOGO_PATH = _find_image_file(["logo.jpeg", "logo.jpg", "logo.png", "logo.webp"], fallback_keyword="logo")
_BG_PATH = _find_image_file(
    ["background.jpeg", "background.jpg", "background.png", "background.webp", "bg.jpeg", "bg.jpg", "bg.png"],
    fallback_keyword="background",
)

_LOGO_URI = _img_to_data_uri(_LOGO_PATH)
_BG_URI = _img_to_data_uri(_BG_PATH)

# Build background rule
if _BG_URI:
    _bg_rule = f"""
        background-image: linear-gradient(rgba(247, 250, 254, 0.48), rgba(247, 250, 254, 0.58)), url("{_BG_URI}") !important;
        background-size: cover !important;
        background-position: center center !important;
        background-repeat: no-repeat !important;
        background-attachment: fixed !important;
    """
else:
    _bg_rule = """
        background: linear-gradient(135deg, #eef2f7 0%, #dbe6f6 100%) !important;
    """

st.markdown(
    f"""
    <style>
    /* Full height and transparent root defaults */
    html, body {{
        min-height: 100%;
        margin: 0;
        padding: 0;
    }}

    /* Main background applied to Streamlit's primary view container */
    .stApp,
    [data-testid="stAppViewContainer"] {{
        min-height: 100vh !important;
        {_bg_rule}
    }}

    /* Keep internal structural wrappers transparent so the background shows through */
    [data-testid="stAppViewContainer"] > .main,
    [data-testid="stMain"],
    [data-testid="stMain"] > section,
    [data-testid="stMainBlockContainer"],
    section.main {{
        background: transparent !important;
        background-color: transparent !important;
    }}

    /* Subtle blurred header bar */
    [data-testid="stHeader"] {{
        background: rgba(255, 255, 255, 0.45) !important;
        backdrop-filter: blur(8px) !important;
        -webkit-backdrop-filter: blur(8px) !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.4) !important;
    }}

    /* Frosted-glass container for main content */
    .block-container {{
        background: rgba(255, 255, 255, 0.65) !important;
        backdrop-filter: blur(8px) !important;
        -webkit-backdrop-filter: blur(8px) !important;
        border: 1px solid rgba(255, 255, 255, 0.8) !important;
        border-radius: 16px !important;
        padding: 1.5rem 1.75rem !important;
        box-shadow: 0 10px 30px rgba(11, 61, 145, 0.10) !important;
        margin-top: 1rem !important;
        margin-bottom: 2rem !important;
    }}

    /* Tab bar & panels */
    .stTabs [data-baseweb="tab-list"] {{
        background: rgba(255, 255, 255, 0.55) !important;
        padding: 0.3rem 0.5rem !important;
        border-radius: 10px !important;
        border: 1px solid rgba(255, 255, 255, 0.6) !important;
    }}
    .stTabs [data-baseweb="tab-panel"] {{
        background: transparent !important;
        padding-top: 0.75rem !important;
    }}

    /* Forms and Expanders */
    div[data-testid="stExpander"],
    div[data-testid="stForm"] {{
        background: rgba(255, 255, 255, 0.82) !important;
        backdrop-filter: blur(6px) !important;
        -webkit-backdrop-filter: blur(6px) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(11, 61, 145, 0.12) !important;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04) !important;
    }}

    /* Question & Option Typography */
    .cbt-question {{
        font-size: 24px !important;
        font-weight: 700 !important;
        color: #0b1f44 !important;
        line-height: 1.35;
        margin-bottom: 0.75rem;
        text-shadow: 0 1px 2px rgba(255,255,255,0.7);
    }}
    .cbt-option, div[data-testid="stRadio"] label,
    div[data-testid="stRadio"] label p,
    div[data-testid="stRadio"] label span {{
        font-size: 20px !important;
        color: #111111 !important;
        line-height: 1.4 !important;
    }}

    /* Navigator grid buttons: small width, compact badge buttons */
    div[data-testid="stHorizontalBlock"]:has(> div[data-testid="column"]:nth-child(6)) div[data-testid="column"] {{
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
    }}
    div[data-testid="stHorizontalBlock"]:has(> div[data-testid="column"]:nth-child(6)) div[data-testid="column"] button {{
        max-width: 36px !important;
        width: 34px !important;
        min-width: 28px !important;
        height: 30px !important;
        min-height: 30px !important;
        padding: 0px !important;
        margin: 2px auto !important;
        border-radius: 5px !important;
    }}
    div[data-testid="stHorizontalBlock"]:has(> div[data-testid="column"]:nth-child(6)) div[data-testid="column"] button p {{
        font-size: 0.72rem !important;
        font-weight: 700 !important;
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1 !important;
        text-align: center !important;
    }}

    /* Normal buttons (Prev, Next, Submit, Refresh, Forms) maintain proper full dimensions */
    div[data-testid="stHorizontalBlock"]:not(:has(> div[data-testid="column"]:nth-child(6))) div[data-testid="column"] button {{
        min-height: 2.2rem !important;
        font-size: 0.95rem !important;
        border-radius: 6px !important;
    }}

    /* Header & Branding */
    .cbt-brand {{
        font-size: 1.75rem;
        font-weight: 800;
        color: #0b3d91;
        letter-spacing: -0.02em;
        margin-bottom: 0.15rem;
        text-shadow: 0 1px 2px rgba(255,255,255,0.8);
    }}
    .cbt-sub {{ 
        color: #333333; 
        font-size: 0.95rem; 
        margin-bottom: 1rem;
        font-weight: 500;
    }}

    /* Timer box */
    .timer-box {{
        background: #fff3cd; 
        border: 2px solid #ffc107; 
        border-radius: 8px;
        padding: 0.55rem 1rem; 
        font-size: 1.25rem; 
        font-weight: 700;
        color: #856404; 
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }}
    .timer-box.danger {{
        background: #f8d7da; 
        border-color: #dc3545; 
        color: #721c24;
    }}

    /* Printable results sheet */
    .results-sheet {{
        border: 2px solid #0b3d91; 
        padding: 1.75rem; 
        background: #ffffff !important; 
        color: #000;
        font-family: Georgia, "Times New Roman", serif;
        border-radius: 8px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.08);
    }}
    .results-sheet h2 {{ margin-top: 0; color: #0b3d91; }}
    .grade-badge {{
        display: inline-block; padding: 0.35rem 0.9rem; border-radius: 6px;
        font-weight: 800; font-size: 1.4rem; background: #e8f5e9;
        color: #1b5e20; border: 2px solid #2e7d32;
    }}
    .code-box {{
        font-size: 1.5rem; font-weight: 800; letter-spacing: 0.12em;
        background: #e3f2fd; border: 2px dashed #0b3d91; border-radius: 8px;
        padding: 0.65rem 1.15rem; text-align: center; color: #0b3d91;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Paths & defaults
# ---------------------------------------------------------------------------
DATA_DIR = Path(__file__).parent / "data"
BANK_FILE = DATA_DIR / "question_bank.json"
SETTINGS_FILE = DATA_DIR / "settings.json"
STUDENTS_FILE = DATA_DIR / "students.json"
SUBMISSIONS_FILE = DATA_DIR / "submissions.json"
IMAGE_DIR = DATA_DIR / "images"
PASSPORT_DIR = IMAGE_DIR / "passports"
DATA_DIR.mkdir(exist_ok=True)
IMAGE_DIR.mkdir(exist_ok=True)
PASSPORT_DIR.mkdir(exist_ok=True)

SCIENCE_SUBJECTS = [
    "Mathematics",
    "Further Mathematics",
    "English Language",
    "Physics",
    "Chemistry",
    "Biology",
    "Agricultural Science",
    "Geography",
    "Computer Studies / ICT",
    "Technical Drawing",
    "Basic Science",
    "Basic Technology",
]
COMMERCIAL_SUBJECTS = [
    "Economics",
    "Commerce",
    "Financial Accounting",
    "Business Studies",
    "Office Practice",
    "Marketing",
    "Insurance",
    "Store Management",
    "Government",
    "Civic Education",
    "Book Keeping",
]
ALL_SUBJECTS = SCIENCE_SUBJECTS + COMMERCIAL_SUBJECTS

DEFAULT_PASSWORD_HASH = hashlib.sha256(b"teacher123").hexdigest()

DEFAULT_BANK = {
    "JSS1 Digital Technology": [
        {
            "type": "mcq",
            "question": "Which part of a computer is often called the brain of the computer?",
            "options": {
                "A": "Monitor",
                "B": "Central Processing Unit (CPU)",
                "C": "Keyboard",
                "D": "Mouse",
            },
            "answer": "B",
            "explanation": "The CPU processes instructions and controls computer operations.",
        },
        {
            "type": "mcq",
            "question": "Which of these is an example of computer hardware?",
            "options": {
                "A": "Microsoft Word",
                "B": "Windows Operating System",
                "C": "Keyboard",
                "D": "Paint Application",
            },
            "answer": "C",
            "explanation": "A keyboard is a physical component, so it is hardware.",
        },
        {
            "type": "theory",
            "question": "Explain two clear differences between computer hardware and software.",
            "options": {},
            "answer": "",
            "explanation": "Hardware is physical; software refers to instructions and programs.",
        },
    ],
}

DEFAULT_SETTINGS = {
    "password_hash": DEFAULT_PASSWORD_HASH,
    "exam_durations": {},
    "default_duration_minutes": 30,  # Default to 30 mins so CBT examinations have an active timer
    "grade_boundaries": {"A": 70, "B": 60, "C": 50, "D": 40, "E": 30, "F": 0},
    "require_student_code": True,
}

# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------
def save_bank(bank_data: dict) -> None:
    BANK_FILE.write_text(json.dumps(bank_data, indent=2, ensure_ascii=False), encoding="utf-8")

def load_bank() -> dict:
    if BANK_FILE.exists():
        try:
            data = json.loads(BANK_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                for qs in data.values():
                    for q in qs:
                        if "type" not in q:
                            q["type"] = "theory" if not q.get("options") else "mcq"
                return data
        except (json.JSONDecodeError, OSError):
            st.warning("The saved question bank could not be read. Using default sample questions.")
    save_bank(DEFAULT_BANK)
    return json.loads(json.dumps(DEFAULT_BANK))

def save_settings(settings_data: dict) -> None:
    SETTINGS_FILE.write_text(json.dumps(settings_data, indent=2), encoding="utf-8")

def load_settings() -> dict:
    if SETTINGS_FILE.exists():
        try:
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                merged = {**DEFAULT_SETTINGS, **data}
                merged["grade_boundaries"] = {
                    **DEFAULT_SETTINGS["grade_boundaries"],
                    **data.get("grade_boundaries", {}),
                }
                # Ensure a sensible default duration exists
                if not merged.get("default_duration_minutes"):
                    merged["default_duration_minutes"] = 30
                return merged
        except (json.JSONDecodeError, OSError):
            pass
    save_settings(DEFAULT_SETTINGS)
    return json.loads(json.dumps(DEFAULT_SETTINGS))

def load_students() -> list:
    if STUDENTS_FILE.exists():
        try:
            data = json.loads(STUDENTS_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
        except (json.JSONDecodeError, OSError):
            pass
    return []

def save_students(students_list: list) -> None:
    STUDENTS_FILE.write_text(json.dumps(students_list, indent=2, ensure_ascii=False), encoding="utf-8")

def load_submissions() -> list:
    if SUBMISSIONS_FILE.exists():
        try:
            data = json.loads(SUBMISSIONS_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
        except (json.JSONDecodeError, OSError):
            pass
    return []

def save_submissions(subs: list) -> None:
    SUBMISSIONS_FILE.write_text(json.dumps(subs, indent=2, ensure_ascii=False), encoding="utf-8")

def hash_password(plain: str) -> str:
    return hashlib.sha256(plain.encode("utf-8")).hexdigest()

def check_password(plain: str, stored_hash: str) -> bool:
    return hash_password(plain) == stored_hash

def generate_access_code(existing_codes: set) -> str:
    alphabet = string.ascii_uppercase + string.digits
    for _ in range(50):
        code = "".join(random.choices(alphabet, k=8))
        if code not in existing_codes:
            return code
    return uuid.uuid4().hex[:8].upper()

# ---------------------------------------------------------------------------
# Question utilities
# ---------------------------------------------------------------------------
def normalize_answer(value) -> str:
    return str(value).strip().upper().replace("OPTION ", "")

def is_mcq(q: dict) -> bool:
    return q.get("type", "mcq") != "theory" and bool(q.get("options"))

def row_to_question(row) -> dict:
    question_text = str(row.get("question", "")).strip()
    qtype = str(row.get("type", "mcq")).strip().lower()
    if qtype not in {"mcq", "theory"}:
        qtype = "mcq"
    explanation = str(row.get("explanation", "")).strip()
    if explanation.lower() == "nan":
        explanation = ""
    image_url = str(row.get("image_url", "")).strip()
    if image_url.lower() == "nan":
        image_url = ""

    if qtype == "theory":
        q = {
            "type": "theory",
            "question": question_text,
            "options": {},
            "answer": "",
            "explanation": explanation,
        }
        if not question_text:
            raise ValueError("Theory question text cannot be blank.")
    else:
        options = {
            "A": str(row.get("option_a", "")).strip(),
            "B": str(row.get("option_b", "")).strip(),
            "C": str(row.get("option_c", "")).strip(),
            "D": str(row.get("option_d", "")).strip(),
        }
        answer = normalize_answer(row.get("correct_answer", ""))
        if not question_text or any(not v or v.lower() == "nan" for v in options.values()):
            raise ValueError("Every MCQ row must contain a question and all four options.")
        if answer not in {"A", "B", "C", "D"}:
            raise ValueError("correct_answer must be A, B, C, or D for MCQ.")
        q = {
            "type": "mcq",
            "question": question_text,
            "options": options,
            "answer": answer,
            "explanation": explanation,
        }
    if image_url:
        q["image_url"] = image_url
    return q

def questions_to_dataframe(bank_data: dict) -> pd.DataFrame:
    rows = []
    for exam, questions in bank_data.items():
        for q in questions:
            opts = q.get("options") or {}
            rows.append(
                {
                    "exam": exam,
                    "type": q.get("type", "mcq"),
                    "question": q["question"],
                    "option_a": opts.get("A", ""),
                    "option_b": opts.get("B", ""),
                    "option_c": opts.get("C", ""),
                    "option_d": opts.get("D", ""),
                    "correct_answer": q.get("answer", ""),
                    "explanation": q.get("explanation", ""),
                    "image_url": q.get("image_url") or q.get("image_path") or "",
                }
            )
    return pd.DataFrame(
        rows,
        columns=[
            "exam", "type", "question", "option_a", "option_b", "option_c", "option_d",
            "correct_answer", "explanation", "image_url",
        ],
    )

def save_uploaded_image(uploaded_file, subfolder: str | None = None) -> str | None:
    if uploaded_file is None:
        return None
    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix not in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}:
        suffix = ".png"
    safe_name = f"{uuid.uuid4().hex}{suffix}"
    folder = IMAGE_DIR
    rel = "data/images"
    if subfolder:
        folder = IMAGE_DIR / subfolder
        folder.mkdir(parents=True, exist_ok=True)
        rel = f"data/images/{subfolder}"
    dest = folder / safe_name
    dest.write_bytes(uploaded_file.getvalue())
    return f"{rel}/{safe_name}"

def save_passport_photo(uploaded_file) -> str | None:
    return save_uploaded_image(uploaded_file, subfolder="passports")

def passport_data_uri(photo_path: str | None) -> str:
    if not photo_path:
        return ""
    p = Path(photo_path)
    if not p.is_absolute():
        p = Path(__file__).parent / photo_path
    if not p.exists():
        return ""
    mime = "image/jpeg"
    if p.suffix.lower() == ".png":
        mime = "image/png"
    elif p.suffix.lower() in {".gif"}:
        mime = "image/gif"
    elif p.suffix.lower() in {".webp"}:
        mime = "image/webp"
    data = base64.b64encode(p.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"

def resolve_image_source(q: dict):
    path = q.get("image_path") or ""
    url = q.get("image_url") or ""
    if path:
        p = Path(path)
        if not p.is_absolute():
            p = Path(__file__).parent / path
        if p.exists():
            return str(p)
    if url and re.match(r"^https?://", url, re.I):
        return url
    if url and Path(url).exists():
        return url
    return None

def show_question_image(q: dict, caption: str = "Question diagram") -> None:
    src = resolve_image_source(q)
    if not src:
        return
    try:
        st.image(src, caption=caption, use_container_width=True)
    except Exception:
        try:
            st.image(src, caption=caption)
        except Exception:
            st.caption(f"(Image could not be loaded: {src})")

def assign_grade(percent: float, boundaries: dict) -> str:
    ordered = sorted(boundaries.items(), key=lambda x: -x[1])
    for letter, threshold in ordered:
        if percent >= threshold:
            return letter
    return "F"

def find_student_by_code(students_list: list, code: str) -> dict | None:
    code = code.strip().upper()
    for s in students_list:
        if s.get("code", "").upper() == code:
            return s
    return None

# ---------------------------------------------------------------------------
# Session bootstrap
# ---------------------------------------------------------------------------
if "bank" not in st.session_state:
    st.session_state.bank = load_bank()
if "settings" not in st.session_state:
    st.session_state.settings = load_settings()
if "students" not in st.session_state:
    st.session_state.students = load_students()
if "exam_attempt" not in st.session_state:
    st.session_state.exam_attempt = None
if "teacher_authenticated" not in st.session_state:
    st.session_state.teacher_authenticated = False
if "student_session" not in st.session_state:
    st.session_state.student_session = None

bank = st.session_state.bank
settings = st.session_state.settings
students = st.session_state.students

# ---------------------------------------------------------------------------
# Header & Navigation
# ---------------------------------------------------------------------------
_logo_html = (
    f'<img src="{_LOGO_URI}" alt="Effortswill Academy logo" '
    f'style="height:62px;width:auto;border-radius:8px;margin-right:12px;vertical-align:middle;box-shadow:0 2px 8px rgba(0,0,0,0.15);" />'
    if _LOGO_URI else ""
)
st.markdown(
    f"""
    <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:0.25rem;">
        {_logo_html}
        <div class="cbt-brand">EFFORTSWILL ACADEMY CBT</div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="cbt-sub">Purposefulness &amp; Dedication · Teacher-Issued Access Codes · Objective &amp; Theory</div>',
    unsafe_allow_html=True,
)

student_tab, teacher_tab, help_tab = st.tabs(
    ["🎓 Student exam", "👩‍🏫 Teacher dashboard", "ℹ️ Setup & template"]
)

# ===========================================================================
# STUDENT TAB — Login with Teacher-Issued Access Code Only
# ===========================================================================
with student_tab:
    # ---- Not logged in ----
    if st.session_state.student_session is None:
        st.subheader("Student Examination Login")
        st.caption("Enter the unique 8-character access code provided to you by your teacher.")
        
        login_col1, _ = st.columns([2, 1])
        with login_col1:
            login_code = st.text_input("Access code", key="login_code", placeholder="e.g. A7K2M9QX")
            if st.button("Log in & Proceed to Exam", type="primary", key="student_login_btn"):
                stu = find_student_by_code(students, login_code or "")
                if not stu:
                    st.error("Invalid access code. Please confirm your access code with your teacher.")
                elif stu.get("completed"):
                    st.error(
                        f"This code has already been used to complete **{stu.get('exam')}**. "
                        "Please speak with your teacher if you require a retake or reset."
                    )
                elif stu.get("exam") not in bank or not bank.get(stu.get("exam")):
                    st.error(f"The examination '{stu.get('exam')}' linked to this code is currently unavailable.")
                else:
                    st.session_state.student_session = {
                        "code": stu["code"],
                        "name": stu["name"],
                        "class": stu.get("class", ""),
                        "exam": stu["exam"],
                    }
                    st.session_state.exam_attempt = None
                    st.success(f"Welcome, {stu['name']}!")
                    st.rerun()

    # ---- Logged in ----
    else:
        sess = st.session_state.student_session
        chosen_exam = sess["exam"]
        if chosen_exam not in bank or not bank[chosen_exam]:
            st.error("The selected examination is currently unavailable in the bank.")
            if st.button("Log out", key="student_logout_no_exam"):
                st.session_state.student_session = None
                st.session_state.exam_attempt = None
                st.rerun()
        else:
            questions = bank[chosen_exam]
            duration_min = settings.get("exam_durations", {}).get(
                chosen_exam, settings.get("default_duration_minutes", 30)
            )
            if not duration_min or duration_min <= 0:
                duration_min = settings.get("default_duration_minutes", 30) or 30

            top_l, top_r = st.columns([4, 1])
            with top_l:
                st.write(
                    f"**{sess['name']}**"
                    + (f" · Class: {sess['class']}" if sess.get("class") else "")
                    + f" · Code: `{sess['code']}` · Exam: **{chosen_exam}**"
                )
            with top_r:
                if st.button("Log out", key="student_logout_header"):
                    st.session_state.student_session = None
                    st.session_state.exam_attempt = None
                    st.rerun()

            # Init attempt bound to this session exam
            if (
                st.session_state.exam_attempt is None
                or st.session_state.exam_attempt.get("exam") != chosen_exam
                or st.session_state.exam_attempt.get("student_code") != sess["code"]
            ):
                st.session_state.exam_attempt = {
                    "exam": chosen_exam,
                    "student_code": sess["code"],
                    "index": 0,
                    "answers": {},
                    "finished": False,
                    "order": list(range(len(questions))),
                    "started_at": None,
                    "duration_seconds": duration_min * 60,
                    "student_name": sess["name"],
                    "student_class": sess.get("class", ""),
                    "auto_submitted": False,
                }

            attempt = st.session_state.exam_attempt
            if len(attempt["order"]) != len(questions):
                attempt["order"] = list(range(len(questions)))
                attempt["index"] = 0
                st.session_state.exam_attempt = attempt

            # Start Exam Prompt
            if attempt["started_at"] is None and not attempt["finished"]:
                n_mcq = sum(1 for q in questions if is_mcq(q))
                n_th = len(questions) - n_mcq
                st.info(
                    f"**{chosen_exam}** — {len(questions)} question(s) "
                    f"({n_mcq} objective, {n_th} theory)"
                    + (f" · Time limit: **{duration_min} minutes**" if duration_min else " · Untimed exam")
                )
                if st.button("▶ Start exam", type="primary", use_container_width=True, key="start_exam_btn"):
                    attempt["started_at"] = datetime.now(timezone.utc).isoformat()
                    attempt["duration_seconds"] = duration_min * 60 if duration_min else 30 * 60
                    for s in students:
                        if s.get("code") == sess["code"]:
                            s["started"] = True
                            break
                    save_students(students)
                    st.session_state.students = students
                    st.rerun()

            elif not attempt["finished"]:
                # Ensure duration_seconds is active
                if attempt.get("duration_seconds", 0) <= 0 and duration_min > 0:
                    attempt["duration_seconds"] = duration_min * 60

                # -----------------------------------------------------------
                # SERVER-SIDE TIMER EXPIRY CHECK
                # -----------------------------------------------------------
                remaining_seconds = None
                if attempt.get("duration_seconds", 0) > 0 and attempt.get("started_at"):
                    try:
                        started = datetime.fromisoformat(attempt["started_at"])
                        if started.tzinfo is None:
                            started = started.replace(tzinfo=timezone.utc)
                        elapsed = (datetime.now(timezone.utc) - started).total_seconds()
                        remaining_seconds = max(0.0, attempt["duration_seconds"] - elapsed)
                        if remaining_seconds <= 0:
                            attempt["finished"] = True
                            attempt["auto_submitted"] = True
                            st.rerun()
                    except Exception:
                        remaining_seconds = float(attempt["duration_seconds"])

                # -----------------------------------------------------------
                # 1. QUESTIONS NUMBERING BUTTONS (QUESTION NAVIGATOR)
                # -----------------------------------------------------------
                total_questions = len(questions)
                idx = attempt["index"]
                q_index = attempt["order"][idx]
                q = questions[q_index]

                st.caption("**Question Navigator** · ● current · ✓ answered · number = unattempted")
                ROW_SIZE = 12
                for row_start in range(0, total_questions, ROW_SIZE):
                    row_end = min(row_start + ROW_SIZE, total_questions)
                    count_in_row = row_end - row_start
                    cols = st.columns(ROW_SIZE)
                    for offset in range(count_in_row):
                        n = row_start + offset
                        if n == idx:
                            label, kind = f"●{n + 1}", "primary"
                        elif n in attempt["answers"] and str(attempt["answers"].get(n, "")).strip():
                            label, kind = f"✓{n + 1}", "secondary"
                        else:
                            label, kind = f"{n + 1}", "secondary"
                        with cols[offset]:
                            if st.button(
                                label,
                                key=f"jump_{sess['code']}_{n}",
                                use_container_width=True,
                                type=kind,
                            ):
                                attempt["index"] = n
                                st.rerun()

                answered_count = sum(
                    1
                    for i in range(total_questions)
                    if str(attempt["answers"].get(i, "")).strip()
                )
                st.caption(f"Answered: {answered_count} of {total_questions}")
                st.progress((idx + 1) / total_questions)

                # -----------------------------------------------------------
                # 2. LIVE WORKING TIMER (COMES AFTER QUESTION NAVIGATOR)
                # -----------------------------------------------------------
                st.write("")
                if remaining_seconds is not None:
                    mins, secs = divmod(int(remaining_seconds), 60)
                    timer_component_html = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                      <meta charset="utf-8">
                      <style>
                        * {{
                          box-sizing: border-box;
                          margin: 0;
                          padding: 0;
                          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                        }}
                        body {{
                          background: transparent;
                          overflow: hidden;
                        }}
                        .timer-box {{
                          background: #fff3cd; 
                          border: 2px solid #ffc107; 
                          border-radius: 8px;
                          padding: 0.5rem 1rem; 
                          font-size: 1.25rem; 
                          font-weight: 700;
                          color: #856404; 
                          text-align: center;
                          box-shadow: 0 2px 8px rgba(0,0,0,0.06);
                          transition: background-color 0.3s, border-color 0.3s, color 0.3s;
                        }}
                        .timer-box.danger {{
                          background: #f8d7da !important; 
                          border-color: #dc3545 !important; 
                          color: #721c24 !important;
                          animation: timerPulse 1s infinite alternate;
                        }}
                        @keyframes timerPulse {{
                          from {{ opacity: 1; }}
                          to {{ opacity: 0.65; }}
                        }}
                      </style>
                    </head>
                    <body>
                      <div id="live-timer-display" class="timer-box{' danger' if remaining_seconds < 60 else ''}">
                        ⏱ Time remaining: {mins:02d}:{secs:02d}
                      </div>
                      <script>
                        (function() {{
                          var targetTime = Date.now() + ({int(remaining_seconds)} * 1000);
                          var display = document.getElementById("live-timer-display");
                          
                          function formatTwo(num) {{
                            return (num < 10 ? "0" : "") + num;
                          }}
                          
                          function updateCountdown() {{
                            var now = Date.now();
                            var diff = Math.max(0, Math.round((targetTime - now) / 1000));
                            var m = Math.floor(diff / 60);
                            var s = diff % 60;
                            
                            display.textContent = "⏱ Time remaining: " + formatTwo(m) + ":" + formatTwo(s);
                            
                            if (diff <= 60) {{
                              display.className = "timer-box danger";
                            }} else {{
                              display.className = "timer-box";
                            }}
                            
                            if (diff <= 0) {{
                              clearInterval(timerInterval);
                              display.textContent = "⏱ Time expired! Submitting examination...";
                              setTimeout(function() {{
                                try {{
                                  var buttons = window.parent.document.querySelectorAll("button");
                                  for (var i = 0; i < buttons.length; i++) {{
                                    var txt = (buttons[i].innerText || buttons[i].textContent || "").trim();
                                    if (txt.indexOf("Finish exam") !== -1 || txt.indexOf("Submit exam") !== -1 || txt.indexOf("Yes, submit") !== -1) {{
                                      buttons[i].click();
                                      return;
                                    }}
                                  }}
                                  window.parent.location.reload();
                                }} catch(e) {{
                                  window.parent.location.reload();
                                }}
                              }}, 500);
                            }}
                          }}
                          
                          updateCountdown();
                          var timerInterval = setInterval(updateCountdown, 1000);
                        }})();
                      </script>
                    </body>
                    </html>
                    """
                    t_col1, t_col2 = st.columns([5, 1])
                    with t_col1:
                        components.html(timer_component_html, height=56)
                    with t_col2:
                        if st.button("🔄 Sync", key="refresh_timer", use_container_width=True, help="Synchronize timer with server"):
                            st.rerun()
                else:
                    st.caption("⏱ Untimed exam sitting")

                st.divider()

                # -----------------------------------------------------------
                # 3. CURRENT QUESTION CONTENT
                # -----------------------------------------------------------
                qtype_label = "Objective (MCQ)" if is_mcq(q) else "Theory"
                st.markdown(f"**Question {idx + 1} of {total_questions}** · _{qtype_label}_")
                st.markdown(f'<div class="cbt-question">{q["question"]}</div>', unsafe_allow_html=True)
                show_question_image(q)

                if is_mcq(q):
                    answer_key = f"ans_mcq_{sess['code']}_{q_index}"
                    options = ["A", "B", "C", "D"]
                    opts_map = q.get("options") or {}
                    if answer_key not in st.session_state:
                        saved = attempt["answers"].get(q_index)
                        st.session_state[answer_key] = saved if saved in options else None
                    selected = st.radio(
                        "Choose one answer:",
                        options,
                        format_func=lambda letter: f"{letter}. {opts_map.get(letter, '')}",
                        key=answer_key,
                    )
                    if selected in options:
                        attempt["answers"][q_index] = selected
                else:
                    theory_key = f"ans_th_{sess['code']}_{q_index}"
                    if theory_key not in st.session_state:
                        st.session_state[theory_key] = str(
                            attempt["answers"].get(q_index, "") or ""
                        )
                    text = st.text_area(
                        "Write your answer:",
                        key=theory_key,
                        height=160,
                    )
                    if text is not None:
                        attempt["answers"][q_index] = text

                left, right = st.columns(2)
                with left:
                    if st.button(
                        "← Previous",
                        disabled=(idx == 0),
                        use_container_width=True,
                        key=f"prev_{q_index}",
                    ):
                        attempt["index"] -= 1
                        st.rerun()
                with right:
                    if idx < total_questions - 1:
                        if st.button("Next →", type="primary", use_container_width=True, key=f"next_{q_index}"):
                            attempt["index"] += 1
                            st.rerun()
                    else:
                        if st.button("Finish exam", type="primary", use_container_width=True, key="finish_btn"):
                            attempt["finished"] = True
                            st.rerun()

                st.divider()
                unanswered = total_questions - answered_count
                if unanswered:
                    st.warning(f"{unanswered} question(s) currently unanswered.")
                if st.button("Submit exam", use_container_width=True, key="submit_btn"):
                    if unanswered:
                        st.session_state["confirm_submit"] = True
                    else:
                        attempt["finished"] = True
                        st.rerun()
                if st.session_state.get("confirm_submit"):
                    st.warning("Some questions are still unanswered. Submit anyway?")
                    y, n = st.columns(2)
                    with y:
                        if st.button("Yes, submit", type="primary", key="confirm_submit_yes"):
                            attempt["finished"] = True
                            st.session_state["confirm_submit"] = False
                            st.rerun()
                    with n:
                        if st.button("Continue answering", key="confirm_submit_no"):
                            st.session_state["confirm_submit"] = False
                            st.rerun()

            else:
                # ---- Results ----
                mcq_indices = [i for i, q in enumerate(questions) if is_mcq(q)]
                theory_indices = [i for i, q in enumerate(questions) if not is_mcq(q)]
                score = sum(
                    1
                    for i in mcq_indices
                    if attempt["answers"].get(i) == questions[i].get("answer")
                )
                total_mcq = len(mcq_indices)
                percent = (score / total_mcq * 100) if total_mcq else 0.0
                grade = assign_grade(percent, settings["grade_boundaries"]) if total_mcq else "—"
                exam_date = datetime.now().strftime("%Y-%m-%d %H:%M")
                name_display = attempt.get("student_name") or sess["name"]
                class_display = attempt.get("student_class") or sess.get("class") or "—"

                if attempt.get("auto_submitted"):
                    st.warning("Time expired — examination submitted automatically.")

                st.success("Exam completed successfully!")
                a, b, c, d = st.columns(4)
                a.metric("MCQ score", f"{score}/{total_mcq}" if total_mcq else "N/A")
                b.metric("Percentage", f"{percent:.1f}%" if total_mcq else "—")
                c.metric("Grade", grade)
                d.metric("Theory Qs", len(theory_indices))

                # Mark code completed + store submission
                save_key = f"saved_result_{sess['code']}"
                if not attempt.get("result_saved") and not st.session_state.get(save_key):
                    for s in students:
                        if s.get("code") == sess["code"]:
                            s["completed"] = True
                            s["completed_at"] = datetime.now(timezone.utc).isoformat()
                            s["mcq_score"] = score
                            s["mcq_total"] = total_mcq
                            s["percent"] = round(percent, 1)
                            s["grade"] = grade
                            break
                    save_students(students)
                    st.session_state.students = students

                    subs = load_submissions()
                    already = any(
                        s.get("code") == sess["code"] and s.get("exam") == chosen_exam
                        for s in subs
                    )
                    if not already:
                        subs.append(
                            {
                                "code": sess["code"],
                                "name": name_display,
                                "class": class_display,
                                "exam": chosen_exam,
                                "submitted_at": exam_date,
                                "answers": {str(k): v for k, v in attempt["answers"].items()},
                                "mcq_score": score,
                                "mcq_total": total_mcq,
                                "percent": round(percent, 1),
                                "grade": grade,
                            }
                        )
                        save_submissions(subs)
                    attempt["result_saved"] = True
                    st.session_state[save_key] = True

                if attempt.get("result_saved") or st.session_state.get(save_key):
                    st.success("Result automatically recorded. Your teacher can view it in the Teacher Dashboard.")

                st.markdown("### 📄 Results sheet")
                photo_uri = ""
                for s in students:
                    if s.get("code") == sess["code"]:
                        photo_uri = passport_data_uri(s.get("photo_path"))
                        break
                photo_html = ""
                if photo_uri:
                    photo_html = f"""
                    <div style="float:right; margin:0 0 12px 16px; text-align:center;">
                      <img src="{photo_uri}" alt="Passport"
                           style="width:110px; height:130px; object-fit:cover;
                                  border:2px solid #333; border-radius:4px;" />
                      <div style="font-size:0.7rem; color:#555; margin-top:2px;">Passport</div>
                    </div>
                    """
                results_html = f"""
                <div class="results-sheet">
                  <h2>EFFORTSWILL ACADEMY CBT — Results</h2>
                  {photo_html}
                  <table style="width:100%; border-collapse:collapse; margin-bottom:1rem;">
                    <tr><td style="padding:4px 8px;"><strong>Student</strong></td><td>{name_display}</td></tr>
                    <tr><td style="padding:4px 8px;"><strong>Class</strong></td><td>{class_display}</td></tr>
                    <tr><td style="padding:4px 8px;"><strong>Access code</strong></td><td>{sess['code']}</td></tr>
                    <tr><td style="padding:4px 8px;"><strong>Examination</strong></td><td>{chosen_exam}</td></tr>
                    <tr><td style="padding:4px 8px;"><strong>Date</strong></td><td>{exam_date}</td></tr>
                    <tr><td style="padding:4px 8px;"><strong>MCQ score</strong></td><td>{score} / {total_mcq}</td></tr>
                    <tr><td style="padding:4px 8px;"><strong>Percentage</strong></td><td>{percent:.1f}%</td></tr>
                    <tr><td style="padding:4px 8px;"><strong>Grade</strong></td>
                        <td><span class="grade-badge">{grade}</span></td></tr>
                  </table>
                  <div style="clear:both;"></div>
                  <p style="font-size:0.85rem; color:#555;">Theory responses are saved for teacher review and grading.</p>
                </div>
                """
                st.markdown(results_html, unsafe_allow_html=True)
                st.caption("Print with Ctrl+P / Cmd+P.")

                with st.expander("📋 Check answers (MCQ + your theory responses)", expanded=False):
                    for i, q in enumerate(questions):
                        user_answer = attempt["answers"].get(i, "")
                        if is_mcq(q):
                            correct = q.get("answer")
                            ok = user_answer == correct
                            status = "✅ Correct" if ok else ("❌ Incorrect" if user_answer else "○ Not answered")
                            st.markdown(f"**{i + 1}. {q['question']}** — {status}")
                            show_question_image(q, caption=f"Q{i+1}")
                            if user_answer in (q.get("options") or {}):
                                st.write(f"Your answer: **{user_answer}**. {q['options'][user_answer]}")
                            else:
                                st.write("Your answer: *Not answered*")
                            st.write(f"Correct answer: **{correct}**. {q['options'].get(correct, '')}")
                        else:
                            st.markdown(f"**{i + 1}. [Theory] {q['question']}**")
                            show_question_image(q, caption=f"Q{i+1}")
                            st.write("Your answer:")
                            st.write(user_answer or "*Not answered*")
                            if q.get("explanation"):
                                st.caption(f"Marking guide: {q['explanation']}")
                        st.divider()

                st.info("Your access code has now been completed and closed. Log out when finished.")
                if st.button("Log out", type="primary", key="student_logout_after_exam"):
                    st.session_state.student_session = None
                    st.session_state.exam_attempt = None
                    st.rerun()

# ===========================================================================
# TEACHER DASHBOARD
# ===========================================================================
with teacher_tab:
    if not st.session_state.teacher_authenticated:
        st.subheader("Teacher login")
        st.caption("Default password: **teacher123**")
        pwd = st.text_input("Password", type="password", key="teacher_pwd")
        if st.button("Log in", type="primary", key="teacher_login_btn"):
            if check_password(pwd, settings["password_hash"]):
                st.session_state.teacher_authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password.")
    else:
        st.subheader("Teacher dashboard")
        if st.button("Log out (teacher)", key="teacher_logout_btn"):
            st.session_state.teacher_authenticated = False
            st.rerun()

        # ---- Student registrations & Access Code Generation ----
        with st.expander("🎓 Student registrations & access codes", expanded=True):
            st.markdown(
                "Register a student for one or more examinations. The system generates a unique **8-character "
                "access code** per subject to give to the student. Passport photo is optional."
            )
            bank_exams = list(bank.keys()) if bank else []
            subject_choices = list(dict.fromkeys(ALL_SUBJECTS + bank_exams))
            with st.form("teacher_reg_form", clear_on_submit=True):
                t_name = st.text_input("Student full name *")
                t_class = st.text_input("Class / Form", placeholder="e.g. SS2 Science")
                t_photo = st.file_uploader(
                    "Passport photograph (optional)",
                    type=["png", "jpg", "jpeg", "webp"],
                    key="teacher_reg_passport",
                )
                st.markdown("**Subjects to register** (select all that apply):")
                t_subjects = st.multiselect(
                    "Science, commercial & bank subjects",
                    options=subject_choices,
                    default=[],
                    key="teacher_reg_subjects",
                    help="Select every subject this student is taking.",
                )
                submitted = st.form_submit_button("Register student & generate code(s)", type="primary")
                if submitted:
                    if not t_name.strip():
                        st.error("Enter student name.")
                    elif not t_subjects:
                        st.error("Select at least one subject.")
                    else:
                        photo_path = save_passport_photo(t_photo) if t_photo is not None else None
                        existing = {s.get("code", "").upper() for s in students}
                        created = []
                        for subj in t_subjects:
                            code = generate_access_code(existing)
                            existing.add(code.upper())
                            rec = {
                                "code": code,
                                "name": t_name.strip(),
                                "class": t_class.strip(),
                                "exam": subj,
                                "registered_at": datetime.now(timezone.utc).isoformat(),
                                "completed": False,
                                "started": False,
                            }
                            if photo_path:
                                rec["photo_path"] = photo_path
                            students.append(rec)
                            created.append((subj, code))
                        save_students(students)
                        st.session_state.students = students
                        codes_txt = ", ".join(f"{s}: **{c}**" for s, c in created)
                        st.success(
                            f"✅ Registered **{t_name.strip()}** for {len(created)} subject(s) — {codes_txt}"
                        )
                        st.rerun()

            if students:
                df = pd.DataFrame(students)
                if "photo_path" in df.columns:
                    df = df.copy()
                    df["photo"] = df["photo_path"].apply(lambda x: "Yes" if x else "")
                show_cols = [c for c in ["code", "name", "class", "exam", "started", "completed", "percent", "grade", "photo"] if c in df.columns]
                st.dataframe(df[show_cols], hide_index=True, use_container_width=True)
                st.download_button(
                    "Download student access codes (CSV)",
                    data=df.to_csv(index=False).encode("utf-8-sig"),
                    file_name="student_access_codes.csv",
                    mime="text/csv",
                    key="dl_student_codes",
                )
                reset_code = st.text_input(
                    "Reset a code (allow student retake)",
                    placeholder="Enter 8-character code to reset",
                    key="reset_code_input",
                )
                if st.button("Reset code", key="reset_code_btn"):
                    found = False
                    for s in students:
                        if s.get("code", "").upper() == (reset_code or "").strip().upper():
                            s["completed"] = False
                            s["started"] = False
                            s.pop("completed_at", None)
                            s.pop("mcq_score", None)
                            s.pop("percent", None)
                            s.pop("grade", None)
                            found = True
                            break
                    if found:
                        save_students(students)
                        st.session_state.students = students
                        st.success("Access code reset — student can now sit the exam again.")
                        st.rerun()
                    else:
                        st.error("Code not found in registry.")
            else:
                st.caption("No students registered yet.")

        # ---- Settings ----
        with st.expander("⚙️ Examination settings", expanded=False):
            new_pwd = st.text_input("New password", type="password", key="new_pwd")
            new_pwd2 = st.text_input("Confirm new password", type="password", key="new_pwd2")
            if st.button("Update password", key="update_pwd_btn"):
                if not new_pwd:
                    st.error("Password cannot be empty.")
                elif new_pwd != new_pwd2:
                    st.error("Passwords do not match.")
                else:
                    settings["password_hash"] = hash_password(new_pwd)
                    save_settings(settings)
                    st.session_state.settings = settings
                    st.success("Password updated.")

            default_dur = st.number_input(
                "Default duration (minutes, 0 = untimed)",
                min_value=0, max_value=300,
                value=int(settings.get("default_duration_minutes", 30)),
                key="default_duration_input",
            )
            if st.button("Save default duration", key="save_default_dur_btn"):
                settings["default_duration_minutes"] = int(default_dur)
                save_settings(settings)
                st.session_state.settings = settings
                st.success("Saved.")

            for exam_name in list(bank.keys()):
                current = int(
                    settings.get("exam_durations", {}).get(
                        exam_name, settings.get("default_duration_minutes", 30)
                    )
                )
                val = st.number_input(
                    f"Duration for «{exam_name}» (min)",
                    min_value=0, max_value=300, value=current, key=f"dur_{exam_name}",
                )
                if st.button(f"Save duration · {exam_name}", key=f"save_dur_{exam_name}"):
                    settings.setdefault("exam_durations", {})[exam_name] = int(val)
                    save_settings(settings)
                    st.session_state.settings = settings
                    st.success("Saved.")

            gb = settings.get("grade_boundaries", DEFAULT_SETTINGS["grade_boundaries"])
            gcols = st.columns(6)
            new_gb = {}
            for i, letter in enumerate(["A", "B", "C", "D", "E", "F"]):
                with gcols[i]:
                    new_gb[letter] = st.number_input(
                        letter, min_value=0, max_value=100,
                        value=int(gb.get(letter, 0)), key=f"gb_{letter}",
                    )
            if st.button("Save grade boundaries", key="save_grades_btn"):
                settings["grade_boundaries"] = new_gb
                save_settings(settings)
                st.session_state.settings = settings
                st.success("Saved.")

        # ---- Add MCQ ----
        with st.expander("➕ Add objective (MCQ) question", expanded=False):
            existing_names = list(bank.keys())
            exam_mode = st.radio(
                "Exam name", ["Choose existing exam", "Create new exam"],
                horizontal=True, key="mcq_exam_mode",
            )
            if exam_mode == "Choose existing exam" and existing_names:
                exam_name = st.selectbox("Exam", existing_names, key="mcq_existing")
            else:
                exam_name = st.text_input("New exam name", key="mcq_new")

            new_image_file = st.file_uploader(
                "Picture (optional)", type=["png", "jpg", "jpeg", "gif", "webp", "bmp"], key="mcq_img"
            )
            new_image_url = st.text_input("Or image URL", key="mcq_img_url")

            with st.form("mcq_form", clear_on_submit=True):
                question_text = st.text_area("Question")
                c1, c2 = st.columns(2)
                with c1:
                    option_a = st.text_input("Option A")
                    option_b = st.text_input("Option B")
                with c2:
                    option_c = st.text_input("Option C")
                    option_d = st.text_input("Option D")
                correct = st.selectbox("Correct answer", ["A", "B", "C", "D"])
                explanation = st.text_area("Explanation (optional)")
                if st.form_submit_button("Save MCQ", type="primary"):
                    if not (exam_name or "").strip():
                        st.error("Enter an exam name.")
                    elif not question_text.strip() or not all(
                        [option_a.strip(), option_b.strip(), option_c.strip(), option_d.strip()]
                    ):
                        st.error("Enter question and all four options.")
                    else:
                        new_q = {
                            "type": "mcq",
                            "question": question_text.strip(),
                            "options": {
                                "A": option_a.strip(), "B": option_b.strip(),
                                "C": option_c.strip(), "D": option_d.strip(),
                            },
                            "answer": correct,
                            "explanation": explanation.strip(),
                        }
                        path = save_uploaded_image(new_image_file)
                        if path:
                            new_q["image_path"] = path
                        if (new_image_url or "").strip():
                            new_q["image_url"] = new_image_url.strip()
                        bank.setdefault(exam_name.strip(), []).append(new_q)
                        save_bank(bank)
                        st.success("MCQ saved.")
                        st.rerun()

        # ---- Add theory ----
        with st.expander("📝 Add theory question", expanded=False):
            existing_names = list(bank.keys())
            th_mode = st.radio(
                "Exam name", ["Choose existing exam", "Create new exam"],
                horizontal=True, key="th_exam_mode",
            )
            if th_mode == "Choose existing exam" and existing_names:
                th_exam = st.selectbox("Exam", existing_names, key="th_existing")
            else:
                th_exam = st.text_input("New exam name", key="th_new")

            th_image_file = st.file_uploader(
                "Picture / diagram (optional)",
                type=["png", "jpg", "jpeg", "gif", "webp", "bmp"],
                key="th_img",
            )
            th_image_url = st.text_input("Or image URL", key="th_img_url")

            with st.form("theory_form", clear_on_submit=True):
                th_q = st.text_area("Theory question", height=120)
                th_note = st.text_area(
                    "Marking note / sample points (optional, for teachers)",
                    height=80,
                )
                if st.form_submit_button("Save theory question", type="primary"):
                    if not (th_exam or "").strip():
                        st.error("Enter an exam name.")
                    elif not th_q.strip():
                        st.error("Enter the theory question.")
                    else:
                        new_q = {
                            "type": "theory",
                            "question": th_q.strip(),
                            "options": {},
                            "answer": "",
                            "explanation": th_note.strip(),
                        }
                        path = save_uploaded_image(th_image_file)
                        if path:
                            new_q["image_path"] = path
                        if (th_image_url or "").strip():
                            new_q["image_url"] = th_image_url.strip()
                        bank.setdefault(th_exam.strip(), []).append(new_q)
                        save_bank(bank)
                        st.success("Theory question saved.")
                        st.rerun()

        # ---- Import ----
        with st.expander("📤 Import questions from CSV or Excel", expanded=False):
            st.markdown(
                "Required: `exam`, `question`. For MCQ also: `option_a`…`option_d`, `correct_answer`. "
                "Optional: `type` (`mcq` or `theory`), `explanation`, `image_url`."
            )
            uploaded = st.file_uploader("CSV / Excel", type=["csv", "xlsx", "xls"], key="import_file")
            import_mode = st.radio(
                "Import behaviour",
                ["Add questions to existing bank", "Replace questions for exams in the file"],
                key="import_mode",
            )
            if uploaded is not None:
                try:
                    if uploaded.name.lower().endswith(".csv"):
                        frame = pd.read_csv(uploaded, dtype=str).fillna("")
                    else:
                        frame = pd.read_excel(uploaded, dtype=str).fillna("")
                    frame.columns = [str(c).strip().lower() for c in frame.columns]
                    if "exam" not in frame.columns or "question" not in frame.columns:
                        st.error("Missing required columns: exam, question")
                    else:
                        st.dataframe(frame.head(8), use_container_width=True)
                        if st.button("Import", type="primary", key="import_questions_btn"):
                            imported = {}
                            errors = []
                            for row_number, (_, row) in enumerate(frame.iterrows(), start=2):
                                exam = str(row.get("exam", "")).strip()
                                if not exam:
                                    errors.append(f"Row {row_number}: blank exam.")
                                    continue
                                try:
                                    q = row_to_question(row)
                                    imported.setdefault(exam, []).append(q)
                                except ValueError as exc:
                                    errors.append(f"Row {row_number}: {exc}")
                            if errors:
                                st.error("Import problems:")
                                for e in errors[:20]:
                                    st.write(f"- {e}")
                            elif not imported:
                                st.error("No valid questions.")
                            else:
                                for exam, qs in imported.items():
                                    if import_mode.startswith("Replace"):
                                        bank[exam] = qs
                                    else:
                                        bank.setdefault(exam, []).extend(qs)
                                save_bank(bank)
                                total_q = sum(map(len, imported.values()))
                                exam_list = ", ".join(imported.keys())
                                st.success(
                                    f"✅ **Import successful!** Imported **{total_q}** question(s) "
                                    f"across **{len(imported)}** exam(s): {exam_list}."
                                )
                                st.balloons()
                                st.rerun()
                except Exception as exc:
                    st.error(f"Could not read file: {exc}")

        # ---- Question management (Collapsible Expander) ----
        with st.expander("📚 Question management", expanded=False):
            if not bank:
                st.info("Question bank is empty.")
            else:
                filter_exam = st.selectbox(
                    "Filter by exam", ["All exams"] + list(bank.keys()), key="mgmt_filter"
                )
                search_q = st.text_input("Search question text", key="mgmt_search")
                flat = []
                for ename, qs in bank.items():
                    if filter_exam != "All exams" and ename != filter_exam:
                        continue
                    for i, q in enumerate(qs):
                        if search_q and search_q.lower() not in q["question"].lower():
                            continue
                        flat.append((ename, i, q))
                st.caption(f"Showing {len(flat)} question(s)")
                for ename, q_idx, q in flat:
                    kind = "MCQ" if is_mcq(q) else "Theory"
                    pic = " 🖼" if resolve_image_source(q) else ""
                    with st.expander(
                        f"[{ename}] [{kind}] Q{q_idx + 1}: {q['question'][:70]}"
                        f"{'…' if len(q['question']) > 70 else ''}{pic}"
                    ):
                        st.write(q["question"])
                        show_question_image(q)
                        if is_mcq(q):
                            opts = q.get("options") or {}
                            st.write(
                                f"A. {opts.get('A','')} · B. {opts.get('B','')} · "
                                f"C. {opts.get('C','')} · D. {opts.get('D','')}"
                            )
                            st.write(f"**Correct:** {q.get('answer')}")
                        else:
                            st.caption("Theory question — students submit written answers.")
                        if q.get("explanation"):
                            st.caption(f"Guide: {q['explanation']}")
                        if st.button("🗑 Delete question", key=f"del_{ename}_{q_idx}"):
                            bank[ename].pop(q_idx)
                            if not bank[ename]:
                                del bank[ename]
                            save_bank(bank)
                            st.success("Question deleted.")
                            st.rerun()

                st.divider()
                st.markdown("**Question Bank Summary**")
                summary = pd.DataFrame(
                    [{"Exam": n, "Questions": len(qs)} for n, qs in bank.items()]
                )
                st.dataframe(summary, hide_index=True, use_container_width=True)
                export_df = questions_to_dataframe(bank)
                st.download_button(
                    "Download question bank (CSV)",
                    data=export_df.to_csv(index=False).encode("utf-8-sig"),
                    file_name="question_bank_export.csv",
                    mime="text/csv",
                    key="dl_question_bank",
                )

        # ---- Submissions (Theory Review & Scores) ----
        with st.expander("📥 Student submissions (theory review)", expanded=False):
            subs = load_submissions()
            if not subs:
                st.caption("No submissions recorded yet.")
            else:
                results_df = pd.DataFrame([
                    {
                        "Student": sub.get("name", ""),
                        "Class": sub.get("class", ""),
                        "Access Code": sub.get("code", ""),
                        "Examination": sub.get("exam", ""),
                        "Date Submitted": sub.get("submitted_at", ""),
                        "MCQ Score": f"{sub.get('mcq_score', 0)}/{sub.get('mcq_total', 0)}",
                        "Percentage": sub.get("percent", 0),
                        "Grade": sub.get("grade", ""),
                    }
                    for sub in subs
                ])
                st.markdown("**Recorded Results**")
                st.dataframe(results_df.iloc[::-1], hide_index=True, use_container_width=True)
                st.download_button(
                    "📥 Download all examination results (CSV)",
                    data=results_df.to_csv(index=False).encode("utf-8-sig"),
                    file_name="effortswill_exam_results.csv",
                    mime="text/csv",
                    key="dl_exam_results",
                )
                st.caption("Results save automatically on student submission or timer expiry.")
                for sub in reversed(subs[-50:]):
                    st.markdown(
                        f"**{sub.get('name')}** (`{sub.get('code')}`) · {sub.get('exam')} · "
                        f"{sub.get('submitted_at')} · MCQ {sub.get('mcq_score')}/{sub.get('mcq_total')} "
                        f"({sub.get('percent')}%) · Grade {sub.get('grade')}"
                    )
                    answers = sub.get("answers") or {}
                    exam_qs = bank.get(sub.get("exam"), [])
                    for i_str, ans in answers.items():
                        try:
                            i = int(i_str)
                        except ValueError:
                            continue
                        if i < len(exam_qs) and not is_mcq(exam_qs[i]):
                            st.write(f"**Theory Q{i + 1}:** {exam_qs[i]['question'][:120]}")
                            st.write(ans or "*[No answer submitted]*")
                    st.divider()

# ===========================================================================
# HELP & TEMPLATE
# ===========================================================================
with help_tab:
    st.subheader("Import format")
    template = pd.DataFrame(
        [
            {
                "exam": "Sample Exam",
                "type": "mcq",
                "question": "Which part is the brain of the computer?",
                "option_a": "Monitor",
                "option_b": "CPU",
                "option_c": "Keyboard",
                "option_d": "Mouse",
                "correct_answer": "B",
                "explanation": "CPU processes instructions.",
                "image_url": "",
            },
            {
                "exam": "Sample Exam",
                "type": "theory",
                "question": "Explain two differences between hardware and software.",
                "option_a": "",
                "option_b": "",
                "option_c": "",
                "option_d": "",
                "correct_answer": "",
                "explanation": "Hardware physical; software programs.",
                "image_url": "",
            },
        ]
    )
    st.dataframe(template, hide_index=True, use_container_width=True)
    st.download_button(
        "Download CSV template",
        data=template.to_csv(index=False).encode("utf-8-sig"),
        file_name="exam_question_template.csv",
        mime="text/csv",
        type="primary",
        key="dl_csv_template",
    )

    st.markdown(
        """
**Teacher-Controlled Access Codes Workflow**

1. The teacher logs into the **Teacher dashboard**.
2. Open **🎓 Student registrations & access codes**, enter student details, select subjects, and click **Register student & generate code(s)**.
3. The teacher hands the generated unique 8-character code (e.g. `A7K2M9QX`) to each student.
4. The student opens **Student exam**, types in their code, and sits their designated paper.
5. Upon submission, the code is marked completed so it cannot be reused without teacher authorization.

**Question Management & Theory**
- The **📚 Question management** tab is collapsed by default and opens on click.
- Objective (MCQ) questions are auto-graded immediately. Theory answers are saved for teacher marking under **Student submissions**.
"""
    )