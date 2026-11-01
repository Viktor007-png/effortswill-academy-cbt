# EFFORTSWILL ACADEMY CBT

Streamlit computer-based testing for **Effortswill Academy**  
*Purposefulness & Dedication*

## Features

| Feature | Description |
|--------|-------------|
| 🎓 Student registration | Tick science & commercial subjects; optional passport photo; unique code per subject |
| 📷 Passport on results | Optional photo appears on printable exam result sheet |
| 🔐 Access-code login | Only that student can sit the exam they registered for |
| 📝 MCQ + theory | Objective (A–D) and theory (typed) questions |
| 🖼 Picture questions | Upload or link diagrams |
| ⏱️ Exam timer | Teacher sets duration; auto-submit when time ends |
| 👩‍🏫 Teacher dashboard | Password-protected (default: `teacher123`) |
| 📊 Auto marking | MCQ score, %, grade; theory saved for review |
| 📄 Printable results | Student details, score, grade, date |

## Student flow

1. **Register for an exam** → save the **access code**
2. **Login with access code** → start only that exam
3. Submit → code is marked used (teacher can reset for a retake)

## Teacher flow

1. Log in (password `teacher123`) — change it under Settings  
2. Add MCQ and/or theory questions (or import CSV)  
3. Register students or let them self-register  
4. Share codes; review theory under *Student submissions*

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## CSV columns

`exam, type, question, option_a, option_b, option_c, option_d, correct_answer, explanation, image_url`

- `type`: `mcq` or `theory`  
- For theory, leave options and correct_answer blank  

## Data files

- `data/question_bank.json` — questions  
- `data/students.json` — registrations & codes  
- `data/submissions.json` — completed scripts  
- `data/settings.json` — password, timers, grades  
- `data/images/` — uploaded pictures  
- `assets/` — logo & background  


## Individual student performance history
The teacher dashboard includes a searchable student performance history. Search by student name, class, or access code, select a student, and review all saved examination attempts, average score, best score, and a downloadable CSV record. Results continue to be saved automatically to `data/submissions.json`.
