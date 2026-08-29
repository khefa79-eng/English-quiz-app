import streamlit as st
import json
import os
import string
import re
import time
import urllib.parse
from datetime import datetime
from PIL import Image
import pandas as pd
from google import genai
from google.genai import types

st.set_page_config(
    page_title="Mrs. Kheffa Eletreby | English Assessments",
    page_icon="📝",
    layout="centered"
)

st.markdown("""
    <style>
    .main-title-box {
        background: linear-gradient(135deg, #1E3A8A, #3B82F6);
        padding: 20px 15px;
        border-radius: 14px;
        color: white;
        margin-bottom: 22px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.12);
        text-align: center;
    }
    .main-title-box h2 { font-size: 1.45rem; margin: 0; font-weight: 700; }
    .main-title-box h3 { font-size: 1.15rem; margin: 6px 0; color: #E0E7FF; font-weight: 600; }
    .main-title-box p { font-size: 0.95rem; margin: 0; color: #DBEAFE; }
    .stRadio label, .stSelectbox label, .stTextInput label { font-size: 1.05rem !important; font-weight: 600 !important; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; font-weight: bold; font-size: 1.05rem; }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="main-title-box">
        <h2>🎓 English Assessment Platform</h2>
        <h3>Mrs. Kheffa Eletreby</h3>
        <p>Online English Teacher | 📱 WhatsApp: <b>01090570624</b></p>
    </div>
""", unsafe_allow_html=True)

EXAM_STORAGE_FILE = "current_exam.json"
SUBMISSIONS_FILE = "submitted_students.json"

def save_exam_to_disk(title, questions):
    data = {"title": title, "questions": questions}
    with open(EXAM_STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_exam_from_disk():
    if os.path.exists(EXAM_STORAGE_FILE):
        try:
            with open(EXAM_STORAGE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None

def load_submissions():
    if os.path.exists(SUBMISSIONS_FILE):
        try:
            with open(SUBMISSIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def clean_text_for_grading(text):
    if not text:
        return ""
    text = text.translate(str.maketrans('', '', string.punctuation + '؟،؛«»ـ'))
    text = text.lower()
    return " ".join(text.split())

def record_submission(student_name, student_phone, student_grade, score, total, percentage):
    submissions = load_submissions()
    clean_phone = re.sub(r'\D', '', student_phone)
    key_id = clean_phone if clean_phone else clean_text_for_grading(student_name)
    submissions[key_id] = {
        "full_name": student_name.strip(),
        "phone": student_phone.strip(),
        "grade": student_grade.strip(),
        "score": score,
        "total": total,
        "percentage": percentage,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(SUBMISSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(submissions, f, ensure_ascii=False, indent=2)

def extract_json_safely(raw_text):
    match = re.search(r'\[.*\]', raw_text, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    cleaned = raw_text.replace("```json", "").replace("
