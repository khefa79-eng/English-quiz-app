import streamlit as st
import json
import os
import string
import re
import urllib.parse
from datetime import datetime
import pandas as pd

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
    .passage-box {
        background-color: #F8FAFC;
        border-left: 5px solid #3B82F6;
        padding: 18px;
        border-radius: 8px;
        margin-bottom: 18px;
        font-size: 1.05rem;
        line-height: 1.7;
        color: #1E293B;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
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

EXAM_BANK_FILE = "exam_bank.json"
ACTIVE_GRADES_FILE = "active_by_grade.json"
SUBMISSIONS_FILE = "submitted_students.json"

GRADES_LIST = [
    "Primary 1 (أولى ابتدائي)", "Primary 2 (تانية ابتدائي)", "Primary 3 (تالتة ابتدائي)",
    "Primary 4 (رابعة ابتدائي)", "Primary 5 (خامسة ابتدائي)", "Primary 6 (سادسة ابتدائي)",
    "Prep 1 (أولى إعدادي)", "Prep 2 (تانية إعدادي)", "Prep 3 (تالتة إعدادي)",
    "Secondary 1 (أولى ثانوي)", "Secondary 2 (تانية ثانوي)", "Secondary 3 (تالتة ثانوي)"
]

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

def record_submission(exam_key, student_name, student_phone, student_grade, score, total, percentage):
    submissions = load_submissions()
    clean_phone = re.sub(r'\D', '', student_phone)
    record_id = f"{exam_key}_{clean_phone}" if clean_phone else f"{exam_key}_{clean_text_for_grading(student_name)}"
    submissions[record_id] = {
        "exam_key": exam_key,
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

# --- MULTI-TRACK INDEPENDENT GRADE ROUTING ---
exam_bank = load_exam_bank()
active_grades_map = load_active_grades()
query_params = st.query_params

resolved_grade = None
selected_grade_param = query_params.get("grade", None)

if selected_grade_param:
    matched = [g for g in GRADES_LIST if selected_grade_param.lower().strip() in g.lower()]
    if matched:
        resolved_grade = matched[0]

# If no grade in URL, ask the student to select their grade
if not resolved_grade and 'student_chosen_grade' not in st.session_state:
    st.markdown("### 🎓 مرحباً بك في منصة التقييمات")
    st.info("يرجى اختيار صفك الدراسي لعرض الاختبار المخصص لك:")
    grade_selection = st.selectbox("اختر الصف الدراسي:", ["-- اختر الصف --"] + GRADES_LIST, key="direct_grade_select")
    if grade_selection != "-- اختر الصف --":
        if st.button("الانتقال للاختبار 🚀"):
            st.session_state['student_chosen_grade'] = grade_selection
            st.rerun()
elif not resolved_grade and 'student_chosen_grade' in st.session_state:
    resolved_grade = st.session_state['student_chosen_grade']

active_exam = None
active_exam_key = ""

if resolved_grade and resolved_grade in exam_bank:
    # 1. Check if an active exam is explicitly set for this grade
    target_eid = active_grades_map.get(resolved_grade)
    if target_eid and target_eid in exam_bank[resolved_grade]:
        active_exam = exam_bank[resolved_grade][target_eid]
        active_exam_key = f"{resolved_grade}_{target_eid}"
    elif len(exam_bank[resolved_grade]) > 0:
        # Fallback to the latest exam created for this grade
        latest_eid = list(exam_bank[resolved_grade].keys())[-1]
        active_exam = exam_bank[resolved_grade][latest_eid]
        active_exam_key = f"{resolved_grade}_{latest_eid}"

# --- STUDENT INTERFACE ---
if resolved_grade:
    if active_exam and active_exam.get("questions"):
        questions = active_exam["questions"]
        q_title = active_exam.get("title", "English Assessment")
        
        st.markdown(f"### 📝 {q_title}")
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
                        st.error(f"⚠️ عذراً يا {prev['full_name']}! لقد تم أداء هذا الاختبار مسبقاً بهذا الرقم/الاسم بتاريخ {prev['timestamp']}. لا يُسمح بإعادة الاختبار.")
                        st.info(f"🏆 **درجتك المسجلة:** {prev['score']} / {prev['total']} ({prev['percentage']}%)")
                        
                        teacher_phone = "201090570624"
                        wa_msg = f"*Exam:* {q_title}\n*Teacher:* Mrs. Kheffa Eletreby\n*Student:* {prev['full_name']}\n*Grade:* {resolved_grade}\n*Phone:* {prev.get('phone', '')}\n*Recorded Score:* {prev['score']}/{prev['total']} ({prev['percentage']}%)"
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
                
                breakdown_text = f"*Exam:* {q_title}\n*Teacher:* Mrs. Kheffa Eletreby\n*Student:* {active_student}\n*Grade:* {resolved_grade}\n*Phone:* {active_phone}\n"
                
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
                
                record_submission(active_exam_key, active_student, active_phone, resolved_grade, score, total, percentage)
                
                teacher_phone = "201090570624"
                whatsapp_url = f"https://wa.me/{teacher_phone}?text={urllib.parse.quote(breakdown_text)}"
                
                st.markdown(f"""
                    <div style="text-align: center; margin-top: 25px;">
                        <a href="{whatsapp_url}" target="_blank" style="background-color: #25D366; color: white; padding: 14px 28px; text-decoration: none; font-size: 17px; font-weight: bold; border-radius: 8px; display: inline-block;">
                            📲 Send Result to Mrs. Kheffa on WhatsApp
                        </a>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.info(f"👋 لا يوجد اختبار نشط حالياً لصف **{resolved_grade}**. يرجى من المعلمة تفعيل أو نشر الاختبار من لوحة التحكم.")

# --- HIDDEN TEACHER PORTAL & ARCHIVE MANAGER ---
st.write("---")
with st.expander("🔒 Admin Portal & Exam Bank", expanded=False):
    admin_pass = st.text_input("Enter Admin Password:", type="password", key="sec_admin_pass")
    
    if admin_pass == "admin":
        st.success("أهلاً بكِ مس خفة! لوحة إدارة وتخزين بنك الاختبارات المستقلة لكل مرحلة.")
        
        tab_new, tab_bank, tab_reports = st.tabs(["➕ إضافة اختبار جديد", "📚 بنك الاختبارات والتفعيل المستقل", "📊 التقارير والإكسيل"])
        
        with tab_new:
            sel_grade = st.selectbox("اختر الصف الدراسي للاختبار:", GRADES_LIST, key="new_exam_grade")
            quiz_title = st.text_input("Quiz Title (عنوان الاختبار):", f"{sel_grade.split(' ')[0]} - Assessment 1", key="exam_title_input")
            raw_text = st.text_area("Paste formatted questions text here:", height=200, key="new_raw_text")
            
            if st.button("💾 حفظ ونشر الاختبار لهذا الصف فوراً"):
                if raw_text.strip():
                    parsed = parse_text_locally(raw_text)
                    if parsed and len(parsed) > 0:
                        bank = load_exam_bank()
                        if sel_grade not in bank:
                            bank[sel_grade] = {}
                        
                        exam_id = f"exam_{int(datetime.now().timestamp())}"
                        bank[sel_grade][exam_id] = {
                            "title": quiz_title,
                            "grade": sel_grade,
                            "questions": parsed,
                            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                        }
                        save_exam_bank(bank)
                        set_active_exam_for_grade(sel_grade, exam_id)
                        st.success(f"🎉 تم حفظ ونشر '{quiz_title}' لصف **{sel_grade}** بنجاح دون التأثير على أي صف آخر!")
                        st.rerun()
                    else:
                        st.error("يرجى التأكد من كتابة الأسئلة بالتنسيق المطلوب.")
                else:
                    st.error("يرجى لصق نص الأسئلة.")

        with tab_bank:
            bank = load_exam_bank()
            active_map = load_active_grades()
            if bank:
                for gr_name, exams_dict in bank.items():
                    active_id_for_this = active_map.get(gr_name, list(exams_dict.keys())[-1] if exams_dict else "")
                    st.markdown(f"#### 📁 {gr_name} ({len(exams_dict)} اختبارات)")
                    for e_id, e_info in list(exams_dict.items()):
                        is_current = (e_id == active_id_for_this)
                        c1, c2, c3 = st.columns([3, 1, 1])
                        status_tag = "🟢 [النشط حالياً]" if is_current else "⚪"
                        c1.write(f"{status_tag} **{e_info['title']}** ({len(e_info['questions'])} أسئلة) - {e_info.get('created_at','')}")
                        if not is_current:
                            if c2.button("🚀 تفعيل لصفه", key=f"act_{e_id}"):
                                set_active_exam_for_grade(gr_name, e_id)
                                st.success(f"تم تفعيل {e_info['title']} ليكون الاختبار النشط لصف {gr_name}!")
                                st.rerun()
                        else:
                            c2.write("✅ نشط")
                        if c3.button("🗑️ حذف", key=f"del_{e_id}"):
                            del bank[gr_name][e_id]
                            save_exam_bank(bank)
                            st.rerun()
                    st.write("---")
            else:
                st.info("لا توجد اختبارات محفوظة في البنك بعد.")

        with tab_reports:
            subs = load_submissions()
            if subs:
                df_data = []
                for _, s_data in subs.items():
                    df_data.append({
                        "اسم الطالب": s_data.get('full_name', ''),
                        "الصف الدراسي": s_data.get('grade', ''),
                        "رقم الهاتف": s_data.get('phone', ''),
                        "الدرجة": s_data.get('score', 0),
                        "المجموع": s_data.get('total', 0),
                        "النسبة": f"{s_data.get('percentage', 0)}%",
                        "وقت التسليم": s_data.get('timestamp', '')
                    })
                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True)
                
                csv_data = df.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 تحميل كشف الدرجات الكامل (Excel / CSV)",
                    data=csv_data,
                    file_name=f"All_Grades_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("لا توجد نتائج مسجلة حتى الآن.")
    elif admin_pass:
        st.error("Incorrect password!")
