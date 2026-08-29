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
    cleaned = raw_text.replace("```json", "").replace("```", "").strip()
    return json.loads(cleaned)

def parse_text_locally(text):
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
    questions = []
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # 1. Matching
        if re.search(r'(?i)match\s*:', line):
            premise = re.sub(r'(?i)^\d+[\.\-]?\s*match\s*:\s*', '', line).strip()
            options, answer = [], ""
            i += 1
            while i < len(lines) and not re.match(r'^\d+[\.\-]', lines[i]):
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
            
        # 2. Reorder
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
            
        # 3. MCQ / Fill-in-the-blank
        elif re.match(r'^\d+[\.\-]', line):
            q_text = line
            options = []
            i += 1
            while i < len(lines) and re.match(r'^[a-dA-D][\.\)]', lines[i]):
                opt_val = re.sub(r'^[a-dA-D][\.\)]\s*', '', lines[i]).strip()
                options.append(opt_val)
                i += 1
            if options:
                questions.append({
                    "type": "mcq",
                    "question": q_text,
                    "options": options,
                    "answer": options[0]
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
            "Primary 1 (أولى ابتدائي)",
            "Primary 2 (تانية ابتدائي)",
            "Primary 3 (تالتة ابتدائي)",
            "Primary 4 (رابعة ابتدائي)",
            "Primary 5 (خامسة ابتدائي)",
            "Primary 6 (سادسة ابتدائي)",
            "Prep 1 (أولى إعدادي)",
            "Prep 2 (تانية إعدادي)",
            "Prep 3 (تالتة إعدادي)",
            "Secondary 1 (أولى ثانوي)",
            "Secondary 2 (تانية ثانوي)",
            "Secondary 3 (تالتة ثانوي)"
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
                    wa_msg = f"*Exam:* {q_title}\n*Teacher:* Mrs. Kheffa Eletreby\n*Student:* {prev['full_name']}\n*Grade:* {prev.get('grade', '')}\n*Phone:* {prev.get('phone', '')}\n*Recorded Score:* {prev['score']}/{prev['total']} ({prev['percentage']}%)"
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
                for idx, q in enumerate(questions):
                    q_type = q.get('type', 'mcq')
                    st.markdown(f"**Question {idx + 1} (1 Mark)**")
                    
                    if q_type == "reading" and "passage" in q:
                        st.info(f"📖 **Read the passage:**\n\n{q['passage']}")
                    
                    if q_type in ["mcq", "reading"]:
                        st.write(q.get('question', ''))
                        user_answers[idx] = st.radio("Choose correct answer:", options=q.get('options', []), key=f"ans_mcq_{idx}", index=None)
                    elif q_type == "fill_blank":
                        st.write(q.get('question', ''))
                        user_answers[idx] = st.selectbox("Select missing word:", options=["-- Select --"] + q.get('options', []), key=f"ans_fill_{idx}")
                    elif q_type == "matching":
                        st.write(f"🔹 Match: **{q.get('premise', '')}**")
                        user_answers[idx] = st.selectbox("Select match:", options=["-- Select Match --"] + q.get('options', []), key=f"ans_match_{idx}")
                    elif q_type == "reorder":
                        st.write(q.get('question', 'Rearrange the following words:'))
                        words_list = q.get('scrambled_words', [])
                        if words_list:
                            selected_words = st.multiselect("Select words in order:", options=words_list, key=f"ans_reorder_{idx}")
                            user_answers[idx] = " ".join(selected_words)
                        else:
                            user_answers[idx] = st.text_input("Write sentence in correct order:", key=f"ans_txt_reorder_{idx}")
                    st.write("---")
                    
                submit = st.form_submit_button("Submit Exam & View Results 📊")
                if submit:
                    st.session_state['exam_submitted'] = True
                    st.session_state['submitted_answers'] = user_answers
                    st.rerun()

        # Results
        if st.session_state.get('exam_submitted', False):
            st.subheader("📋 Results & Model Answers")
            score = 0
            total = len(questions)
            user_answers = st.session_state.get('submitted_answers', {})
            
            breakdown_text = f"*Exam:* {q_title}\n*Teacher:* Mrs. Kheffa Eletreby\n*Student:* {active_student}\n*Grade:* {active_grade}\n*Phone:* {active_phone}\n"
            
            for idx, q in enumerate(questions):
                q_type = q.get('type', 'mcq')
                ans = user_answers.get(idx, "")
                correct = q.get('answer', '')
                is_correct = False
                
                if q_type in ["reorder", "fill_blank"]:
                    if clean_text_for_grading(str(ans)) == clean_text_for_grading(str(correct)) and ans:
                        is_correct = True
                else:
                    if str(ans).strip() == str(correct).strip() and ans not in ["-- Select --", "-- Select Match --", None, ""]:
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
            
            record_submission(active_student, active_phone, active_grade, score, total, percentage)
            
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
    st.info("👋 لا يوجد اختبار نشط حالياً. يرجى الانتظار حتى تقوم المعلمة بنشر الاختبار.")

# --- HIDDEN TEACHER PORTAL ---
st.write("---")
with st.expander("🔒 Admin Portal", expanded=False):
    admin_pass = st.text_input("Enter Admin Password:", type="password", key="sec_admin_pass")
    
    if admin_pass == "admin":
        st.success("أهلاً بكِ مس خفة! هذه لوحة التحكم الخاصة بكِ فقط.")
        quiz_title = st.text_input("Quiz Title / Grade:", "Prep 1 - Assessment", key="exam_title_input")
        api_key = st.text_input("Gemini API Key (مطلوب فقط عند رفع ملف):", type="password", key="api_key_input")
        
        uploaded_file = st.file_uploader("Upload PDF or Image (اختياري):", type=["pdf", "png", "jpg", "jpeg"])
        raw_text = st.text_area("Or paste formatted questions text here (الأسرع والموصى به دائماً):", height=150)
        
        col_pub, col_rst = st.columns([2, 1])
        with col_pub:
            if st.button("🚀 Publish Exam to All Students"):
                if raw_text.strip() and uploaded_file is None:
                    parsed = parse_text_locally(raw_text)
                    if parsed and len(parsed) > 0:
                        save_exam_to_disk(quiz_title, parsed)
                        st.success(f"🎉 تم استخراج {len(parsed)} سؤال ونشر الاختبار '{quiz_title}' لجميع الطلاب فوراً!")
                        st.rerun()
                
                if not api_key:
                    st.error("يرجى إدخال Gemini API Key.")
                elif uploaded_file is None and not raw_text.strip():
                    st.error("يرجى إدخال نص الأسئلة أو رفع ملف.")
                else:
                    with st.spinner("Processing questions & publishing..."):
                        client = genai.Client(api_key=api_key)
                        prompt = """
                        Strictly extract and convert the provided English exam questions into a JSON array.
                        DO NOT add any questions outside the provided material.
                        
                        Return ONLY a raw JSON array:
                        [
                          {"type": "mcq", "question": "...", "options": ["A", "B", "C", "D"], "answer": "A"},
                          {"type": "fill_blank", "question": "...", "options": ["opt1", "opt2"], "answer": "opt1"},
                          {"type": "matching", "premise": "Item A", "options": ["Choice 1", "Choice 2"], "answer": "Choice 1"},
                          {"type": "reorder", "question": "Rearrange:", "scrambled_words": ["word1", "word2"], "answer": "word1 word2"}
                        ]
                        """
                        contents = [prompt]
                        if uploaded_file is not None:
                            bytes_data = uploaded_file.getvalue()
                            if uploaded_file.type == "application/pdf":
                                contents.append(types.Part.from_bytes(data=bytes_data, mime_type="application/pdf"))
                            elif uploaded_file.type.startswith("image/"):
                                contents.append(Image.open(uploaded_file))
                        if raw_text.strip():
                            contents.append(f"\n--- EXAM CONTENT ---\n{raw_text}")
                            
                        parsed = None
                        for attempt in range(3):
                            try:
                                res = client.models.generate_content(model="gemini-3.6-flash", contents=contents)
                                if res and res.text:
                                    parsed = extract_json_safely(res.text)
                                    if parsed:
                                        break
                            except Exception:
                                time.sleep(2)
                                
                        if parsed and len(parsed) > 0:
                            save_exam_to_disk(quiz_title, parsed)
                            st.success(f"🎉 تم نشر الاختبار '{quiz_title}' لجميع الطلاب بنجاح!")
                            st.rerun()
                        else:
                            st.error("تعذر المعالجة عبر الذكاء الاصطناعي حالياً. يرجى لصق نص الأسئلة المنسق مباشرة في المربع للتحويل الفوري!")

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
