import streamlit as st
import json
import os
import string
import re
import urllib.parse
from datetime import datetime, timezone, timedelta, date
import pandas as pd

st.set_page_config(
    page_title="Mrs. Kheffa Eletreby | English Assessments",
    page_icon="📝",
    layout="centered"
)

# Egypt Local Time (UTC + 3 Hours)
EGYPT_TIMEZONE = timezone(timedelta(hours=3))

# Term Start Anchor: Saturday, August 29, 2026
ACADEMIC_START_DATE = date(2026, 8, 29)

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
    .main-title-box h2 { font-size: 1.5rem; margin: 0; font-weight: 800; }
    .main-title-box h3 { font-size: 1.15rem; margin: 6px 0; color: #E0E7FF; font-weight: 600; }
    .main-title-box p { font-size: 0.95rem; margin: 0; color: #DBEAFE; }

    .grade-focus-header {
        background-color: #EFF6FF;
        border: 2px solid #3B82F6;
        border-radius: 10px;
        padding: 14px 18px;
        margin: 15px 0;
        color: #1E3A8A;
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

EXAM_BANK_FILE = "exam_bank.json"
ACTIVE_GRADES_FILE = "active_by_grade.json"
SUBMISSIONS_FILE = "submitted_students.json"

GRADES_MAP = {
    "1": "Primary 1 (أولى ابتدائي)",
    "2": "Primary 2 (تانية ابتدائي)",
    "3": "Primary 3 (تالتة ابتدائي)",
    "4": "Primary 4 (رابعة ابتدائي)",
    "5": "Primary 5 (خامسة ابتدائي)",
    "6": "Primary 6 (سادسة ابتدائي)",
    "prep1": "Prep 1 (أولى إعدادي)",
    "prep2": "Prep 2 (تانية إعدادي)",
    "prep3": "Prep 3 (تالتة إعدادي)",
    "sec1": "Secondary 1 (أولى ثانوي)",
    "sec2": "Secondary 2 (تانية ثانوي)",
    "sec3": "Secondary 3 (تالتة ثانوي)"
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
    """Calculates Week number starting from Saturday 2026-08-29."""
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
    if os.path.exists(EXAM_BANK_FILE):
        try:
            with open(EXAM_BANK_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_exam_bank(bank):
    with open(EXAM_BANK_FILE, "w", encoding="utf-8") as f:
        json.dump(bank, f, ensure_ascii=False, indent=2)

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
    text = text.translate(str.maketrans('', '', string.punctuation + '؟،؛«»ـ“”‘’'))
    text = text.lower()
    return " ".join(text.split())

def record_submission(exam_key, exam_title, student_name, student_phone, student_grade, score, total, percentage):
    submissions = load_submissions()
    clean_phone = re.sub(r'\D', '', student_phone)
    record_id = f"{exam_key}_{clean_phone}" if clean_phone else f"{exam_key}_{clean_text_for_grading(student_name)}"
    submissions[record_id] = {
        "exam_key": exam_key,
        "exam_title": exam_title,
        "full_name": student_name.strip(),
        "phone": student_phone.strip(),
        "grade": student_grade.strip(),
        "score": score,
        "total": total,
        "percentage": percentage,
        "timestamp": get_current_egypt_time()
    }
    with open(SUBMISSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(submissions, f, ensure_ascii=False, indent=2)

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
    rows_html = ""
    medals = ["🥇", "🥈", "🥉", "⭐", "⭐", "⭐", "⭐", "⭐", "⭐", "⭐"]
    colors = ["#F59E0B", "#64748B", "#B45309", "#4F46E5", "#4F46E5", "#4F46E5", "#4F46E5", "#4F46E5", "#4F46E5", "#4F46E5"]
    
    for i, w in enumerate(winners_list):
        medal = medals[i] if i < len(medals) else "⭐"
        color = colors[i] if i < len(colors) else "#4F46E5"
        clean_g_tag = w.get('grade', '').split('(')[0].strip()
        grade_badge = f"<span style='background:#E0E7FF; color:#1E40AF; padding:3px 9px; border-radius:8px; font-size:0.85rem; font-weight:700; margin-left:8px;'>{clean_g_tag}</span>" if clean_g_tag else ""
        
        rows_html += f"""
        <div style="display:flex; justify-content:space-between; align-items:center; background:#FFFFFF; padding:10px 16px; border-radius:10px; margin-bottom:8px; box-shadow:0 2px 4px rgba(0,0,0,0.04); border-right: 5px solid {color};">
            <div style="display:flex; align-items:center; gap:8px;">
                <span style="font-size:1.4rem;">{medal}</span>
                <span style="font-size:1.1rem; font-weight:800; color:#1E293B;">{w['name']}</span>
                {grade_badge}
            </div>
            <div style="background:{color}; color:white; padding:4px 12px; border-radius:15px; font-weight:bold; font-size:0.95rem;">
                {w['score']}% ({w['marks']})
            </div>
        </div>
        """
        
    widget_html = f"""
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <div style="text-align: center; margin-bottom: 15px;">
        <button onclick="downloadCard_{card_id}()" style="background: linear-gradient(135deg, #2563EB, #1D4ED8); color: white; border: none; padding: 12px 24px; border-radius: 10px; font-size: 16px; font-weight: 800; cursor: pointer; box-shadow: 0 4px 10px rgba(37,99,235,0.3); display: inline-flex; align-items: center; gap: 8px;">
            📸 حفظ لوحة الشرف كصورة للواتساب (Download Image)
        </button>
    </div>
    <div id="{card_id}" style="background: linear-gradient(135deg, #1E3A8A 0%, #1E40AF 50%, #3B82F6 100%); padding: 25px; border-radius: 16px; color: white; font-family: sans-serif; box-shadow: 0 8px 24px rgba(0,0,0,0.15); border: 3px solid #FCD34D; max-width: 680px; margin: 0 auto;">
        <div style="text-align: center; border-bottom: 2px dashed rgba(255,255,255,0.3); padding-bottom: 15px; margin-bottom: 18px;">
            <div style="font-size: 1.8rem; margin-bottom: 4px;">🏆 <b>HONOR ROLL & TOP ACHIEVERS</b> 🏆</div>
            <div style="font-size: 1.25rem; font-weight: 700; color: #FEF08A;">لوحة شرف المتفوقين — Mrs. Kheffa Eletreby</div>
            <div style="font-size: 1rem; color: #DBEAFE; margin-top: 5px;">📚 <b>{grade_name}</b> | 📝 {exam_name}</div>
        </div>
        <div>
            {rows_html}
        </div>
        <div style="text-align: center; margin-top: 18px; font-size: 0.95rem; color: #FEF08A; font-weight: 700; border-top: 1px solid rgba(255,255,255,0.2); padding-top: 10px;">
            🌟 ألف مبروك لأبطالنا المتميزين مع أطيب أمنياتي بدوام التفوق والنجاح! 🌟
        </div>
    </div>
    <script>
    function downloadCard_{card_id}() {{
        var card = document.getElementById("{card_id}");
        html2canvas(card, {{ scale: 2 }}).then(function(canvas) {{
            var link = document.createElement('a');
            link.download = 'Honor_Roll_{grade_name.split(' ')[0]}.png';
            link.href = canvas.toDataURL();
            link.click();
        }});
    }}
    </script>
    """
    st.components.v1.html(widget_html, height=len(winners_list) * 65 + 240)

def parse_text_locally(text):
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
    questions = []
    current_passage = ""
    current_box_words = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        if re.match(r'(?i)^passage\s*:\s*', line):
            current_passage = re.sub(r'(?i)^passage\s*:\s*', '', line).strip()
            i += 1
            while i < len(lines) and not re.match(r'^\d+[\.\-]', lines[i]) and not re.search(r'(?i)^(match|words|box)\s*:', lines[i]):
                current_passage += " " + lines[i]
                i += 1
            continue

        if re.match(r'(?i)^box\s*:\s*', line):
            raw_box = re.sub(r'(?i)^box\s*:\s*', '', line).strip('[] ')
            current_box_words = [w.strip().strip('"\'') for w in raw_box.split(',') if w.strip()]
            i += 1
            continue

        if re.search(r'(?i)match\s*:', line):
            premise = re.sub(r'(?i)^\d+[\.\-]?\s*match\s*:\s*', '', line).strip()
            options, answer = [], ""
            i += 1
            while i < len(lines) and not re.match(r'^\d+[\.\-]', lines[i]) and not re.search(r'(?i)^(passage|box)\s*:', lines[i]):
                if re.search(r'(?i)^options\s*:', lines[i]):
                    opt_raw = re.sub(r'(?i)^options\s*:\s*', '', lines[i]).strip('[] ')
                    options = [o.strip().strip('"\'') for o in opt_raw.split(',') if o.strip()]
                elif re.search(r'(?i)^answer\s*:', lines[i]):
                    answer = re.sub(r'(?i)^answer\s*:\s*', '', lines[i]).strip()
                i += 1
            if premise and options:
                questions.append({
                    "type": "matching",
                    "premise": premise,
                    "options": options,
                    "answer": answer if answer else options[0]
                })
            continue

        elif re.search(r'(?i)words\s*:', line):
            words_raw = re.search(r'\[(.*?)\]', line)
            words = [w.strip().strip('"\'') for w in words_raw.group(1).split(',')] if words_raw else []
            answer = ""
            i += 1
            if i < len(lines) and re.search(r'(?i)^answer\s*:', lines[i]):
                answer = re.sub(r'(?i)^answer\s*:\s*', '', lines[i]).strip()
                i += 1
            if words:
                questions.append({
                    "type": "reorder",
                    "question": "Rearrange the words to make a correct sentence:",
                    "scrambled_words": words,
                    "answer": answer if answer else " ".join(words)
                })
            continue

        elif re.match(r'^\d+[\.\-]', line):
            q_text = line
            options = []
            answer = ""
            i += 1
            while i < len(lines) and (re.match(r'^[a-dA-D][\.\)]', lines[i]) or re.search(r'(?i)^answer\s*:', lines[i]) or re.search(r'(?i)^options\s*:', lines[i])):
                if re.search(r'(?i)^answer\s*:', lines[i]):
                    answer = re.sub(r'(?i)^answer\s*:\s*', '', lines[i]).strip()
                elif re.search(r'(?i)^options\s*:', lines[i]):
                    opt_raw = re.sub(r'(?i)^options\s*:\s*', '', lines[i]).strip('[] ')
                    options = [o.strip().strip('"\'') for o in opt_raw.split(',') if o.strip()]
                else:
                    opt_val = re.sub(r'^[a-dA-D][\.\)]\s*', '', lines[i]).strip()
                    options.append(opt_val)
                i += 1

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
                    "answer": answer if answer else options[0]
                }
                if current_passage:
                    q_obj["passage"] = current_passage
                questions.append(q_obj)
            elif answer:
                questions.append({
                    "type": "fill_text",
                    "question": q_text,
                    "answer": answer
                })
            continue
        i += 1
    return questions

# --- ROBUST EXAM LOCATOR ---
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
        if st.button("الانتقال للاختبار 🚀"):
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
        stu_name = st.text_input("اسم الطالب رباعي (Student Full Name):", key="gate_student_name")
        stu_phone = st.text_input("رقم تليفون الطالب أو ولي الأمر (Phone Number):", key="gate_student_phone")
        
        start_btn = st.button("🚀 بدء الاختبار (Start Exam)")
        
        if start_btn:
            clean_phone_input = re.sub(r'\D', '', stu_phone)
            if not stu_name.strip():
                st.error("يرجى كتابة الاسم رباعي للمتابعة!")
            elif not clean_phone_input or len(clean_phone_input) < 10:
                st.error("يرجى كتابة رقم هاتف صحيح مكون من 11 رقماً!")
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
                            <a href="{whatsapp_url}" target="_blank" style="background-color: #25D366; color: white; padding: 12px 24px; text-decoration: none; font-size: 16px; font-weight: bold; border-radius: 8px; display: inline-block;">
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
                displayed_passages = set()
                displayed_boxes = set()
                
                for idx, q in enumerate(questions):
                    q_type = q.get('type', 'mcq')
                    st.markdown(f"**Question {idx + 1} (1 Mark)**")
                    
                    if q_type == "reading" and "passage" in q:
                        pass_text = q['passage']
                        if pass_text not in displayed_passages:
                            st.markdown(f"""
                            <div class="passage-box">
                                📖 <b>Read the text / اقرأ النص التالي:</b><br><br>
                                {pass_text}
                            </div>
                            """, unsafe_allow_html=True)
                            render_speech_player(pass_text)
                            displayed_passages.add(pass_text)

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
                        user_answers[idx] = st.radio("Choose correct answer:", options=q.get('options', []), key=f"ans_mcq_{idx}", index=None)
                    elif q_type == "box_complete":
                        st.write(q.get('question', ''))
                        user_answers[idx] = st.selectbox("Select word / اختر الكلمة:", options=["-- Select Word --"] + q.get('box_words', []), key=f"ans_box_{idx}")
                    elif q_type == "matching":
                        st.write(f"🔹 Match: **{q.get('premise', '')}**")
                        user_answers[idx] = st.selectbox("Select match:", options=["-- Select Match --"] + q.get('options', []), key=f"ans_match_{idx}")
                    elif q_type == "reorder":
                        st.write(q.get('question', 'Rearrange the following words:'))
                        words_list = q.get('scrambled_words', [])
                        selected_words = st.multiselect("Tap words in correct order (اضغط على الكلمات بالترتيب):", options=words_list, key=f"ans_reorder_{idx}")
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

        # Results View
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
                is_correct = False
                
                if q_type in ["reorder", "fill_text", "box_complete"]:
                    if clean_text_for_grading(str(ans)) == clean_text_for_grading(str(correct)) and ans not in ["-- Select Word --", ""]:
                        is_correct = True
                else:
                    if str(ans).strip() == str(correct).strip() and ans not in ["-- Select Match --", None, ""]:
                        is_correct = True
                        
                if is_correct:
                    score += 1
                    st.success(f"**Q{idx + 1}: Correct ✅** (Your answer: {ans})")
                    breakdown_text += f"Q{idx+1}: Correct ✅\n"
                else:
                    st.error(f"**Q{idx + 1}: Incorrect ❌** | Your answer: {ans or 'None'} | **Model Answer:** {correct}")
                    breakdown_text += f"Q{idx+1}: Incorrect ❌ (Ans: {ans or 'None'} | Correct: {correct})\n"
                    
            percentage = round((score / total) * 100, 1)
            st.info(f"### 🏆 Final Score: {score} / {total} ({percentage}%)")
            breakdown_text += f"\n*Final Score:* {score}/{total} ({percentage}%)"
            
            record_submission(active_exam_key, full_exam_desc, active_student, active_phone, resolved_grade, score, total, percentage)
            
            teacher_phone = "201090570624"
            whatsapp_url = f"https://wa.me/{teacher_phone}?text={urllib.parse.quote(breakdown_text)}"
            
            st.markdown(f"""
                <div style="text-align: center; margin-top: 25px;">
                    <a href="{whatsapp_url}" target="_blank" style="background-color: #25D366; color: white; padding: 14px 28px; text-decoration: none; font-size: 17px; font-weight: bold; border-radius: 8px; display: inline-block;">
                        📲 Send Result to Mrs. Kheffa on WhatsApp
                    </a>
                </div>
            """, unsafe_allow_html=True)
elif resolved_grade:
    st.info(f"👋 لا يوجد اختبار نشط حالياً لصف **{resolved_grade}**. يرجى من المعلمة تفعيل الاختبار من لوحة التحكم.")

# --- TEACHER CONTROL PORTAL & SINGLE-GRADE FOCUS ARCHIVE ---
st.write("---")
with st.expander("🔒 Admin Portal & Exam Bank (لوحة تحكم المعلمة)", expanded=False):
    admin_pass = st.text_input("Enter Admin Password:", type="password", key="sec_admin_pass")
    
    if admin_pass == "admin":
        st.success("أهلاً بكِ مس خفة! لوحة تحكم بنظام الأسابيع الدراسية المخصصة (Week 1, Week 2...).")
        
        tab_weekly, tab_reports, tab_bank, tab_new = st.tabs([
            "🏆 أرشيف أوائل الأسابيع (Weekly Honor)", 
            "📊 كشوف الدرجات العامة", 
            "📚 استعراض بنك الاختبارات", 
            "➕ إضافة اختبار جديد لصف"
        ])
        
        # TAB 1: CUSTOM ACADEMIC WEEKLY HONOR ROLL
        with tab_weekly:
            st.markdown("### 🏆 أرشيف أوائل وتكريم كل أسبوع (Weekly Honor Roll)")
            subs = load_submissions()
            
            if subs:
                records = []
                for _, s_data in subs.items():
                    d_obj = extract_date_obj(s_data.get('timestamp', ''))
                    week_label, week_sort_idx = calculate_custom_academic_week(d_obj)
                        
                    records.append({
                        "اسم الطالب": s_data.get('full_name', ''),
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
                
                # Sort weeks logically (Week 1, Week 2...)
                weeks_df = df_weekly_all[["week_label", "week_idx"]].drop_duplicates().sort_values(by="week_idx", ascending=False)
                unique_weeks = weeks_df["week_label"].tolist()
                
                c_w1, c_w2 = st.columns([2.2, 1.2])
                chosen_week = c_w1.selectbox("📅 اختاري الأسبوع الدراسي المطلوب:", unique_weeks, key="sel_honor_week")
                filter_wk_grade = c_w2.selectbox("المرحلة:", ["جميع المراحل"] + GRADES_LIST, key="sel_honor_wk_grade")
                
                df_selected_week = df_weekly_all[df_weekly_all["week_label"] == chosen_week]
                if filter_wk_grade != "جميع المراحل":
                    df_selected_week = df_selected_week[df_selected_week["الصف الدراسي"] == filter_wk_grade]
                    
                df_selected_week = df_selected_week.sort_values(by=["النسبة", "الدرجة"], ascending=[False, False])
                
                if not df_selected_week.empty:
                    top_score_wk = df_selected_week["النسبة"].max()
                    top_wk_df = df_selected_week[df_selected_week["النسبة"] >= min(85.0, top_score_wk)].head(10)
                    
                    wk_winners = []
                    for _, r in top_wk_df.iterrows():
                        wk_winners.append({
                            "name": r["اسم الطالب"],
                            "grade": r["الصف الدراسي"],
                            "score": r["النسبة"],
                            "marks": f"{r['الدرجة']}/{r['المجموع']}"
                        })
                    
                    if wk_winners:
                        short_wk_title = chosen_week.split('(')[0].strip()
                        render_honor_card_widget(
                            f"🏆 أوائل {short_wk_title} - {filter_wk_grade}",
                            chosen_week,
                            wk_winners,
                            card_id="weekly-honor-card"
                        )
                    
                    st.write("---")
                    st.markdown(f"#### 📋 كشف المتفوقين المسجل لـ ({chosen_week}):")
                    
                    df_wk_display = df_selected_week.copy()
                    df_wk_display["النسبة المئوية"] = df_wk_display["النسبة"].apply(lambda x: f"{x}%")
                    df_wk_display = df_wk_display.drop(columns=["النسبة", "week_idx", "week_label"])
                    
                    st.dataframe(df_wk_display, use_container_width=True)
                    
                    clean_file_label = chosen_week.split(' ')[0] + "_" + chosen_week.split(' ')[1]
                    csv_wk_data = df_selected_week.drop(columns=["week_idx"]).to_csv(index=False).encode('utf-8-sig')
                    st.download_button(
                        label=f"📥 تحميل شيت أوائل ({clean_file_label}.csv)",
                        data=csv_wk_data,
                        file_name=f"Top_Achievers_{clean_file_label}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info(f"لا توجد نتائج مسجلة لـ {chosen_week}.")
            else:
                st.info("لا توجد تسليمات مسجلة لتوليد لوحة شرف الأسابيع بعد.")

        # TAB 2: GENERAL REPORTS
        with tab_reports:
            st.markdown("### 📊 كشوف الدرجات العامة وتصفية الاختبارات")
            subs = load_submissions()
            
            if subs:
                c_sel_gr, c_sel_ex = st.columns([1.5, 2])
                filter_grade = c_sel_gr.selectbox(
                    "اختر الصف الدراسي المطلوب:",
                    ["-- جميع المراحل معاً --"] + GRADES_LIST,
                    key="report_grade_filter"
                )
                
                records = []
                for _, s_data in subs.items():
                    records.append({
                        "اسم الطالب": s_data.get('full_name', ''),
                        "الصف الدراسي": s_data.get('grade', ''),
                        "رقم الهاتف": s_data.get('phone', ''),
                        "عنوان الاختبار": s_data.get('exam_title', s_data.get('exam_key', '')),
                        "الدرجة": s_data.get('score', 0),
                        "المجموع": s_data.get('total', 0),
                        "النسبة": s_data.get('percentage', 0),
                        "وقت التسليم": clean_time_display(s_data.get('timestamp', ''))
                    })
                df_all = pd.DataFrame(records)
                
                if filter_grade != "-- جميع المراحل معاً --":
                    df_filtered = df_all[df_all["الصف الدراسي"] == filter_grade]
                else:
                    df_filtered = df_all
                    
                available_exams = list(df_filtered["عنوان الاختبار"].unique())
                chosen_exam_title = "-- جميع اختبارات هذا الصف --"
                
                if len(available_exams) > 1:
                    filter_exam = c_sel_ex.selectbox(
                        "تصفية باختبار محدد:",
                        ["-- جميع اختبارات هذا الصف --"] + available_exams,
                        key="report_exam_filter"
                    )
                    chosen_exam_title = filter_exam
                    if filter_exam != "-- جميع اختبارات هذا الصف --":
                        df_filtered = df_filtered[df_filtered["عنوان الاختبار"] == filter_exam]
                else:
                    c_sel_ex.info("كل الاختبارات معروضة")
                    if len(available_exams) == 1:
                        chosen_exam_title = available_exams[0]
                
                df_filtered = df_filtered.sort_values(by=["النسبة", "الدرجة"], ascending=[False, False])
                
                if not df_filtered.empty:
                    top_threshold = df_filtered["النسبة"].max()
                    top_students_df = df_filtered[df_filtered["النسبة"] >= min(85.0, top_threshold)].head(8)
                    
                    winners = []
                    for _, r in top_students_df.iterrows():
                        winners.append({
                            "name": r["اسم الطالب"],
                            "grade": r["الصف الدراسي"],
                            "score": r["النسبة"],
                            "marks": f"{r['الدرجة']}/{r['المجموع']}"
                        })
                    
                    if winners:
                        render_honor_card_widget(
                            filter_grade if filter_grade != "-- جميع المراحل معاً --" else "All Grades (جميع المراحل)",
                            chosen_exam_title,
                            winners,
                            card_id="general-honor-card"
                        )
                    
                    st.write("---")
                    st.markdown("#### 📋 جدول تفريغ الدرجات الكامل:")
                    
                    df_display = df_filtered.copy()
                    df_display["النسبة المئوية"] = df_display["النسبة"].apply(lambda x: f"{x}%")
                    df_display = df_display.drop(columns=["النسبة"])
                    
                    st.dataframe(df_display, use_container_width=True)
                    
                    clean_gr_filename = filter_grade.split(' ')[0] if filter_grade != "-- جميع المراحل معاً --" else "All_Grades"
                    csv_data = df_filtered.to_csv(index=False).encode('utf-8-sig')
                    
                    st.download_button(
                        label=f"📥 تحميل كشف درجات ({clean_gr_filename}) بصيغة Excel / CSV",
                        data=csv_data,
                        file_name=f"Grades_{clean_gr_filename}_{datetime.now().strftime('%Y%m%d_%I%M%p')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info(f"لا توجد نتائج مسجلة لصف {filter_grade} حتى الآن.")
            else:
                st.info("لا توجد أي نتائج مسجلة في المنصة بعد.")

        # TAB 3: BROWSE EXAM BANK
        with tab_bank:
            st.markdown("### 🔍 اختاري الصف الدراسي المطلوب:")
            selected_manage_grade = st.selectbox("الصف المطلوب:", GRADES_LIST, key="sel_mgr_grade")
            
            short_c = [k for k, v in GRADES_MAP.items() if v == selected_manage_grade]
            sc_code = short_c[0] if short_c else "1"
            clean_short_grade = selected_manage_grade.split('(')[0].strip()
            group_link = f"https://mrs-kheffa-quiz.streamlit.app/?g={sc_code}"
            
            bank = load_exam_bank()
            active_map = load_active_grades()
            grade_exams = bank.get(selected_manage_grade, {})
            
            active_id = active_map.get(selected_manage_grade, list(grade_exams.keys())[-1] if grade_exams else "")
            active_obj = grade_exams.get(active_id)
            
            live_txt = f"[{active_obj.get('unit','')} - {active_obj.get('lesson','')}] {active_obj.get('title','')}" if active_obj else "لا يوجد اختبار نشط حالياً"
            st.markdown(f"""
            <div class="grade-focus-header">
                <h4 style="margin:0; color:#1E40AF;">📁 مجلد: {selected_manage_grade}</h4>
                <div style="margin-top:6px; font-size:0.95rem;">
                    🟢 <b>الامتحان المفتوح للطلاب حالياً:</b> <span style="color:#15803D; font-weight:bold;">{live_txt}</span><br>
                    🔗 <b>رابط الجروب العام:</b> <code>{group_link}</code>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if grade_exams:
                st.markdown(f"**سجل اختبارات هذا الصف مرتبة ومؤرخة بالروابط المرقمة ({len(grade_exams)} اختبارات):**")
                
                exam_items = list(grade_exams.items())
                for idx, (e_id, e_info) in enumerate(exam_items, 1):
                    is_current = (e_id == active_id)
                    u_lbl = e_info.get('unit', '')
                    l_lbl = e_info.get('lesson', '')
                    t_lbl = e_info.get('title', '')
                    num_q = len(e_info.get('questions', []))
                    
                    time_display_val = clean_time_display(e_info.get('created_at', ''))
                    numbered_quiz_url = f"https://mrs-kheffa-quiz.streamlit.app/?g={sc_code}&exam={idx}"
                    
                    card_class = "card-active" if is_current else "card-idle"
                    badge_html = '<span class="badge-active">🟢 شغال للطلبة الآن</span>' if is_current else '<span class="badge-idle">⏸️ محفوظ في الأرشيف</span>'
                    
                    st.markdown(f"""
                    <div class="{card_class}">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 8px;">
                            <span style="font-size:1.25rem; font-weight:800; color:#1E3A8A;">
                                <span class="grade-badge-title">{clean_short_grade}</span> 📝 الاختبار رقم ({idx}) &nbsp;—&nbsp; 🕒 {time_display_val}
                            </span>
                            {badge_html}
                        </div>
                        <div style="font-size:1.05rem; font-weight:600; color:#0F172A; margin-bottom: 8px;">
                            📌 <b>الوحدة والدرس:</b> [{u_lbl} - {l_lbl}] &nbsp;|&nbsp; <b>الموضوع:</b> {t_lbl} &nbsp;|&nbsp; <b>الأسئلة:</b> {num_q} سؤال
                        </div>
                        <div style="background:white; padding:7px 12px; border-radius:6px; border:1.5px solid #93C5FD; font-size:0.92rem;">
                            🔗 <b>رابط هذا الاختبار المرقم بالصف:</b> <code>{numbered_quiz_url}</code>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    c1, c2 = st.columns([3, 1])
                    if not is_current:
                        if c1.button(f"🚀 تشغيل الاختبار رقم ({idx}) لجروب الواتساب الآن", key=f"activate_{e_id}"):
                            set_active_exam_for_grade(selected_manage_grade, e_id)
                            st.success(f"تم تفعيل الاختبار رقم ({idx}) ليكون المتاح لجروب {selected_manage_grade}!")
                            st.rerun()
                    else:
                        c1.success(f"✅ الاختبار رقم ({idx}) هو المتاح حالياً لجميع طلاب الجروب")
                        
                    if c2.button(f"🗑️ حذف الاختبار ({idx})", key=f"del_{e_id}"):
                        del bank[selected_manage_grade][e_id]
                        save_exam_bank(bank)
                        st.rerun()
                    st.write("")
            else:
                st.info(f"لا توجد اختبارات محفوظة في مجلد {selected_manage_grade} بعد.")

        # TAB 4: ADD NEW EXAM
        with tab_new:
            st.markdown("#### 📝 تجهيز وحفظ اختبار جديد")
            c_g, c_u, c_l = st.columns([2, 1, 1])
            sel_grade = c_g.selectbox("الصف الدراسي المستهدف:", GRADES_LIST, key="new_exam_grade")
            quiz_unit = c_u.text_input("الوحدة (Unit):", "Unit 1", key="exam_unit_input")
            quiz_lesson = c_l.text_input("الدرس (Lesson):", "Lesson 1", key="exam_lesson_input")
            
            quiz_title = st.text_input("عنوان الاختبار أو موضوعه:", f"{quiz_unit} - {quiz_lesson} Assessment", key="exam_title_input")
            raw_text = st.text_area("ألصقي نص الأسئلة المنسقة هنا:", height=180, key="new_raw_text")
            
            col_save_draft, col_save_pub = st.columns([1, 1])
            save_as_draft = col_save_draft.button("📁 حفظ في الأرشيف فقط (بدون تفعيل حالياً)")
            save_and_pub = col_save_pub.button("🚀 حفظ وتفعيل للطلاب فوراً")
            
            if save_as_draft or save_and_pub:
                if raw_text.strip():
                    parsed = parse_text_locally(raw_text)
                    if parsed and len(parsed) > 0:
                        bank = load_exam_bank()
                        if sel_grade not in bank:
                            bank[sel_grade] = {}
                        
                        exam_id = f"exam_{int(datetime.now().timestamp())}"
                        bank[sel_grade][exam_id] = {
                            "title": quiz_title.strip(),
                            "unit": quiz_unit.strip(),
                            "lesson": quiz_lesson.strip(),
                            "grade": sel_grade,
                            "questions": parsed,
                            "created_at": get_current_egypt_time()
                        }
                        save_exam_bank(bank)
                        
                        if save_and_pub:
                            set_active_exam_for_grade(sel_grade, exam_id)
                            st.success(f"🎉 تم حفظ وتفعيل '{quiz_title}' لصف {sel_grade} فوراً بتوقيت مصر!")
                        else:
                            st.success(f"📁 تم حفظ '{quiz_title}' في مجلد {sel_grade} بنجاح كأرشيف للأسبوع القادم!")
                        st.rerun()
                    else:
                        st.error("يرجى التأكد من كتابة الأسئلة بالتنسيق المطلوب.")
                else:
                    st.error("يرجى لصق نص الأسئلة أولاً.")
    elif admin_pass:
        st.error("Incorrect password!")
