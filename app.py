import streamlit as st
import json
import os
import string
import re
import random
import urllib.parse
from datetime import datetime
import pandas as pd

st.set_page_config(
    page_title="Mrs. Kheffa Eletreby | English Assessments",
    page_icon="📝",
    layout="centered"
)

# Custom Styling
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
    text = text.translate(str.maketrans('', '', string.punctuation + '؟،؛«»ـ“”‘’'))
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
        
        # 1. Passage Section
        if re.match(r'(?i)^passage\s*:\s*', line):
            current_passage = re.sub(r'(?i)^passage\s*:\s*', '', line).strip()
            i += 1
            while i < len(lines) and not re.match(r'^\d+[\.\-]', lines[i]) and not re.search(r'(?i)^(match|words|box)\s*:', lines[i]):
                current_passage += " " + lines[i]
                i += 1
            continue

        # 2. Word Box for Fill in the Blanks
        if re.match(r'(?i)^box\s*:\s*', line):
            raw_box = re.sub(r'(?i)^box\s*:\s*', '', line).strip('[] ')
            current_box_words = [w.strip().strip('"\'') for w in raw_box.split(',') if w.strip()]
            i += 1
            continue

        # 3. Matching
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

        # 4. Reorder (With Scramble Protection)
        elif re.search(r'(?i)words\s*:', line):
            words_raw = re.search(r'\[(.*?)\]', line)
            words = [w.strip().strip('"\'') for w in words_raw.group(1).split(',')] if words_raw else []
            answer = ""
            i += 1
            if i < len(lines) and re.search(r'(?i)^answer\s*:', lines[i]):
                answer = re.sub(r'(?i)^answer\s*:\s*', '', lines[i]).strip()
                i += 1
            if words:
                correct_ans = answer if answer else " ".join(words)
                # Shuffle words if given in correct order so the student has to reorder
                shuffled_words = list(words)
                if len(shuffled_words) > 1 and " ".join(shuffled_words).lower() == correct_ans.lower():
                    random.shuffle(shuffled_words)
                questions.append({
                    "type": "reorder",
                    "question": "Rearrange the words to make a correct sentence:",
                    "scrambled_words": shuffled_words,
                    "answer": correct_ans
                })
            continue

        # 5. Standard Questions (MCQ, Passage MCQ, Fill from Box)
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

# --- STUDENT INTERFACE ---
active_exam = load_exam_from_disk()

if active_exam and active_exam.get("questions"):
    questions = active_exam["questions"]
    q_title = active_exam.get("title", "English Assessment")
    
    st.subheader(f"📝 {q_title}")
    
    if 'current_verified_student' not in st.session_state:
        st.markdown("### 👤 تسجيل دخول الطالب")
        stu_name = st.text_input("اسم الطالب رباعي (Student Full Name):", key="gate_student_name")
        stu_phone = st.text_input("رقم تليفون الطالب أو ولي الأمر (Phone Number):", key="gate_student_phone")
        stu_grade = st.selectbox("الصف الدراسي (Grade):", [
            "-- اختر الصف الدراسي --",
            "Primary 1 (أولى ابتدائي)", "Primary 2 (تانية ابتدائي)", "Primary 3 (تالتة ابتدائي)",
            "Primary 4 (رابعة ابتدائي)", "Primary 5 (خامسة ابتدائي)", "Primary 6 (سادسة ابتدائي)",
            "Prep 1 (أولى إعدادي)", "Prep 2 (تانية إعدادي)", "Prep 3 (تالتة إعدادي)",
            "Secondary 1 (أولى ثانوي)", "Secondary 2 (تانية ثانوي)", "Secondary 3 (تالتة ثانوي)"
        ], key="gate_student_grade")
        
        start_btn = st.button("🚀 بدء الاختبار (Start Exam)")
        
        if start_btn:
            clean_phone_input = re.sub(r'\D', '', stu_phone)
            if not stu_name.strip():
                st.error("يرجى كتابة الاسم رباعي للمتابعة!")
            elif not clean_phone_input or len(clean_phone_input) < 10:
                st.error("يرجى كتابة رقم هاتف صحيح مكون من 11 رقماً!")
            elif stu_grade == "-- اختر الصف الدراسي --":
                st.error("يرجى اختيار الصف الدراسي!")
            else:
                norm_name = clean_text_for_grading(stu_name)
                all_subs = load_submissions()
                
                if clean_phone_input in all_subs or norm_name in all_subs:
                    prev = all_subs.get(clean_phone_input, all_subs.get(norm_name))
                    st.error(f"⚠️ عذراً يا {prev['full_name']}! لقد تم أداء هذا الاختبار مسبقاً بهذا الرقم/الاسم بتاريخ {prev['timestamp']}. لا يُسمح بإعادة الاختبار.")
                    st.info(f"🏆 **درجتك المسجلة:** {prev['score']} / {prev['total']} ({prev['percentage']}%)")
                    
                    teacher_phone = "201090570624"
                    wa_msg = f"السلام عليكم مس خفـة الاتربي ، أنا الطالب(ة): {prev['full_name']}\nالصف: {prev.get('grade','')}\nلقد انتهيت من حل اختبار: {q_title}\nدرجتي: {prev['score']} من {prev['total']} ({prev['percentage']}%)."
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
                    st.session_state['current_verified_grade'] = stu_grade
                    st.rerun()
    else:
        active_student = st.session_state['current_verified_student']
        active_phone = st.session_state['current_verified_phone']
        active_grade = st.session_state['current_verified_grade']
        
        if not st.session_state.get('exam_submitted', False):
            st.info(f"مرحباً بك يا **{active_student}** ({active_grade})! أجب عن جميع الأسئلة ثم اضغط Submit Exam.")
            
            with st.form("interactive_exam_form"):
                user_answers = {}
                displayed_passages = set()
                displayed_boxes = set()
                
                for idx, q in enumerate(questions):
                    q_type = q.get('type', 'mcq')
                    st.markdown(f"**Question {idx + 1} (1 Mark)**")
                    
                    # Reading Passage Display with Audio Player
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

                    # Word Box for Read & Complete
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
                    
                    # Controls
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

        # Results & Model Answers (On-screen Model Answers for Student)
        if st.session_state.get('exam_submitted', False):
            st.subheader("📋 Results & Model Answers")
            score = 0
            total = len(questions)
            user_answers = st.session_state.get('submitted_answers', {})
            
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
                else:
                    st.error(f"**Q{idx + 1}: Incorrect ❌** | Your answer: {ans or 'None'} | **Model Answer:** {correct}")
                    
            percentage = round((score / total) * 100, 1)
            st.info(f"### 🏆 Final Score: {score} / {total} ({percentage}%)")
            
            # Record submission to disk
            record_submission(active_student, active_phone, active_grade, score, total, percentage)
            
            # Short & Elegant WhatsApp Message for the Teacher
            clean_wa_text = f"السلام عليكم مس خفـة الاتربي ، أنا الطالب(ة): {active_student}\nالصف: {active_grade} | هاتف: {active_phone}\nلقد انتهيت من حل اختبار: {q_title}\nدرجتي: {score} من {total} ({percentage}%)."
            
            teacher_phone = "201090570624"
            whatsapp_url = f"https://wa.me/{teacher_phone}?text={urllib.parse.quote(clean_wa_text)}"
            
            st.markdown(f"""
                <div style="text-align: center; margin-top: 25px;">
                    <a href="{whatsapp_url}" target="_blank" style="background-color: #25D366; color: white; padding: 14px 28px; text-decoration: none; font-size: 17px; font-weight: bold; border-radius: 8px; display: inline-block;">
                        📲 إرسال النتيجة إلى مس خفة على الواتساب
                    </a>
                </div>
            """, unsafe_allow_html=True)
else:
    st.info("👋 لا يوجد اختبار نشط حالياً. يرجى الانتظار حتى تقوم المعلمة بنشر الاختبار.")

# --- HIDDEN TEACHER PORTAL ---
st.write("---")
with st.expander("🔒 Admin Portal", expanded=False):
    admin_pass = st.text_input("Enter Admin Password:", type="password", key="sec_admin_pass")
    
    if admin_pass == "admin":
        st.success("أهلاً بكِ مس خفة! هذه لوحة التحكم الخاصة بكِ.")
        quiz_title = st.text_input("Quiz Title / Grade:", "Prep 1 - Assessment", key="exam_title_input")
        raw_text = st.text_area("Paste formatted questions text here:", height=220)
        
        col_pub, col_rst = st.columns([2, 1])
        with col_pub:
            if st.button("🚀 Publish Exam to All Students"):
                if raw_text.strip():
                    parsed = parse_text_locally(raw_text)
                    if parsed and len(parsed) > 0:
                        save_exam_to_disk(quiz_title, parsed)
                        st.success(f"🎉 تم استخراج {len(parsed)} سؤال ونشر الاختبار '{quiz_title}' لجميع الطلاب فوراً!")
                        st.rerun()
                    else:
                        st.error("يرجى التأكد من كتابة الأسئلة بالتنسيق المطلوب.")
                else:
                    st.error("يرجى لصق نص الأسئلة أولاً.")

        with col_rst:
            if st.button("🔄 Reset All Student Submissions"):
                if os.path.exists(SUBMISSIONS_FILE):
                    os.remove(SUBMISSIONS_FILE)
                st.info("تم تصفير سجل الطلاب؛ يمكنهم الحل مجدداً.")

        subs = load_submissions()
        if subs:
            st.write("---")
            st.markdown(f"### 📊 كشف درجات الطلاب المكتملة ({len(subs)} طالب)")
            
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
                label="📥 تحميل كشف الدرجات (Excel / CSV)",
                data=csv_data,
                file_name=f"Grades_{quiz_title}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    elif admin_pass:
        st.error("Incorrect password!")
