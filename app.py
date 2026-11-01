"""
EFFORTSWILL ACADEMY CBT
Student registration + access codes, MCQ & theory questions, timer, marking.
"""

from __future__ import annotations

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

# ---------------------------------------------------------------------------
# Page & branding
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="EFFORTSWILL ACADEMY CBT",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Load branding assets (logo + low-opacity school photo background)
_ASSETS = Path(__file__).parent / "assets"
_LOGO_PATH = _ASSETS / "logo.jpeg"
_BG_PATH = _ASSETS / "background.jpeg"

def _img_to_data_uri(path: Path, mime: str = "image/jpeg") -> str:
    if not path.exists():
        return ""
    import base64
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"

_LOGO_URI = _img_to_data_uri(_LOGO_PATH)
_BG_URI = _img_to_data_uri(_BG_PATH)

# Apply the school photo as a persistent background. Keep Streamlit's
# structural containers transparent so they do not hide the image.
_bg_css = """
html, body, .stApp {
    min-height: 100%;
}
.stApp {
    min-height: 100vh !important;
    background-color: #eaf1f8 !important;
    background-image: url("BG_IMAGE_PLACEHOLDER") !important;
    background-size: cover !important;
    background-position: center 42% !important;
    background-repeat: no-repeat !important;
    background-attachment: fixed !important;
}
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > .main,
section.main {
    background: transparent !important;
}
[data-testid="stHeader"] {
    background: rgba(255, 255, 255, 0.55) !important;
    backdrop-filter: blur(4px);
}
.block-container {
    background: rgba(255, 255, 255, 0.48) !important;
    border: 1px solid rgba(255, 255, 255, 0.45) !important;
    border-radius: 12px !important;
    padding: 1.25rem 1.5rem !important;
    box-shadow: 0 4px 24px rgba(0,0,0,0.12) !important;
    backdrop-filter: blur(1.5px);
}
div[data-testid="stExpander"],
div[data-testid="stForm"],
.stTabs [data-baseweb="tab-panel"] {
    background: rgba(255, 255, 255, 0.90) !important;
    border-radius: 10px !important;
}
/* Keep text readable while allowing the school photo to remain visible. */
h1, h2, h3, h4, p, label, span, .stMarkdown, .stText {
    text-shadow: 0 0 1px rgba(255,255,255,0.8);
}
/* On phones, avoid fixed-background quirks and give the photo a stable crop. */
@media (max-width: 768px) {
    .stApp {
        background-attachment: scroll !important;
        background-position: center 38% !important;
        background-size: cover !important;
    }
    .block-container {
        background: rgba(255, 255, 255, 0.62) !important;
        padding: 1rem 0.8rem !important;
        backdrop-filter: none;
    }
}
"""
if _BG_URI:
    _bg_css = _bg_css.replace("BG_IMAGE_PLACEHOLDER", _BG_URI)
else:
    _bg_css = _bg_css.replace('background-image: url("BG_IMAGE_PLACEHOLDER") !important;', '')

st.markdown(
    f"""
    <style>
    {_bg_css}
    .cbt-question {
        font-size: 26px !important;
        font-weight: 700 !important;
        color: #000000 !important;
        line-height: 1.35;
        margin-bottom: 0.75rem;
    }
    .cbt-option, div[data-testid="stRadio"] label,
    div[data-testid="stRadio"] label p,
    div[data-testid="stRadio"] label span {
        font-size: 24px !important;
        color: #111111 !important;
        line-height: 1.4 !important;
    }
    div[data-testid="stHorizontalBlock"] div[data-testid="column"] button {
        padding: 0.12rem 0.2rem !important;
        min-height: 1.55rem !important;
        height: auto !important;
        font-size: 0.72rem !important;
        line-height: 1.15 !important;
        border-radius: 4px !important;
    }
    div[data-testid="stHorizontalBlock"] div[data-testid="column"] button p {
        font-size: 0.72rem !important;
        margin: 0 !important;
    }
    .cbt-brand {
        font-size: 1.75rem;
        font-weight: 800;
        color: #0b3d91;
        letter-spacing: -0.02em;
        margin-bottom: 0.15rem;
    }
    .cbt-sub { color: #444; font-size: 0.95rem; margin-bottom: 1rem; }
    .timer-box {
        background: #fff3cd; border: 2px solid #ffc107; border-radius: 8px;
        padding: 0.6rem 1rem; font-size: 1.25rem; font-weight: 700;
        color: #856404; text-align: center;
    }
    .timer-box.danger {
        background: #f8d7da; border-color: #dc3545; color: #721c24;
    }
    .results-sheet {
        border: 1px solid #333; padding: 1.5rem; background: #fff; color: #000;
        font-family: Georgia, "Times New Roman", serif;
    }
    .results-sheet h2 { margin-top: 0; color: #0b3d91; }
    .grade-badge {
        display: inline-block; padding: 0.35rem 0.9rem; border-radius: 6px;
        font-weight: 800; font-size: 1.4rem; background: #e8f5e9;
        color: #1b5e20; border: 2px solid #2e7d32;
    }
    .code-box {
        font-size: 1.6rem; font-weight: 800; letter-spacing: 0.12em;
        background: #e3f2fd; border: 2px dashed #0b3d91; border-radius: 8px;
        padding: 0.75rem 1.25rem; text-align: center; color: #0b3d91;
    }
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

# Science + Commercial subjects (students can tick any they wish to register for)
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
            "explanation": "The CPU processes instructions and controls many computer operations.",
        },
        {
            "type": "mcq",
            "question": "Which of these is an example of computer hardware?",
            "options": {
                "A": "Microsoft Word",
                "B": "Windows",
                "C": "Keyboard",
                "D": "Paint application",
            },
            "answer": "C",
            "explanation": "A keyboard is a physical component, so it is hardware.",
        },
        {
            "type": "theory",
            "question": "Explain two differences between hardware and software.",
            "options": {},
            "answer": "",
            "explanation": "Hardware is physical; software is programs/instructions.",
        },
    ],
}

DEFAULT_SETTINGS = {
    "password_hash": DEFAULT_PASSWORD_HASH,
    "exam_durations": {},
    "default_duration_minutes": 0,
    "grade_boundaries": {"A": 70, "B": 60, "C": 50, "D": 40, "E": 30, "F": 0},
    "require_student_code": True,  # students must login with a code
}


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------
def save_bank(bank: dict) -> None:
    BANK_FILE.write_text(json.dumps(bank, indent=2, ensure_ascii=False), encoding="utf-8")


def load_bank() -> dict:
    if BANK_FILE.exists():
        try:
            data = json.loads(BANK_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                # Ensure type field exists on older questions
                for qs in data.values():
                    for q in qs:
                        if "type" not in q:
                            q["type"] = "theory" if not q.get("options") else "mcq"
                return data
        except (json.JSONDecodeError, OSError):
            st.warning("The saved question bank could not be read. Using sample questions.")
    save_bank(DEFAULT_BANK)
    return json.loads(json.dumps(DEFAULT_BANK))


def save_settings(settings: dict) -> None:
    SETTINGS_FILE.write_text(json.dumps(settings, indent=2), encoding="utf-8")


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


def save_students(students: list) -> None:
    STUDENTS_FILE.write_text(json.dumps(students, indent=2, ensure_ascii=False), encoding="utf-8")


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
    """Generate a unique 8-character alphanumeric code."""
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


def questions_to_dataframe(bank: dict) -> pd.DataFrame:
    rows = []
    for exam, questions in bank.items():
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
    """Optional student passport photo → data/images/passports/."""
    return save_uploaded_image(uploaded_file, subfolder="passports")


def passport_data_uri(photo_path: str | None) -> str:
    """Return data-URI for embedding passport on results printout."""
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
    import base64
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


def show_question_image(q: dict, caption: str = "Question image") -> None:
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


def build_student_report_card_pdf(student_name: str, student_class: str, access_code: str,
                                  records: list[dict], class_position: str,
                                  class_size: int, average: float, remarks: str) -> bytes:
    """Create a printable PDF report card from saved examination records."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm,
                            topMargin=14*mm, bottomMargin=16*mm)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="SchoolTitle", parent=styles["Title"], alignment=1,
                              fontSize=18, leading=22, textColor=colors.HexColor("#17365D"), spaceAfter=3))
    styles.add(ParagraphStyle(name="ReportTitle", parent=styles["Heading2"], alignment=1,
                              fontSize=12, leading=15, textColor=colors.HexColor("#24527A"), spaceAfter=12))
    styles.add(ParagraphStyle(name="SmallCell", parent=styles["BodyText"], fontSize=8, leading=10))
    story = []
    if _LOGO_PATH.exists():
        try:
            logo = RLImage(str(_LOGO_PATH), width=19*mm, height=19*mm, kind="proportional")
            logo.hAlign = "CENTER"
            story.append(logo)
        except Exception:
            pass
    story.extend([Paragraph("EFFORTSWILL ACADEMY", styles["SchoolTitle"]),
                  Paragraph("STUDENT ACADEMIC REPORT CARD", styles["ReportTitle"])])
    info = [
        ["Student Name", student_name or "N/A", "Class", student_class or "N/A"],
        ["Access Code", access_code or "N/A", "Class Position", f"{class_position} of {class_size}" if class_position else "N/A"],
        ["Overall CBT Average", f"{average:.1f}%", "Examinations", str(len(records))],
    ]
    info_table = Table(info, colWidths=[31*mm, 58*mm, 31*mm, 54*mm])
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#EAF0F6")),
        ("BACKGROUND", (2,0), (2,-1), colors.HexColor("#EAF0F6")),
        ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"), ("FONTNAME", (2,0), (2,-1), "Helvetica-Bold"),
        ("GRID", (0,0), (-1,-1), .5, colors.HexColor("#AAB7C4")),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"), ("FONTSIZE", (0,0), (-1,-1), 8),
        ("TOPPADDING", (0,0), (-1,-1), 7), ("BOTTOMPADDING", (0,0), (-1,-1), 7),
    ]))
    story.extend([info_table, Spacer(1, 8*mm), Paragraph("EXAMINATION PERFORMANCE", styles["Heading3"])])
    rows = [["S/N", "Subject / Examination", "Date", "Score", "Grade"]]
    for i, item in enumerate(sorted(records, key=lambda r: str(r.get("submitted_at", ""))), 1):
        try:
            score = float(item.get("percent", 0) or 0)
        except (TypeError, ValueError):
            score = 0.0
        rows.append([str(i), str(item.get("exam", "")), str(item.get("submitted_at", ""))[:19], f"{score:.1f}%", str(item.get("grade", ""))])
    if len(rows) == 1:
        rows.append(["1", "No examination records", "", "", ""])
    result_table = Table(rows, repeatRows=1, colWidths=[12*mm, 67*mm, 43*mm, 25*mm, 25*mm])
    result_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#17365D")), ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"), ("GRID", (0,0), (-1,-1), .45, colors.HexColor("#AAB7C4")),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F3F6F9")]),
        ("FONTSIZE", (0,0), (-1,-1), 8), ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 7), ("BOTTOMPADDING", (0,0), (-1,-1), 7),
    ]))
    story.extend([result_table, Spacer(1, 8*mm), Paragraph("TEACHER'S REMARKS", styles["Heading3"])])
    safe_remarks = (remarks or "No remarks provided.").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")
    story.append(Paragraph(safe_remarks, styles["BodyText"]))
    story.extend([Spacer(1, 15*mm), Paragraph("______________________________                         ______________________________", styles["BodyText"]),
                  Paragraph("Class Teacher's Signature                                      Principal's Signature", styles["SmallCell"])])
    doc.build(story)
    return buffer.getvalue()


def remember_answer(widget_key: str, question_index: int) -> None:
    attempt = st.session_state.get("exam_attempt")
    selected = st.session_state.get(widget_key)
    if attempt is not None and selected in {"A", "B", "C", "D"}:
        attempt["answers"][question_index] = selected


def remember_theory(widget_key: str, question_index: int) -> None:
    attempt = st.session_state.get("exam_attempt")
    text = st.session_state.get(widget_key)
    if attempt is not None and text is not None:
        attempt["answers"][question_index] = str(text)


def find_student_by_code(students: list, code: str) -> dict | None:
    code = code.strip().upper()
    for s in students:
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
    st.session_state.student_session = None  # {code, name, class, exam}

bank = st.session_state.bank
settings = st.session_state.settings
students = st.session_state.students

_logo_html = (
    f'<img src="{_LOGO_URI}" alt="Effortswill Academy logo" '
    f'style="height:64px;width:auto;border-radius:8px;margin-right:12px;vertical-align:middle;" />'
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
    '<div class="cbt-sub">Purposefulness &amp; Dedication · Registration · access codes · MCQ &amp; theory</div>',
    unsafe_allow_html=True,
)

student_tab, teacher_tab, help_tab = st.tabs(
    ["🎓 Student exam", "👩‍🏫 Teacher dashboard", "ℹ️ Setup & template"]
)

# ===========================================================================
# STUDENT TAB — register / login with code / take exam
# ===========================================================================
with student_tab:
    require_code = settings.get("require_student_code", True)

    # ---- Not logged in ----
    if st.session_state.student_session is None:
        mode = st.radio(
            "Choose",
            ["Login with access code", "Register for an exam"],
            horizontal=True,
            key="stu_mode",
        )

        if mode.startswith("Login"):
            st.subheader("Student login")
            st.caption("Enter the access code given to you after registration.")
            login_code = st.text_input("Access code", key="login_code", placeholder="e.g. A7K2M9QX")
            if st.button("Log in", type="primary", key="student_login_btn"):
                stu = find_student_by_code(students, login_code or "")
                if not stu:
                    st.error("Invalid access code. Check the code or register first.")
                elif stu.get("completed"):
                    st.error(
                        f"This code was already used to complete **{stu.get('exam')}**. "
                        "Ask the teacher for a new registration if you need to retake."
                    )
                elif stu.get("exam") not in bank or not bank.get(stu.get("exam")):
                    st.error("The exam linked to this code is no longer available.")
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

        else:
            st.subheader("Student registration")
            st.caption(
                "Enter your details, optionally upload a passport photo, and tick all subjects "
                "you want to register for. You will receive a unique access code **per subject**."
            )
            reg_name = st.text_input("Full name *", key="reg_name")
            reg_class = st.text_input("Class / Form", key="reg_class", placeholder="e.g. SS2A")
            reg_photo = st.file_uploader(
                "Passport photograph (optional)",
                type=["png", "jpg", "jpeg", "webp"],
                key="reg_passport",
                help="Optional. Shown on your result printout if provided.",
            )
            if reg_photo is not None:
                st.image(reg_photo, caption="Passport preview", width=120)

            bank_exams = list(bank.keys()) if bank else []
            # Prefer predefined science + commercial list, then any extra bank exams
            subject_choices = list(dict.fromkeys(ALL_SUBJECTS + bank_exams))
            st.markdown("**Select subjects to register for** (tick all that apply):")
            col_sci, col_com = st.columns(2)
            with col_sci:
                st.caption("🔬 Science subjects")
                sci_selected = []
                for subj in SCIENCE_SUBJECTS:
                    if st.checkbox(subj, key=f"reg_sci_{subj}"):
                        sci_selected.append(subj)
            with col_com:
                st.caption("💼 Commercial subjects")
                com_selected = []
                for subj in COMMERCIAL_SUBJECTS:
                    if st.checkbox(subj, key=f"reg_com_{subj}"):
                        com_selected.append(subj)
            # Any bank exams not already in the fixed lists
            extra = [e for e in bank_exams if e not in ALL_SUBJECTS]
            extra_selected = []
            if extra:
                st.caption("📚 Other exams available in the bank")
                for subj in extra:
                    if st.checkbox(subj, key=f"reg_extra_{subj}"):
                        extra_selected.append(subj)

            selected_subjects = sci_selected + com_selected + extra_selected

            if st.button("Register and get access code(s)", type="primary", key="student_register_btn"):
                if not reg_name.strip():
                    st.error("Enter your full name.")
                elif not selected_subjects:
                    st.error("Tick at least one subject to register for.")
                else:
                    photo_path = save_passport_photo(reg_photo) if reg_photo is not None else None
                    existing = {s.get("code", "").upper() for s in students}
                    created = []
                    for subj in selected_subjects:
                        code = generate_access_code(existing)
                        existing.add(code.upper())
                        record = {
                            "code": code,
                            "name": reg_name.strip(),
                            "class": reg_class.strip(),
                            "exam": subj,
                            "registered_at": datetime.now(timezone.utc).isoformat(),
                            "completed": False,
                            "started": False,
                        }
                        if photo_path:
                            record["photo_path"] = photo_path
                        students.append(record)
                        created.append((subj, code))
                    save_students(students)
                    st.session_state.students = students
                    st.success(
                        f"✅ Registration successful! **{reg_name.strip()}** registered for "
                        f"**{len(created)}** subject(s). Save your access code(s) below."
                    )
                    for subj, code in created:
                        st.markdown(
                            f"**{subj}**  \n"
                            f'<div class="code-box">{code}</div>',
                            unsafe_allow_html=True,
                        )
                    st.info(
                        "Use **Login with access code** and enter the code for the subject you want to sit. "
                        "Each code is for one student and one exam sitting."
                    )

    # ---- Logged in ----
    else:
        sess = st.session_state.student_session
        chosen_exam = sess["exam"]
        if chosen_exam not in bank or not bank[chosen_exam]:
            st.error("Exam not available.")
            if st.button("Log out", key="student_logout_no_exam"):
                st.session_state.student_session = None
                st.session_state.exam_attempt = None
                st.rerun()
        else:
            questions = bank[chosen_exam]
            duration_min = settings.get("exam_durations", {}).get(
                chosen_exam, settings.get("default_duration_minutes", 0)
            )
            top_l, top_r = st.columns([4, 1])
            with top_l:
                st.write(
                    f"**{sess['name']}**"
                    + (f" · {sess['class']}" if sess.get("class") else "")
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
                    "duration_seconds": duration_min * 60 if duration_min else 0,
                    "student_name": sess["name"],
                    "student_class": sess.get("class", ""),
                    "auto_submitted": False,
                }

            attempt = st.session_state.exam_attempt
            if len(attempt["order"]) != len(questions):
                attempt["order"] = list(range(len(questions)))
                attempt["index"] = 0
                st.session_state.exam_attempt = attempt

            # Start
            if attempt["started_at"] is None and not attempt["finished"]:
                n_mcq = sum(1 for q in questions if is_mcq(q))
                n_th = len(questions) - n_mcq
                st.info(
                    f"**{chosen_exam}** — {len(questions)} question(s) "
                    f"({n_mcq} objective, {n_th} theory)"
                    + (f" · Time: **{duration_min} min**" if duration_min else " · No time limit")
                )
                if st.button("▶ Start exam", type="primary", use_container_width=True, key="start_exam_btn"):
                    attempt["started_at"] = datetime.now(timezone.utc).isoformat()
                    attempt["duration_seconds"] = duration_min * 60 if duration_min else 0
                    # Mark student as started
                    for s in students:
                        if s.get("code") == sess["code"]:
                            s["started"] = True
                            break
                    save_students(students)
                    st.session_state.students = students
                    st.rerun()

            elif not attempt["finished"]:
                remaining_seconds = None
                if attempt["duration_seconds"] > 0 and attempt["started_at"]:
                    started = datetime.fromisoformat(attempt["started_at"])
                    elapsed = (datetime.now(timezone.utc) - started).total_seconds()
                    remaining_seconds = max(0, attempt["duration_seconds"] - elapsed)
                    if remaining_seconds <= 0:
                        attempt["finished"] = True
                        attempt["auto_submitted"] = True
                        st.rerun()

                if remaining_seconds is not None:
                    mins, secs = divmod(int(remaining_seconds), 60)
                    danger = remaining_seconds < 60
                    cls = "timer-box danger" if danger else "timer-box"
                    st.markdown(
                        f'<div class="{cls}">⏱ Time remaining: {mins:02d}:{secs:02d}</div>',
                        unsafe_allow_html=True,
                    )
                    if remaining_seconds > 0:
                        if st.button("🔄 Refresh timer", key="refresh_timer"):
                            st.rerun()

                total_questions = len(questions)
                idx = attempt["index"]
                q_index = attempt["order"][idx]
                q = questions[q_index]

                st.caption("**Navigator** · ● current · ✓ answered · number = not answered")
                for row_start in range(0, total_questions, 10):
                    cols = st.columns(10)
                    for offset, col in enumerate(cols):
                        n = row_start + offset
                        if n >= total_questions:
                            continue
                        if n == idx:
                            label, kind = f"●{n + 1}", "primary"
                        elif n in attempt["answers"] and str(attempt["answers"].get(n, "")).strip():
                            label, kind = f"✓{n + 1}", "secondary"
                        else:
                            label, kind = f"{n + 1}", "secondary"
                        with col:
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

                qtype_label = "Objective (MCQ)" if is_mcq(q) else "Theory"
                st.markdown(f"**Question {idx + 1} of {total_questions}** · _{qtype_label}_")
                st.markdown(f'<div class="cbt-question">{q["question"]}</div>', unsafe_allow_html=True)
                show_question_image(q)

                if is_mcq(q):
                    answer_key = f"ans_mcq_{sess['code']}_{q_index}"
                    options = ["A", "B", "C", "D"]
                    opts_map = q.get("options") or {}
                    # Seed once only — do not pass index= when using key= (avoids state errors)
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
                    st.warning(f"{unanswered} question(s) unanswered.")
                if st.button("Submit exam", use_container_width=True, key="submit_btn"):
                    if unanswered:
                        st.session_state["confirm_submit"] = True
                    else:
                        attempt["finished"] = True
                        st.rerun()
                if st.session_state.get("confirm_submit"):
                    st.warning("Some questions are unanswered. Submit anyway?")
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
                    st.warning("Time expired — exam was submitted automatically.")

                st.success("Exam completed!")
                a, b, c, d = st.columns(4)
                a.metric("MCQ score", f"{score}/{total_mcq}" if total_mcq else "N/A")
                b.metric("Percentage", f"{percent:.1f}%" if total_mcq else "—")
                c.metric("Grade", grade)
                d.metric("Theory Qs", len(theory_indices))

                # Mark code completed + store submission (once only)
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

                # The result is written to data/submissions.json immediately after
                # submission, without requiring the student to press another button.
                if attempt.get("result_saved") or st.session_state.get(save_key):
                    st.success("Result automatically saved. Your teacher can view it in the Teacher Dashboard.")

                st.markdown("### 📄 Results sheet")
                # Resolve passport photo for this student (if any)
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
                  <p style="font-size:0.85rem; color:#555;">Theory answers are saved for teacher review.</p>
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
                            status = "✅ Correct" if ok else ("❌ Failed" if user_answer else "○ Not answered")
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
                                st.caption(f"Marking note: {q['explanation']}")
                        st.divider()

                st.info("Your access code is now marked as **used**. Log out when finished.")
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

        # ---- Students & codes ----
        with st.expander("🎓 Student registrations & access codes", expanded=True):
            st.markdown(
                "Register a student for one or more subjects (generates a unique code per subject) "
                "or manage existing codes. Passport photo is optional."
            )
            bank_exams = list(bank.keys()) if bank else []
            subject_choices = list(dict.fromkeys(ALL_SUBJECTS + bank_exams))
            with st.form("teacher_reg_form", clear_on_submit=True):
                t_name = st.text_input("Student full name *")
                t_class = st.text_input("Class / Form")
                t_photo = st.file_uploader(
                    "Passport photograph (optional)",
                    type=["png", "jpg", "jpeg", "webp"],
                    key="teacher_reg_passport",
                )
                st.markdown("**Subjects to register** (select all that apply):")
                t_subjects = st.multiselect(
                    "Science & commercial subjects",
                    options=subject_choices,
                    default=[],
                    key="teacher_reg_subjects",
                    help="Tick every subject this student should sit.",
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
                    "Download student codes (CSV)",
                    data=df.to_csv(index=False).encode("utf-8-sig"),
                    file_name="student_access_codes.csv",
                    mime="text/csv",
                    key="dl_student_codes",
                )
                reset_code = st.text_input(
                    "Reset a code (allow retake)",
                    placeholder="Enter code to reset",
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
                        st.success("Code reset — student can sit again.")
                        st.rerun()
                    else:
                        st.error("Code not found.")
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
                "Default duration (minutes, 0 = no limit)",
                min_value=0, max_value=300,
                value=int(settings.get("default_duration_minutes", 0)),
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
                        exam_name, settings.get("default_duration_minutes", 0)
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
                # Keys omitted inside form — Streamlit scopes form widgets by form id
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
        with st.expander("📝 Add theory question", expanded=True):
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
        st.divider()
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
                                    f"✅ **CSV / Excel import successful!**  \n"
                                    f"Imported **{total_q}** question(s) across "
                                    f"**{len(imported)}** exam(s): {exam_list}."
                                )
                                st.balloons()
                                st.info(
                                    "Questions are now in the bank. Students can register for these exams "
                                    "and sit them with their access codes."
                                )
                                st.rerun()
                except Exception as exc:
                    st.error(f"Could not read file: {exc}")

        # ---- Question management ----
        st.divider()
        st.subheader("📚 Question management")
        if not bank:
            st.info("Question bank is empty.")
        else:
            filter_exam = st.selectbox(
                "Filter by exam", ["All exams"] + list(bank.keys()), key="mgmt_filter"
            )
            search_q = st.text_input("Search", key="mgmt_search")
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
                        st.caption("Theory question — students type a free answer.")
                    if q.get("explanation"):
                        st.caption(q["explanation"])
                    if st.button("🗑 Delete", key=f"del_{ename}_{q_idx}"):
                        bank[ename].pop(q_idx)
                        if not bank[ename]:
                            del bank[ename]
                        save_bank(bank)
                        st.success("Deleted.")
                        st.rerun()

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

        # ---- Submissions (theory review) ----
        st.divider()
        with st.expander("📥 Student submissions (theory review)", expanded=False):
            subs = load_submissions()
            if not subs:
                st.caption("No submissions yet.")
            else:
                # ---- School-wide performance analytics ----
                st.markdown("### 📊 School-wide performance analytics")
                analytics_df = pd.DataFrame([
                    {
                        "Student": sub.get("name", "Unknown student"),
                        "Class": sub.get("class", "Class not set"),
                        "Access Code": sub.get("code", ""),
                        "Examination": sub.get("exam", "Unknown examination"),
                        "Date": sub.get("submitted_at", ""),
                        "Score": float(sub.get("percent", 0) or 0),
                        "Grade": sub.get("grade", ""),
                    }
                    for sub in subs
                ])
                analytics_df["Score"] = pd.to_numeric(analytics_df["Score"], errors="coerce").fillna(0)
                total_attempts = len(analytics_df)
                unique_students = analytics_df["Access Code"].replace("", pd.NA).dropna().nunique()
                if not unique_students:
                    unique_students = analytics_df["Student"].nunique()
                overall_average = round(float(analytics_df["Score"].mean()), 1)
                school_best = round(float(analytics_df["Score"].max()), 1)
                k1, k2, k3, k4 = st.columns(4)
                k1.metric("Exam attempts", total_attempts)
                k2.metric("Students", int(unique_students))
                k3.metric("School average", f"{overall_average}%")
                k4.metric("Highest score", f"{school_best}%")

                # Use access code as the student key to avoid merging students with similar names.
                analytics_df["Student Key"] = analytics_df["Access Code"].where(
                    analytics_df["Access Code"].astype(str).str.strip() != "",
                    analytics_df["Student"],
                )
                student_summary = (
                    analytics_df.groupby(["Student Key", "Student", "Class"], dropna=False)
                    .agg(Examinations=("Score", "count"), Average=("Score", "mean"), Best=("Score", "max"))
                    .reset_index()
                )
                student_summary["Average"] = student_summary["Average"].round(1)
                student_summary["Best"] = student_summary["Best"].round(1)
                student_summary = student_summary.sort_values(
                    ["Average", "Best", "Student"], ascending=[False, False, True]
                )

                class_summary = (
                    analytics_df.groupby("Class", dropna=False)
                    .agg(ExamAttempts=("Score", "count"), Students=("Student Key", "nunique"), Average=("Score", "mean"))
                    .reset_index()
                    .sort_values("Average", ascending=False)
                )
                class_summary["Average"] = class_summary["Average"].round(1)
                exam_summary = (
                    analytics_df.groupby("Examination", dropna=False)
                    .agg(Attempts=("Score", "count"), Average=("Score", "mean"), Highest=("Score", "max"))
                    .reset_index()
                    .sort_values("Average", ascending=False)
                )
                exam_summary[["Average", "Highest"]] = exam_summary[["Average", "Highest"]].round(1)

                ana_tab1, ana_tab2, ana_tab3 = st.tabs(
                    ["🏆 Student rankings", "🏫 Class performance", "📚 Examination analysis"]
                )
                with ana_tab1:
                    st.caption("Rankings are based on each student's average percentage across recorded exam attempts.")
                    ranking = student_summary.drop(columns=["Student Key"]).copy()
                    ranking.insert(0, "Rank", range(1, len(ranking) + 1))
                    st.dataframe(ranking, hide_index=True, use_container_width=True)
                    if not ranking.empty:
                        st.bar_chart(ranking.set_index("Student")["Average"])
                with ana_tab2:
                    st.caption("Class averages use all recorded examination attempts in each class.")
                    st.dataframe(class_summary, hide_index=True, use_container_width=True)
                    if not class_summary.empty:
                        st.bar_chart(class_summary.set_index("Class")["Average"])
                with ana_tab3:
                    st.caption("Examination averages are calculated from saved student results.")
                    st.dataframe(exam_summary, hide_index=True, use_container_width=True)
                    if not exam_summary.empty:
                        st.bar_chart(exam_summary.set_index("Examination")["Average"])
                st.download_button(
                    "📥 Download school analytics (CSV)",
                    data=student_summary.drop(columns=["Student Key"]).to_csv(index=False).encode("utf-8-sig"),
                    file_name="effortswill_school_performance_analytics.csv",
                    mime="text/csv",
                    key="dl_school_analytics",
                )

                # A compact results register plus CSV export for school records.
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
                st.markdown("**Saved examination results**")
                st.dataframe(results_df.iloc[::-1], hide_index=True, use_container_width=True)
                st.download_button(
                    "📥 Download all examination results (CSV)",
                    data=results_df.to_csv(index=False).encode("utf-8-sig"),
                    file_name="effortswill_exam_results.csv",
                    mime="text/csv",
                    key="dl_exam_results",
                )
                st.caption("Results are saved automatically when a student submits or the exam timer expires.")

                # ---- Individual student performance history ----
                st.markdown("### 🔎 Individual student performance history")
                history_query = st.text_input(
                    "Search by student name, class, or access code",
                    key="student_history_search",
                    placeholder="Type a student's name, class, or access code...",
                ).strip().casefold()
                matching_subs = [
                    sub for sub in subs
                    if not history_query or any(
                        history_query in str(sub.get(field, "")).casefold()
                        for field in ("name", "class", "code")
                    )
                ]
                if not matching_subs:
                    st.info("No student examination history matches that search.")
                else:
                    # Group by the student's stable access code where available.
                    student_keys = {}
                    for sub in matching_subs:
                        key = str(sub.get("code") or sub.get("name") or "Unknown student")
                        student_keys.setdefault(key, {
                            "label": f"{sub.get('name', 'Unknown student')} · "
                                     f"{sub.get('class', 'Class not set')} · {key}",
                            "records": [],
                        })["records"].append(sub)
                    selected_key = st.selectbox(
                        "Select student to view full examination history",
                        options=list(student_keys.keys()),
                        format_func=lambda key: student_keys[key]["label"],
                        key="student_history_selected",
                    )
                    history = sorted(
                        student_keys[selected_key]["records"],
                        key=lambda item: str(item.get("submitted_at", "")),
                        reverse=True,
                    )
                    history_df = pd.DataFrame([
                        {
                            "Examination": item.get("exam", ""),
                            "Date": item.get("submitted_at", ""),
                            "MCQ Score": f"{item.get('mcq_score', 0)}/{item.get('mcq_total', 0)}",
                            "Percentage": f"{item.get('percent', 0)}%",
                            "Grade": item.get("grade", ""),
                        }
                        for item in history
                    ])
                    avg_percent = round(
                        sum(float(item.get("percent", 0) or 0) for item in history) / len(history), 1
                    )
                    best_percent = max(float(item.get("percent", 0) or 0) for item in history)
                    metric1, metric2, metric3 = st.columns(3)
                    metric1.metric("Examinations taken", len(history))
                    metric2.metric("Average score", f"{avg_percent}%")
                    metric3.metric("Best score", f"{best_percent}%")
                    st.dataframe(history_df, hide_index=True, use_container_width=True)
                    st.download_button(
                        "📥 Download this student's history (CSV)",
                        data=history_df.to_csv(index=False).encode("utf-8-sig"),
                        file_name="student_performance_history.csv",
                        mime="text/csv",
                        key="dl_one_student_history",
                    )

                    # ---- Printable student report card ----
                    st.markdown("### 🧾 Printable student report card")
                    selected_records = student_keys[selected_key]["records"]
                    selected_name = str(selected_records[0].get("name", "Unknown student"))
                    selected_class = str(selected_records[0].get("class", "Class not set"))
                    selected_code = str(selected_records[0].get("code", ""))
                    selected_average = round(sum(float(item.get("percent", 0) or 0)
                                                  for item in selected_records) / len(selected_records), 1)
                    peer_averages = {}
                    for record in subs:
                        if str(record.get("class", "Class not set")) != selected_class:
                            continue
                        peer_key = str(record.get("code") or record.get("name") or "Unknown student")
                        peer_averages.setdefault(peer_key, []).append(float(record.get("percent", 0) or 0))
                    ordered_peers = sorted(((key, sum(values) / len(values)) for key, values in peer_averages.items()),
                                           key=lambda item: item[1], reverse=True)
                    student_identity = selected_code or selected_name
                    position = next((i for i, (key, _) in enumerate(ordered_peers, 1)
                                     if key == student_identity), None)
                    position_text = str(position) if position is not None else "N/A"
                    remarks_default = ("Excellent performance. Keep up the good work." if selected_average >= 70 else
                                       "Good effort. Continue to practise and aim higher." if selected_average >= 50 else
                                       "More consistent study and practice are encouraged.")
                    teacher_remarks = st.text_area("Teacher's remarks (editable before printing)",
                                                   value=remarks_default, key=f"report_remarks_{selected_key}")
                    report_pdf = build_student_report_card_pdf(selected_name, selected_class, selected_code,
                                                               selected_records, position_text, len(ordered_peers),
                                                               selected_average, teacher_remarks)
                    safe_student = re.sub(r"[^A-Za-z0-9_-]+", "_", selected_name).strip("_") or "student"
                    st.download_button("🖨️ Download printable report card (PDF)", data=report_pdf,
                                        file_name=f"{safe_student}_report_card.pdf", mime="application/pdf",
                                        key=f"dl_report_card_{selected_key}")
                    st.caption("Class position is calculated from each student's average across saved CBT examinations in the same class.")

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
                            st.write(f"**Theory Q{i + 1}:** {exam_qs[i]['question'][:100]}")
                            st.write(ans or "*blank*")
                    st.divider()

# ===========================================================================
# HELP
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
**Student registration & access codes**

1. Student opens **Student exam** → **Register for an exam** (or teacher registers them).
2. A unique **8-character access code** is generated (e.g. `A7K2M9QX`).
3. Student chooses **Login with access code**, enters the code, and can only sit **that** registered exam.
4. After submission, the code is marked **used** (cannot sit again unless the teacher resets it).

**Theory questions**

- Teacher dashboard → **Add theory question** (or CSV with `type=theory`).
- Students type free-text answers. MCQ is auto-marked; theory is saved for teacher review under *Student submissions*.

**Data files**

- `data/question_bank.json` — questions  
- `data/students.json` — registrations & codes  
- `data/submissions.json` — completed scripts  
- `data/settings.json` — password, timers, grades  
- `data/images/` — uploaded pictures  

Default teacher password: **teacher123**
"""
    )
