import streamlit as st
import json
import os
import string
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta, date
import pandas as pd
import pypdf

try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

st.set_page_config(
    page_title="Mrs. Kheffa Eletreby | English Assessments",
    page_icon="📝",
    layout="wide"
)

EGYPT_TIMEZONE = timezone(timedelta(hours=3))
ACADEMIC_START_DATE = date(2026, 8, 29)

EXAM_API_URL = "https://script.google.com/macros/s/AKfycbxK81pBCL75pIssvIQEqvCTvVqVMead9ro3hT9RrnLi8a067MIcPQkelESJaCaLrcPM/exec"
SUBMISSION_API_URL = "https://script.google.com/macros/s/AKfycbwCg2s41mVVD3Uo3A3c8dFhFQY1bS12OaAJ7vcZ-HhIhQ-X7LNPvWbhqi0Lhn0mFS-bmw/exec"

st.markdown("""
    <style>
    .main-title-box {
        background: linear-gradient(135deg, #1E3A8A, #3B82F6);
        padding: 22px 15px;
        border-radius: 14px;
        color: white;
        margin-bottom: 22px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.12);
        text-align: center;
    }
    .main-title-box h2 { font-size: 1.7rem; margin: 0; font-weight: 800; }
    .main-title-box h3 { font-size: 1.25rem; margin: 6px 0; color: #E0E7FF; font-weight: 600; }
    .main-title-box p { font-size: 1rem; margin: 0; color: #DBEAFE; }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        width: 100%;
        display: flex;
        flex-wrap: wrap;
    }
    .stTabs [data-baseweb="tab"] {
        flex-grow: 1;
        background-color: #F8FAFC;
        border-radius: 8px;
        padding: 10px 16px;
        font-weight: bold;
        border: 1px solid #CBD5E1;
    }
    .stTabs [aria-selected="true"] {
        background-color: #EFF6FF !important;
        border: 2px solid #3B82F6 !important;
        color: #1E40AF !important;
    }

    .grade-focus-header {
        background-color: #EFF6FF;
        border: 2.5px solid #3B82F6;
        border-radius: 10px;
        padding: 14px 18px;
        margin: 15px 0;
        color: #1E40AF;
    }
    .student-gate-box {
        background-color: #FEF3C7;
        border: 2px dashed #F59E0B;
        padding: 14px;
        border-radius: 10px;
        margin-bottom: 16px;
        color: #92400E;
        font-size: 0.95rem;
        font-weight: 600;
        line-height: 1.6;
    }
    .card-active {
        background: #F0FDF4;
        border: 2.5px solid #22C55E;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 16px;
        box-shadow: 0 3px 8px rgba(34,197,94,0.12);
    }
    .card-idle {
        background: #F8FAFC;
        border: 1.5px solid #CBD5E1;
        border-right: 6px solid #64748B;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 16px;
    }
    .badge-active {
        background-color: #16A34A;
        color: white;
        padding: 5px 14px;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 700;
    }
    .badge-idle {
        background-color: #64748B;
        color: white;
        padding: 5px 14px;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 600;
    }
    .grade-badge-title {
        background: #1E3A8A;
        color: white;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 1rem;
        font-weight: 800;
        margin-left: 6px;
        display: inline-block;
    }
    .passage-box {
        background-color: #F8FAFC;
        border-left: 5px solid #3B82F6;
        padding: 18px;
        border-radius: 8px;
        margin-bottom: 18px;
        font-size: 1.05rem;
        line-height: 1.7;
        color: #1E293B;
    }
    .word-box-header {
        background-color: #EEF2FF;
        border: 2px dashed #6366F1;
        padding: 12px;
        border-radius: 10px;
        margin: 12px 0 18px 0;
        text-align: center;
        font-size: 1.1rem;
        font-weight: 700;
        color: #312E81;
    }
    .stButton>button { width: 100%; border-radius: 8px; height: 2.8em; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="main-title-box">
        <h2>🎓 English Assessment Platform</h2>
        <h3>Mrs. Kheffa Eletreby</h3>
        <p>Senior English Teacher | 📱 WhatsApp: <b>01090570624</b></p>
    </div>
""", unsafe_allow_html=True)

ACTIVE_GRADES_FILE = "active_by_grade.json"

GRADES_MAP = {
    "p1": "Primary 1 - Connect (أولى ابتدائي - عادي)",
    "p2": "Primary 2 - Connect (تانية ابتدائي - عادي)",
    "p3": "Primary 3 - Connect (تالتة ابتدائي - عادي)",
    "p3_plus": "Primary 3 - Connect Plus (تالتة ابتدائي - بلس)",
    "p4": "Primary 4 - Connect (رابعة ابتدائي - عادي)",
    "p4_plus": "Primary 4 - Connect Plus (رابعة ابتدائي - بلس)",
    "p5": "Primary 5 - Connect (خامسة ابتدائي - عادي)",
    "p5_plus": "Primary 5 - Connect Plus (خامسة ابتدائي - بلس)",
    "p6": "Primary 6 - Connect (سادسة ابتدائي - عادي)",
    "p6_plus": "Primary 6 - Connect Plus (سادسة ابتدائي - بلس)",
    "prep1": "Prep 1 (أولى إعدادي)",
    "prep2": "Prep 2 (تانية إعدادي)",
    "prep3": "Prep 3 (تالتة إعدادي)",
    "sec1": "Secondary 1 (أولى ثانوي)",
    "sec2": "Secondary 2 (تانية ثانوي)",
    "sec3": "Secondary 3 (ثالثة ثانوي)"
}

GRADES_LIST = list(GRADES_MAP.values())

def get_current_egypt_time():
    return datetime.now(timezone.utc).astimezone(EGYPT_TIMEZONE).strftime("%Y-%m-%d | %I:%M %p")

def clean_time_display(date_str):
    if not date_str:
        return ""
    date_str = str(date_str).strip()
    if "|" in date_str and ("AM" in date_str or "PM" in date_str):
        return date_str
    for p in ["%H:%M %d-%m-%Y", "%d-%m-%Y %H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"]:
        try:
            dt = datetime.strptime(date_str, p)
            return (dt + timedelta(hours=3)).strftime("%Y-%m-%d | %I:%M %p")
        except ValueError:
            continue
    return date_str

def extract_date_obj(date_str):
    if not date_str:
        return None
    cleaned = clean_time_display(date_str)
    try:
        raw_d = cleaned.split("|")[0].strip()
        return datetime.strptime(raw_d, "%Y-%m-%d").date()
    except Exception:
        return None

def calculate_custom_academic_week(sub_date):
    if not sub_date:
        return "Week 1 (من 2026-08-29 إلى 2026-09-04)", 1
    days_diff = (sub_date - ACADEMIC_START_DATE).days
    if days_diff < 0:
        week_num = 1
    else:
        week_num = (days_diff // 7) + 1
    start_of_week = ACADEMIC_START_DATE + timedelta(days=(week_num - 1) * 7)
    end_of_week = start_of_week + timedelta(days=6)
    label = f"Week {week_num} (من {start_of_week.strftime('%Y-%m-%d')} إلى {end_of_week.strftime('%Y-%m-%d')})"
    return label, week_num

def load_exam_bank():
    try:
        req = urllib.request.Request(EXAM_API_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data and isinstance(data, dict):
                return data
    except Exception:
        pass
    return {}

def save_exam_to_sheet(exam_id, grade, exam_data, created_at):
    try:
        existing_bank = load_exam_bank()
        if grade in existing_bank:
            for _, ex in existing_bank[grade].items():
                if ex.get("title") == exam_data.get("title") and ex.get("questions") == exam_data.get("questions"):
                    return True
                    
        payload = json.dumps({
            "action": "save_exam",
            "exam_id": exam_id,
            "grade": grade,
            "exam_data": exam_data,
            "created_at": created_at
        }).encode('utf-8')
        req = urllib.request.Request(EXAM_API_URL, data=payload, headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            return True
    except Exception:
        return False

def delete_exam_from_sheet(exam_id, grade):
    try:
        payload = json.dumps({
            "action": "delete_exam",
            "exam_id": exam_id,
            "grade": grade
        }).encode('utf-8')
        req = urllib.request.Request(EXAM_API_URL, data=payload, headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            return True
    except Exception:
        return False

def load_submissions():
    try:
        req = urllib.request.Request(SUBMISSION_API_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data and isinstance(data, dict):
                return data
    except Exception:
        pass
    return {}

def record_submission_to_sheet(exam_key, exam_title, student_name, student_phone, student_grade, score, total, percentage):
    clean_phone = re.sub(r'\D', '', student_phone)
    if len(clean_phone) > 10:
        clean_phone = clean_phone[-10:]
    record_id = f"{exam_key}_{clean_phone}" if clean_phone else f"{exam_key}_{clean_text_for_grading(student_name)}"
    current_time = get_current_egypt_time()
    try:
        payload = json.dumps({
            "action": "save_submission",
            "record_id": record_id,
            "exam_key": exam_key,
            "exam_title": exam_title,
            "full_name": student_name.strip(),
            "phone": student_phone.strip(),
            "grade": student_grade.strip(),
            "score": score,
            "total": total,
            "percentage": percentage,
            "timestamp": current_time
        }).encode('utf-8')
        req = urllib.request.Request(SUBMISSION_API_URL, data=payload, headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            return True
    except Exception:
        return False

def load_active_grades():
    if os.path.exists(ACTIVE_GRADES_FILE):
        try:
            with open(ACTIVE_GRADES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def set_active_exam_for_grade(grade, exam_id):
    active_map = load_active_grades()
    active_map[grade] = exam_id
    with open(ACTIVE_GRADES_FILE, "w", encoding="utf-8") as f:
        json.dump(active_map, f, ensure_ascii=False, indent=2)

def clean_text_for_grading(text):
    if not text:
        return ""
    punctuation_to_remove = string.punctuation + '؟،؛«»ـ“”‘’'
    text = text.translate(str.maketrans('', '', punctuation_to_remove))
    text = text.lower()
    return " ".join(text.split())

def parse_text_locally(text):
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
    questions = []
    current_passage = ""
    current_box_words = []
    i = 0
    auto_q_counter = 1
    
    while i < len(lines):
        line = lines[i]
        
        if re.match(r'(?i)^passage\s*:\s*', line):
            current_passage = re.sub(r'(?i)^passage\s*:\s*', '', line).strip()
            i += 1
            while i < len(lines) and not re.match(r'^(\d+[\.\-]|a[\.\)]|b[\.\)]|c[\.\)]|d[\.\)])', lines[i]) and not re.search(r'(?i)^(match|words|box|answer)\s*:', lines[i]):
                current_passage += " " + lines[i]
                i += 1
            continue

        if re.match(r'(?i)^box\s*:\s*', line):
            raw_box = re.sub(r'(?i)^box\s*:\s*', '', line).strip('[] ')
            current_box_words = [w.strip().strip('"\'') for w in raw_box.split(',') if w.strip()]
            i += 1
            continue

        if re.search(r'(?i)^words\s*:', line):
            words_raw = re.search(r'\[(.*?)\]', line)
            words = [w.strip().strip('"\'') for w in words_raw.group(1).split(',')] if words_raw else []
            answer = ""
            i += 1
            while i < len(lines) and not re.search(r'(?i)^(passage|box|match|words)\s*:', lines[i]):
                if re.search(r'(?i)^answer\s*:', lines[i]):
                    answer = re.sub(r'(?i)^answer\s*:', '', lines[i]).strip().strip('"\'')
                i += 1
            if words and answer:
                questions.append({
                    "type": "reorder",
                    "question": "Rearrange the words to make a correct sentence:",
                    "scrambled_words": words,
                    "answer": answer
                })
            continue

        if re.search(r'(?i)match\s*:', line):
            premise = re.sub(r'(?i)^\d*[\.\-]?\s*match\s*:', '', line).strip()
            options, answer = [], ""
            i += 1
            while i < len(lines) and not re.search(r'(?i)^(passage|box|match|words)\s*:', lines[i]):
                if re.search(r'(?i)^options\s*:', lines[i]):
                    opt_raw = re.sub(r'(?i)^options\s*:', '', lines[i]).strip('[] ')
                    options = [o.strip().strip('"\'') for o in opt_raw.split(',') if o.strip()]
                elif re.search(r'(?i)^answer\s*:', lines[i]):
                    answer = re.sub(r'(?i)^answer\s*:', '', lines[i]).strip()
                i += 1
            if premise and options and answer:
                questions.append({
                    "type": "matching",
                    "premise": premise,
                    "options": options,
                    "answer": answer
                })
            continue

        is_question_line = bool(re.match(r'^\d+[\.\-]', line)) or (not line.lower().startswith(('a.', 'b.', 'c.', 'd.', 'answer:', 'options:')))
        
        if is_question_line:
            q_text = line
            if not re.match(r'^\d+[\.\-]', q_text):
                q_text = f"{auto_q_counter}. {q_text}"
            auto_q_counter += 1
            
            options = []
            answer = ""
            i += 1
            
            while i < len(lines):
                sub_line = lines[i]
                if re.search(r'(?i)^answer\s*:', sub_line):
                    answer = re.sub(r'(?i)^answer\s*:\s*', '', sub_line).strip()
                    i += 1
                    break
                elif re.search(r'(?i)^options\s*:', sub_line):
                    opt_raw = re.sub(r'(?i)^options\s*:', '', sub_line).strip('[] ')
                    options = [o.strip().strip('"\'') for o in opt_raw.split(',') if o.strip()]
                elif re.match(r'^[a-dA-D][\.\)]', sub_line):
                    opt_val = re.sub(r'^[a-dA-D][\.\)]\s*', '', sub_line).strip()
                    options.append(opt_val)
                elif re.match(r'^\d+[\.\-]', sub_line) or re.search(r'(?i)^(passage|box|match|words)\s*:', sub_line):
                    break
                i += 1

            if answer:
                if current_box_words and not options:
                    questions.append({
                        "type": "box_complete",
                        "question": q_text,
                        "box_words": current_box_words,
                        "answer": answer
                    })
                elif options:
                    q_obj = {
                        "type": "reading" if current_passage else "mcq",
                        "question": q_text,
                        "options": options,
                        "answer": answer
                    }
                    if current_passage:
                        q_obj["passage"] = current_passage
                    questions.append(q_obj)
                else:
                    questions.append({
                        "type": "fill_text",
                        "question": q_text,
                        "answer": answer
                    })
            continue
            
        i += 1
        
    return questions

def auto_clean_quiz_questions(questions):
    valid_questions = []
    removed_count = 0
    dummy_keywords = ['word1', 'word2', 'word3', 'word4', 'الخيار a', 'الخيار b', 'الخيار c', 'الطرف الأول من السؤال']
    
    for q in questions:
        q_text = str(q.get('question', q.get('premise', ''))).lower()
        ans = str(q.get('answer', '')).lower()
        opts = [str(o).lower() for o in q.get('options', [])]
        
        is_dummy = False
        for dk in dummy_keywords:
            if dk in q_text or dk in ans or any(dk in opt for opt in opts):
                is_dummy = True
                break
                
        if is_dummy or not ans or ans.strip() == "":
            removed_count += 1
            continue
            
        is_valid = True
        q_type = q.get('type', 'mcq')
        if q_type in ["mcq", "reading", "matching"]:
            if not opts or len(opts) < 2:
                is_valid = False
            elif q_type != "matching":
                match_found = any(clean_text_for_grading(ans) == clean_text_for_grading(opt) for opt in opts)
                if not match_found:
                    is_valid = False

        elif q_type == "box_complete":
            box = [str(b).lower() for b in q.get('box_words', [])]
            if not box:
                is_valid = False
            else:
                match_found = any(clean_text_for_grading(ans) == clean_text_for_grading(b) for b in box)
                if not match_found:
                    is_valid = False
                    
        if is_valid:
            valid_questions.append(q)
        else:
            removed_count += 1
            
    return valid_questions, removed_count

def render_speech_player(text_to_read):
    clean_js_text = text_to_read.replace("'", "\\'").replace('"', '\\"').replace("\n", " ")
    audio_html = f"""
    <div style="margin: 12px 0;">
        <button onclick="speakPassage()" style="background-color: #4F46E5; color: white; border: none; padding: 10px 20px; border-radius: 8px; font-weight: bold; font-size: 15px; cursor: pointer; display: flex; align-items: center; gap: 8px;">
            🔊 Listen to Passage (استمع للنص الصوتي)
        </button>
        <script>
        function speakPassage() {{
            window.speechSynthesis.cancel();
            var msg = new SpeechSynthesisUtterance('{clean_js_text}');
            msg.lang = 'en-US';
            msg.rate = 0.85;
            window.speechSynthesis.speak(msg);
        }}
        </script>
    </div>
    """
    st.components.v1.html(audio_html, height=60)

def render_honor_card_widget(grade_name, exam_name, winners_list, card_id="honor-certificate-card"):
    unique_students_map = {}
    for w in winners_list:
        phone_key = w.get('phone', '')
        score_val = w.get('score', 0)
        key = phone_key if phone_key else clean_text_for_grading(w['name'])
        
        if key not in unique_students_map or score_val > unique_students_map[key]['score']:
            unique_students_map[key] = w

    deduplicated_winners = sorted(list(unique_students_map.values()), key=lambda x: (x['score'], x.get('timestamp', '')), reverse=True)

    rows_html = ""
    medals = ["🥇", "🥈", "🥉", "⭐", "⭐", "⭐", "⭐", "⭐", "⭐", "⭐", "⭐", "⭐", "⭐", "⭐", "⭐"]
    colors = ["#F59E0B", "#64748B", "#B45309", "#4F46E5", "#4F46E5", "#4F46E5", "#4F46E5", "#4F46E5", "#4F46E5", "#4F46E5", "#4F46E5", "#4F46E5", "#4F46E5", "#4F46E5", "#4F46E5"]
    
    for i, w in enumerate(deduplicated_winners):
        medal = medals[i] if i < len(medals) else "⭐"
        color = colors[i] if i < len(colors) else "#4F46E5"
        clean_g_tag = w.get('grade', '').split('(')[0].strip()
        grade_badge = f"<span style='background:#E0E7FF; color:#1E40AF; padding:3px 9px; border-radius:8px; font-size:0.85rem; font-weight:700; margin-left:8px;'>{clean_g_tag}</span>" if clean_g_tag else ""
        
        # إضافة عرض وقت الاختبار داخل بطاقة التكريم إن وجد
        time_badge = f"<span style='font-size:0.8rem; color:#FEF08A; margin-right:8px;'>🕒 {clean_time_display(w.get('timestamp',''))}</span>" if w.get('timestamp') else ""

        rows_html += f"""
        <div style="display:flex; justify-content:space-between; align-items:center; background:#FFFFFF; padding:10px 16px; border-radius:10px; margin-bottom:8px; box-shadow:0 2px 4px rgba(0,0,0,0.04); border-right: 5px solid {color};">
            <div style="display:flex; align-items:center; gap:8px;">
                <span style="font-size:1.3rem;">{medal}</span>
                <span style="font-size:1.05rem; font-weight:800; color:#1E293B;">{w['name']}</span>
                {grade_badge}
            </div>
            <div style="display:flex; align-items:center; gap:10px;">
                {time_badge}
                <div style="background:{color}; color:white; padding:4px 12px; border-radius:15px; font-weight:bold; font-size:0.95rem;">
                    {w['score']}% ({w['marks']})
                </div>
            </div>
        </div>
        """
        
    widget_html = f"""
    <div>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
        <div id="{card_id}" style="background: linear-gradient(135deg, #1E3A8A 0%, #1E40AF 50%, #3B82F6 100%); padding: 25px; border-radius: 16px; color: white; font-family: sans-serif; box-shadow: 0 8px 24px rgba(0,0,0,0.15); border: 3px solid #FCD34D; max-width: 680px; margin: 0 auto;">
            <div style="text-align: center; border-bottom: 2px dashed rgba(255,255,255,0.3); padding-bottom: 15px; margin-bottom: 18px;">
                <div style="font-size: 1.7rem; margin-bottom: 4px;">🏆 <b>STUDENTS PERFORMANCE & HONOR ROLL</b> 🏆</div>
                <div style="font-size: 1.2rem; font-weight: 700; color: #FEF08A;">تقرير درجات الطلاب — Mrs. Kheffa Eletreby</div>
                <div style="font-size: 0.95rem; color: #DBEAFE; margin-top: 5px;">📚 <b>{grade_name}</b> | 📝 {exam_name}</div>
            </div>
            <div>
                {rows_html}
            </div>
            <div style="text-align: center; margin-top: 18px; font-size: 0.95rem; color: #FEF08A; font-weight: 700; border-top: 1px solid rgba(255,255,255,0.2); padding-top: 10px;">
                🌟 ألف مبروك لأبطالنا المتميزين مع أطيب أمنياتي بدوام التفوق والنجاح! 🌟
            </div>
        </div>
        <div style="text-align: center; margin-top: 15px;">
            <button onclick="downloadCardImage()" style="background-color: #22C55E; color: white; border: none; padding: 12px 24px; border-radius: 8px; font-weight: bold; font-size: 15px; cursor: pointer; box-shadow: 0 3px 6px rgba(0,0,0,0.15);">
                📥 تحميل تقرير الكارت كصورة (Download Report Image)
            </button>
        </div>
        <script>
        function downloadCardImage() {{
            const cardElement = document.getElementById("{card_id}");
            html2canvas(cardElement, {{ scale: 2, useCORS: true }}).then(canvas => {{
                const link = document.createElement('a');
                link.download = 'Students_Report_{grade_name.replace(" ", "_")}.png';
                link.href = canvas.toDataURL('image/png');
                link.click();
            }});
        }}
        </script>
    </div>
    """
    st.components.v1.html(widget_html, height=len(deduplicated_winners) * 65 + 340)

exam_bank = load_exam_bank()
active_grades_map = load_active_grades()
query_params = st.query_params

resolved_grade = None
active_exam = None
active_exam_key = ""
exam_number_display = ""

quiz_id_param = query_params.get("quiz", None)
if quiz_id_param:
    for gr_name, exams_dict in exam_bank.items():
        if quiz_id_param in exams_dict:
            active_exam = exams_dict[quiz_id_param]
            resolved_grade = gr_name
            active_exam_key = f"{gr_name}_{quiz_id_param}"
            keys_list = list(exams_dict.keys())
            if quiz_id_param in keys_list:
                clean_gr_lbl = gr_name.split('(')[0].strip()
                exam_number_display = f"[{clean_gr_lbl}] الاختبار رقم ({keys_list.index(quiz_id_param) + 1})"
            break

if not active_exam:
    g_param = query_params.get("g", query_params.get("grade", None))
    exam_num_param = query_params.get("exam", None)
    
    if g_param:
        g_clean = str(g_param).lower().strip()
        if g_clean in GRADES_MAP:
            resolved_grade = GRADES_MAP[g_clean]
        else:
            matched = [g for g in GRADES_LIST if g_clean in g.lower()]
            if matched:
                resolved_grade = matched[0]

    if resolved_grade and resolved_grade in exam_bank:
        grade_exams_list = list(exam_bank[resolved_grade].items())
        clean_gr_lbl = resolved_grade.split('(')[0].strip()
        
        if exam_num_param and str(exam_num_param).isdigit():
            idx_req = int(exam_num_param) - 1
            if 0 <= idx_req < len(grade_exams_list):
                target_eid, active_exam = grade_exams_list[idx_req]
                active_exam_key = f"{resolved_grade}_{target_eid}"
                exam_number_display = f"[{clean_gr_lbl}] الاختبار رقم ({exam_num_param})"
                
        if not active_exam:
            target_eid = active_grades_map.get(resolved_grade)
            if target_eid and target_eid in exam_bank[resolved_grade]:
                active_exam = exam_bank[resolved_grade][target_eid]
                active_exam_key = f"{resolved_grade}_{target_eid}"
                keys_list = list(exam_bank[resolved_grade].keys())
                exam_number_display = f"[{clean_gr_lbl}] الاختبار رقم ({keys_list.index(target_eid) + 1})"
            elif len(grade_exams_list) > 0:
                latest_eid, active_exam = grade_exams_list[-1]
                active_exam_key = f"{resolved_grade}_{latest_eid}"
                exam_number_display = f"[{clean_gr_lbl}] الاختبار رقم ({len(grade_exams_list)})"

if not resolved_grade and not active_exam:
    st.markdown("### 🎓 مرحباً بك في منصة الاختبارات")
    st.info("يرجى اختيار صفك الدراسي للدخول إلى الاختبار المحدد لك:")
    chosen_g = st.selectbox("اختر الصف الدراسي:", ["-- اختر الصف --"] + GRADES_LIST, key="direct_grade_select")
    if chosen_g != "-- اختر الصف --":
        for code, name in GRADES_MAP.items():
            if name == chosen_g:
                st.query_params["g"] = code
                st.rerun()

# --- STUDENT EXAM VIEW ---
if active_exam and active_exam.get("questions"):
    questions = active_exam["questions"]
    q_title = active_exam.get("title", "English Assessment")
    q_unit = active_exam.get("unit", "")
    q_lesson = active_exam.get("lesson", "")
    
    meta_tag = f"[{q_unit} - {q_lesson}] " if (q_unit or q_lesson) else ""
    st.markdown(f"### 📝 {exam_number_display} — {meta_tag}{q_title}")
    st.caption(f"📌 الصف الدراسي: **{resolved_grade}**")
    
    if 'current_verified_student' not in st.session_state:
        st.markdown("#### 👤 تسجيل دخول الطالب")
        
        st.markdown("""
        <div class="student-gate-box">
            ⚠️ <b>تعليمات هامة جداً قبل بدء الاختبار:</b><br>
            • يجب كتابة <b>الاسم رباعياً</b> بوضوح تام.<br>
            • يجب استخدام <b>نفس رقم الهاتف الثابت</b> في كل اختبار، وعدم تغيير الرقم لتجنب رفض دخولك أو تكرار اسمك!
        </div>
        """, unsafe_allow_html=True)
        
        stu_name = st.text_input("اسم الطالب رباعي (Student Full Name):", key="gate_student_name")
        stu_phone = st.text_input("رقم تليفون الطالب أو ولي الأمر (Phone Number):", key="gate_student_phone")
        
        start_btn = st.button("🚀 بدء الاختبار (Start Exam)")
        
        if start_btn:
            clean_phone_input = re.sub(r'\D', '', stu_phone)
            if len(clean_phone_input) > 10:
                clean_phone_input = clean_phone_input[-10:]
                
            name_parts = stu_name.strip().split()
            
            if not stu_name.strip():
                st.error("يرجى كتابة اسم الطالب للمتابعة!")
            elif len(name_parts) < 4:
                st.warning("⚠️ تنبيه: يرجى كتابة **الاسم رباعياً** (4 أسماء على الأقل: الأول، الثاني، الثالث، الرابع) لضمان صحة بياناتك في لوحة الشرف!")
            elif not clean_phone_input or len(clean_phone_input) < 9:
                st.error("يرجى كتابة رقم هاتف صحيح!")
            else:
                norm_name = clean_text_for_grading(stu_name)
                all_subs = load_submissions()
                
                check_phone_key = f"{active_exam_key}_{clean_phone_input}"
                check_name_key = f"{active_exam_key}_{norm_name}"
                
                if check_phone_key in all_subs or check_name_key in all_subs:
                    prev = all_subs.get(check_phone_key, all_subs.get(check_name_key))
                    st.error(f"⚠️ عذراً يا {prev['full_name']}! لقد تم أداء هذا الاختبار مسبقاً بهذا الرقم/الاسم بتاريخ {clean_time_display(prev['timestamp'])}. لا يُسمح بإعادة الاختبار.")
                    st.info(f"🏆 **درجتك المسجلة:** {prev['score']} / {prev['total']} ({prev['percentage']}%)")
                    
                    teacher_phone = "201090570624"
                    wa_msg = f"*Exam:* {exam_number_display} - {meta_tag}{q_title}\n*Teacher:* Mrs. Kheffa Eletreby\n*Student:* {prev['full_name']}\n*Grade:* {resolved_grade}\n*Phone:* {prev.get('phone', '')}\n*Recorded Score:* {prev['score']}/{prev['total']} ({prev['percentage']}%)\n*Time:* {clean_time_display(prev.get('timestamp', ''))}"
                    whatsapp_url = f"https://wa.me/{teacher_phone}?text={urllib.parse.quote(wa_msg)}"
                    
                    st.markdown(f"""
                        <div style="text-align: center; margin-top: 15px;">
                            <a href="{whatsapp_url}" target="_blank" style="background-color: #25D366; color: white; padding: 14px 28px; text-decoration: none; font-size: 16px; font-weight: bold; border-radius: 8px; display: inline-block;">
                                📲 Send Score to Mrs. Kheffa on WhatsApp
                            </a>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.session_state['current_verified_student'] = stu_name.strip()
                    st.session_state['current_verified_phone'] = clean_phone_input
                    st.rerun()
    else:
        active_student = st.session_state['current_verified_student']
        active_phone = st.session_state['current_verified_phone']
        
        if not st.session_state.get('exam_submitted', False):
            st.info(f"مرحباً بك يا **{active_student}** ({resolved_grade})! أجب عن جميع الأسئلة ثم اضغط Submit Exam.")
            
            with st.form("interactive_exam_form"):
                user_answers = {}
                graphic_passages = set()
                displayed_boxes = set()
                
                for idx, q in enumerate(questions):
                    q_type = q.get('type', 'mcq')
                    st.markdown(f"**Question {idx + 1} (1 Mark)**")
                    
                    if q_type == "reading" and "passage" in q:
                        pass_text = q['passage']
                        if pass_text not in graphic_passages:
                            st.markdown(f"""
                            <div class="passage-box">
                                📖 <b>Read the text / اقرأ النص التالي:</b><br><br>
                                {pass_text}
                            </div>
                            """, unsafe_allow_html=True)
                            render_speech_player(pass_text)
                            graphic_passages.add(pass_text)

                    if q_type == "box_complete":
                        box_words = q.get('box_words', [])
                        box_key = ",".join(box_words)
                        if box_key not in displayed_boxes:
                            st.markdown(f"""
                            <div class="word-box-header">
                                📦 Complete from words in the box:<br>
                                [ {' — '.join(box_words)} ]
                            </div>
                            """, unsafe_allow_html=True)
                            displayed_boxes.add(box_key)
                    
                    if q_type in ["mcq", "reading"]:
                        st.write(q.get('question', ''))
                        opt_list = ["-- اختر الإجابة الصحيحة --"] + q.get('options', [])
                        chosen_opt = st.selectbox("Choose correct answer:", options=opt_list, key=f"ans_mcq_{idx}")
                        user_answers[idx] = "" if chosen_opt == "-- اختر الإجابة الصحيحة --" else chosen_opt
                        
                    elif q_type == "box_complete":
                        st.write(q.get('question', ''))
                        box_opts = ["-- Select Word --"] + q.get('box_words', [])
                        chosen_box = st.selectbox("Select word / اختر الكلمة:", options=box_opts, key=f"ans_box_{idx}")
                        user_answers[idx] = "" if chosen_box == "-- Select Word --" else chosen_box
                        
                    elif q_type == "matching":
                        st.write(f"🔹 Match: **{q.get('premise', '')}**")
                        match_opts = ["-- Select Match --"] + q.get('options', [])
                        chosen_match = st.selectbox("Select match:", options=match_opts, key=f"ans_match_{idx}")
                        user_answers[idx] = "" if chosen_match == "-- Select Match --" else chosen_match
                        
                    elif q_type == "reorder":
                        st.write(q.get('question', 'Rearrange the following words:'))
                        words_list = q.get('scrambled_words', [])
                        selected_words = st.multiselect("Tap words in correct order (اضغط على الكلمات بالترتيب الصحيح):", options=words_list, key=f"ans_reorder_{idx}")
                        user_answers[idx] = " ".join(selected_words)
                        
                    elif q_type == "fill_text":
                        st.write(q.get('question', ''))
                        user_answers[idx] = st.text_input("Write your answer:", key=f"ans_filltxt_{idx}")
                        
                    st.write("---")
                    
                submit = st.form_submit_button("Submit Exam & View Results 📊")
                if submit:
                    st.session_state['exam_submitted'] = True
                    st.session_state['submitted_answers'] = user_answers
                    st.rerun()

        if st.session_state.get('exam_submitted', False):
            st.subheader("📋 Results & Model Answers")
            score = 0
            total = len(questions)
            user_answers = st.session_state.get('submitted_answers', {})
            current_time_str = get_current_egypt_time()
            
            full_exam_desc = f"{exam_number_display} - {meta_tag}{q_title}".strip()
            breakdown_text = f"*Exam:* {full_exam_desc}\n*Teacher:* Mrs. Kheffa Eletreby\n*Student:* {active_student}\n*Grade:* {resolved_grade}\n*Phone:* {active_phone}\n*Time:* {current_time_str}\n"
            
            for idx, q in enumerate(questions):
                q_type = q.get('type', 'mcq')
                ans = user_answers.get(idx, "")
                correct = q.get('answer', '')
                
                cleaned_user_ans = clean_text_for_grading(str(ans))
                cleaned_correct_ans = clean_text_for_grading(str(correct))
                
                is_correct = False
                if cleaned_user_ans == cleaned_correct_ans and ans not in ["-- اختر الإجابة الصحيحة --", "-- Select Word --", "-- Select Match --", "", None]:
                    is_correct = True
                
                if q_type == "reorder" and not is_correct:
                    user_words_set = set(cleaned_user_ans.split())
                    correct_words_set = set(cleaned_correct_ans.split())
                    if user_words_set == correct_words_set and len(cleaned_user_ans.split()) == len(cleaned_correct_ans.split()):
                        is_correct = True
                        
                if is_correct:
                    score += 1
                    st.markdown(f"**Q{idx + 1}: Correct ✅** <span style='color: green; font-weight: bold;'>(Your answer: {ans})</span>", unsafe_allow_html=True)
                    breakdown_text += f"Q{idx+1}: Correct ✅\n"
                else:
                    st.markdown(f"**Q{idx + 1}: Incorrect ❌** | <span style='color: red;'>Your answer: {ans or 'None'}</span> | **Model Answer:** <span style='color: green; font-weight: bold;'>{correct}</span>", unsafe_allow_html=True)
                    breakdown_text += f"Q{idx+1}: Incorrect ❌ (Ans: {ans or 'None'} | Correct: {correct})\n"
                    
            percentage = round((score / total) * 100, 1) if total > 0 else 0
            st.info(f"### 🏆 Final Score: {score} / {total} ({percentage}%)")
            breakdown_text += f"\n*Final Score:* {score}/{total} ({percentage}%)"
            
            record_submission_to_sheet(active_exam_key, full_exam_desc, active_student, active_phone, resolved_grade, score, total, percentage)
            
            teacher_phone = "201090570624"
            whatsapp_url = f"https://wa.me/{teacher_phone}?text={urllib.parse.quote(breakdown_text)}"
            
            st.markdown(f"""
                <div style="text-align: center; margin-top: 25px;">
                    <a href="{whatsapp_url}" target="_blank" style="background-color: #25D366; color: white; padding: 14px 28px; text-decoration: none; font-size: 17px; font-weight: bold; border-radius: 8px; display: inline-block;">
                        📲 Send Score to Mrs. Kheffa on WhatsApp
                    </a>
                </div>
            """, unsafe_allow_html=True)
elif resolved_grade:
    st.info(f"👋 لا يوجد اختبار نشط حالياً لصف **{resolved_grade}**.")

st.write("---")
with st.expander("🔒 Admin Portal & Exam Bank (لوحة تحكم المعلمة)", expanded=False):
    admin_pass = st.text_input("Enter Admin Password:", type="password", key="sec_admin_pass")
    
    if admin_pass == "admin":
        st.success("أهلاً بكِ مس خفة!")
        
        tab_weekly, tab_reports, tab_grades_report, tab_bank, tab_pdf, tab_new = st.tabs([
            "🏆 أوائل الأسابيع", 
            "📊 درجات الاختبارات", 
            "🏫 تقرير كل صف",
            "📚 بنك الاختبارات",
            "📄 تحميل كويز وموديل الإجابة PDF",
            "➕ إضافة اختبار"
        ])
        
        with tab_weekly:
            st.markdown("### 🏆 أرشيف أوائل وتكريم كل أسبوع")
            subs = load_submissions()
            if subs:
                records = []
                for _, s_data in subs.items():
                    d_obj = extract_date_obj(s_data.get('timestamp', ''))
                    week_label, week_sort_idx = calculate_custom_academic_week(d_obj)
                    raw_name = str(s_data.get('full_name', '')).strip()
                    clean_n = clean_text_for_grading(raw_name)
                    phone_clean = re.sub(r'\D', '', str(s_data.get('phone', '')))
                    if len(phone_clean) > 10:
                        phone_clean = phone_clean[-10:]
                    unique_key = phone_clean if len(phone_clean) >= 9 else clean_n
                    records.append({
                        "unique_id": unique_key,
                        "اسم الطالب": raw_name,
                        "الصف الدراسي": s_data.get('grade', ''),
                        "رقم الهاتف": s_data.get('phone', ''),
                        "عنوان الاختبار": s_data.get('exam_title', s_data.get('exam_key', '')),
                        "الدرجة": s_data.get('score', 0),
                        "المجموع": s_data.get('total', 0),
                        "النسبة": s_data.get('percentage', 0),
                        "وقت التسليم": clean_time_display(s_data.get('timestamp', '')),
                        "week_label": week_label,
                        "week_idx": week_sort_idx
                    })
                df_weekly_all = pd.DataFrame(records)
                weeks_df = df_weekly_all[["week_label", "week_idx"]].drop_duplicates().sort_values(by="week_idx", ascending=False)
                unique_weeks = weeks_df["week_label"].tolist()
                c_w1, c_w2 = st.columns([2.2, 1.2])
                chosen_week = c_w1.selectbox("📅 الأسبوع:", unique_weeks, key="sel_honor_week")
                filter_wk_grade = c_w2.selectbox("المرحلة:", ["جميع المراحل"] + GRADES_LIST, key="sel_honor_wk_grade")
                df_selected_week = df_weekly_all[df_weekly_all["week_label"] == chosen_week]
                if filter_wk_grade != "جميع المراحل":
                    df_selected_week = df_selected_week[df_selected_week["الصف الدراسي"] == filter_wk_grade]
                df_selected_week = df_selected_week.sort_values(by=["النسبة", "الدرجة", "وقت التسليم"], ascending=[False, False, True])
                df_selected_week = df_selected_week.drop_duplicates(subset=["unique_id"], keep="first")
                if not df_selected_week.empty:
                    wk_winners = [{"name": r["اسم الطالب"], "grade": r["الصف الدراسي"], "score": r["النسبة"], "marks": f"{r['الدرجة']}/{r['المجموع']}", "phone": r["رقم الهاتف"], "timestamp": r["وقت التسليم"]} for _, r in df_selected_week.iterrows()]
                    render_honor_card_widget(f"أوائل الأسبوع", chosen_week, wk_winners, card_id="weekly-honor-card")
                    st.dataframe(df_selected_week.drop(columns=["week_idx", "unique_id"]), use_container_width=True)
                else:
                    st.info("لا توجد نتائج مسجلة لهذا الأسبوع.")

        with tab_reports:
            st.markdown("### 📊 تقرير درجات الطلاب (مع أوقات التسليم)")
            subs = load_submissions()
            if subs:
                records = [{
                    "unique_id": (re.sub(r'\D', '', str(s.get('phone', '')))[-10:] if len(re.sub(r'\D', '', str(s.get('phone', '')))) >= 9 else clean_text_for_grading(s.get('full_name', ''))),
                    "اسم الطالب": str(s.get('full_name', '')).strip(),
                    "الصف الدراسي": s.get('grade', ''),
                    "رقم الهاتف": s.get('phone', ''),
                    "عنوان الاختبار": s.get('exam_title', s.get('exam_key', '')),
                    "الدرجة": s.get('score', 0),
                    "المجموع": s.get('total', 0),
                    "النسبة": s.get('percentage', 0),
                    "وقت التسليم": clean_time_display(s.get('timestamp', ''))
                } for _, s in subs.items()]
                df_all = pd.DataFrame(records)
                c_sel_gr, c_sel_ex = st.columns([1.5, 2])
                filter_grade = c_sel_gr.selectbox("اختر الصف:", ["-- اختر الصف --"] + GRADES_LIST, key="report_grade_filter")
                if filter_grade != "-- اختر الصف --":
                    df_grade_filtered = df_all[df_all["الصف الدراسي"] == filter_grade]
                    if not df_grade_filtered.empty:
                        available_exams = list(df_grade_filtered["عنوان الاختبار"].unique())
                        chosen_exam_filter = c_sel_ex.selectbox("اختر الاختبار:", ["-- اختر الاختبار --"] + available_exams, key="report_exam_filter")
                        if chosen_exam_filter != "-- اختر الاختبار --":
                            df_final_filtered = df_grade_filtered[df_grade_filtered["عنوان الاختبار"] == chosen_exam_filter].drop_duplicates(subset=["unique_id"], keep="first")
                            winners = [{"name": r["اسم الطالب"], "grade": r["الصف الدراسي"], "score": r["النسبة"], "marks": f"{r['الدرجة']}/{r['المجموع']}", "phone": r["رقم الهاتف"], "timestamp": r["وقت التسليم"]} for _, r in df_final_filtered.iterrows()]
                            render_honor_card_widget(filter_grade, chosen_exam_filter, winners, card_id="exam-specific-honor-card")
                            st.dataframe(df_final_filtered.drop(columns=["unique_id"]), use_container_width=True)

        with tab_grades_report:
            st.markdown("### 🏫 تقرير درجات كل صف (مع أوقات التسليم بدقة)")
            subs_g = load_submissions()
            if subs_g:
                selected_report_grade = st.selectbox("اختر الصف:", ["-- اختر الصف --"] + GRADES_LIST, key="dedicated_grade_sel")
                if selected_report_grade != "-- اختر الصف --":
                    g_records = [{
                        "unique_id": (re.sub(r'\D', '', str(s.get('phone', '')))[-10:] if len(re.sub(r'\D', '', str(s.get('phone', '')))) >= 9 else clean_text_for_grading(s.get('full_name', ''))),
                        "اسم الطالب": str(s.get('full_name', '')).strip(),
                        "رقم الهاتف": s.get('phone', ''),
                        "عنوان الاختبار": s.get('exam_title', s.get('exam_key', '')),
                        "الدرجة": s.get('score', 0),
                        "المجموع": s.get('total', 0),
                        "النسبة المئوية (%)": f"{s.get('percentage', 0)}%",
                        "وقت التسليم": clean_time_display(s.get('timestamp', ''))
                    } for _, s in subs_g.items() if s.get('grade') == selected_report_grade]
                    
                    if g_records:
                        df_g_raw = pd.DataFrame(g_records).drop_duplicates(subset=["unique_id"], keep="first")
                        
                        report_winners = [{
                            "name": r["اسم الطالب"],
                            "grade": selected_report_grade,
                            "score": float(r["النسبة المئوية (%)"].replace("%","")),
                            "marks": f"{r['الدرجة']}/{r['المجموع']}",
                            "phone": r["رقم الهاتف"],
                            "timestamp": r["وقت التسليم"]
                        } for _, r in df_g_raw.iterrows()]
                        
                        render_honor_card_widget(selected_report_grade, "تقرير الكشف الكامل", report_winners, card_id="grade-report-card")
                        st.dataframe(df_g_raw, use_container_width=True)

        with tab_bank:
            st.markdown("### 📚 بنك الاختبارات")
            selected_manage_grade = st.selectbox("الصف المطلوب:", GRADES_LIST, key="sel_mgr_grade")
            bank = load_exam_bank()
            grade_exams = bank.get(selected_manage_grade, {})
            if grade_exams:
                for idx, (e_id, e_info) in enumerate(grade_exams.items(), 1):
                    st.write(f"📝 {e_info.get('title')} ({len(e_info.get('questions', []))} سؤال)")
                    if st.button(f"حذف الاختبار {idx}", key=f"del_{e_id}"):
                        delete_exam_from_sheet(e_id, selected_manage_grade)
                        st.rerun()

        with tab_pdf:
            st.markdown("### 📄 معاينة الاختبار PDF")
            pdf_grade = st.selectbox("الصف:", GRADES_LIST, key="pdf_grade_sel")
            bank_pdf = load_exam_bank()
            grade_exams_pdf = bank_pdf.get(pdf_grade, {})
            if grade_exams_pdf:
                chosen_ex = st.selectbox("الاختبار:", list(grade_exams_pdf.keys()), key="pdf_ex_sel")
                if chosen_ex:
                    ex_obj = grade_exams_pdf[chosen_ex]
                    for idx, q in enumerate(ex_obj.get('questions', []), 1):
                        st.write(f"Q{idx}: {q.get('question')} -> Ans: {q.get('answer')}")

        with tab_new:
            st.markdown("### ➕ إضافة اختبار (سواء من ملف PDF أو نسخ نص امتحان HTML جاهز)")
            sel_grade = st.selectbox("الصف:", GRADES_LIST, key="new_exam_grade")
            quiz_unit = st.text_input("الوحدة:", "Unit 1", key="exam_unit_input")
            quiz_lesson = st.text_input("الدرس:", "Lesson 1", key="exam_lesson_input")
            quiz_title = st.text_input("عنوان الاختبار:", f"{quiz_unit} - {quiz_lesson} Assessment", key="exam_title_input")
            
            uploaded_file = st.file_uploader("📂 ارفعي ملف الأسئلة (.pdf أو .txt أو .docx):", type=["pdf", "docx", "txt"], key="quiz_file_uploader")
            
            if 'extracted_file_text' not in st.session_state:
                st.session_state['extracted_file_text'] = ""

            if uploaded_file is not None:
                try:
                    if uploaded_file.name.endswith('.txt'):
                        st.session_state['extracted_file_text'] = uploaded_file.read().decode('utf-8')
                        st.success("📁 تم قراءة ملف النصوص بنجاح!")
                    elif uploaded_file.name.endswith('.docx'):
                        import docx
                        doc = docx.Document(uploaded_file)
                        st.session_state['extracted_file_text'] = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
                        st.success("📁 تم قراءة ملف الـ Word بنجاح!")
                    elif uploaded_file.name.endswith('.pdf'):
                        reader = pypdf.PdfReader(uploaded_file)
                        extracted_pages = [page.extract_text() for page in reader.pages if page.extract_text()]
                        pdf_content = "\n".join(extracted_pages)
                        if pdf_content.strip():
                            st.session_state['extracted_file_text'] = pdf_content
                            st.success("📄 تم استخراج نصوص الـ PDF بالكامل!")
                        else:
                            st.warning("⚠️ الملف مصور (Scanned). يرجى لصق محتوى الـ HTML أو الأسئلة في المربع أدناه مباشرة.")
                except Exception as e:
                    st.error(f"⚠️ خطأ: {e}")

            raw_text = st.text_area("ألصقي نص الأسئلة أو امتحان الـ HTML هنا:", value=st.session_state['extracted_file_text'], height=250, key="new_raw_text")
            
            if st.button("🔍 فحص ومعاينة الأسئلة", key="preview_btn"):
                if raw_text.strip():
                    raw_parsed = parse_text_locally(raw_text)
                    cleaned_parsed, removed_count = auto_clean_quiz_questions(raw_parsed)
                    if removed_count > 0:
                        st.warning(f"⚠️ تم تنبيه وحذف ({removed_count}) سؤال غير مكتمل ليبقى الكويز نظيفاً!")
                    if cleaned_parsed:
                        st.success(f"🎉 تم قراءة وفحص ({len(cleaned_parsed)}) سؤال بنجاح وجاهزة للحفظ!")
                        for p_idx, p_q in enumerate(cleaned_parsed):
                            st.markdown(f"**Q{p_idx + 1}:** {p_q.get('question', p_q.get('premise', ''))} | 🟢 **الإجابة:** `{p_q.get('answer')}`")
                else:
                    st.warning("يرجى لصق النصوص أولاً.")

            col_save_draft, col_save_pub = st.columns([1, 1])
            save_as_draft = col_save_draft.button("📁 حفظ في الأرشيف")
            save_and_pub = col_save_pub.button("🚀 حفظ وتفعيل للطلاب فوراً")
            
            if save_as_draft or save_and_pub:
                if raw_text.strip():
                    raw_parsed = parse_text_locally(raw_text)
                    parsed, _ = auto_clean_quiz_questions(raw_parsed)
                    if parsed and len(parsed) > 0:
                        exam_id = f"exam_{int(datetime.now().timestamp())}"
                        exam_payload = {
                            "title": quiz_title.strip(),
                            "unit": quiz_unit.strip(),
                            "lesson": quiz_lesson.strip(),
                            "grade": sel_grade,
                            "questions": parsed,
                            "created_at": get_current_egypt_time()
                        }
                        if save_exam_to_sheet(exam_id, sel_grade, exam_payload, get_current_egypt_time()):
                            if save_and_pub:
                                set_active_exam_for_grade(sel_grade, exam_id)
                                st.success("🎉 تم حفظ وتفعيل الاختبار بنجاح!")
                            else:
                                st.success("📁 تم حفظ الاختبار في الأرشيف بنجاح!")
                            st.rerun()
                        else:
                            st.error("⚠️ حدث خطأ أثناء الحفظ في جوجل شيت.")
                    else:
                        st.error("لا توجد أسئلة صالحة للحفظ.")
                else:
                    st.error("يرجى لصق نص الأسئلة أولاً.")
    elif admin_pass:
        st.error("Incorrect password!")
