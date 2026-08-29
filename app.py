import streamlit as st
import json
import os
import re
import string
import urllib.parse
from PIL import Image
import PyPDF2
from google import genai

# Page Configuration
st.set_page_config(
    page_title="Mrs. Kheffa Eletreby | English Assessments",
    page_icon="📝",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Responsive Custom Styles
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

QUIZ_FILE = "active_quiz.json"
TEACHER_PASSWORD = "admin"

def save_quiz_data(data, title):
    payload = {"title": title, "questions": data}
    with open(QUIZ_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

def load_quiz_data():
    if os.path.exists(QUIZ_FILE):
        try:
            with open(QUIZ_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None

def clean_text_for_grading(text):
    if not text:
        return ""
    text = text.translate(str.maketrans('', '', string.punctuation + '؟،؛«»ـ'))
    text = text.lower()
    return " ".join(text.split())

st.sidebar.title("Navigation")
app_mode = st.sidebar.radio("Go to:", ["Student Area (الامتحان)", "Teacher Dashboard (لوحة المعلمة)"])

# 1. TEACHER DASHBOARD
if app_mode == "Teacher Dashboard (لوحة المعلمة)":
    st.subheader("🔒 Teacher Control Panel")
    pwd = st.text_input("Enter Teacher Password:", type="password")
    
    if pwd == TEACHER_PASSWORD:
        st.success("Welcome, Mrs. Kheffa! You can now publish your exact quiz.")
        
        quiz_title = st.text_input("Quiz Title / Grade:", "Prep 2 - Unit Assessment")
        api_key = st.text_input("Gemini API Key:", type="password")
        
        uploaded_file = st.file_uploader("Upload PDF or Image (Exam / Worksheet):", type=["pdf", "png", "jpg", "jpeg"])
        raw_text = st.text_area("Or paste questions text here:", height=180)
        
        extracted_content = ""
        image_to_send = None
        
        if uploaded_file is not None:
            if uploaded_file.type == "application/pdf":
                reader = PyPDF2.PdfReader(uploaded_file)
                for page in reader.pages:
                    extracted_content += (page.extract_text() or "") + "\n"
            elif uploaded_file.type.startswith("image/"):
                image_to_send = Image.open(uploaded_file)
        
        if raw_text:
            extracted_content += "\n" + raw_text
            
        if st.button("🚀 Publish Exact Quiz for Students"):
            if not api_key:
                st.error("Please enter your Gemini API key.")
            elif not extracted_content and image_to_send is None:
                st.error("Please provide exam content (upload a file or paste text).")
            else:
                with st.spinner("Processing your exact questions..."):
                    client = genai.Client(api_key=api_key)
                    prompt = """
                    CRITICAL INSTRUCTION:
                    You are a strict exam transcriber and parser.
                    DO NOT invent, generate, hallucinate, or add any new questions of your own.
                    Extract and use ONLY the exact questions provided in the user input / file / image.

                    Convert each question into one of the following JSON structures:
                    1. "mcq": For multiple choice questions. Keep original choices.
                    2. "fill_blank": Sentences with missing words. Include the word bank options in "options".
                    3. "reorder": Scrambled words. Include "scrambled_words" as an array of the words to rearrange, and "answer" as the full correct sentence.
                    4. "matching": Column A item in "premise", all Column B options in "options", correct match in "answer".
                    5. "reading": Passage in "passage", question in "question", choices in "options", correct in "answer".

                    Return ONLY a valid JSON array of objects without markdown blocks.
                    """
                    contents = [prompt]
                    if image_to_send:
                        contents.append(image_to_send)
                    if extracted_content:
                        contents.append(f"\n--- TEACHER'S EXACT EXAM CONTENT ---\n{extracted_content}")
                        
                    try:
                        response = client.models.generate_content(
                            model="gemini-3.6-flash",
                            contents=contents
                        )
                        clean_json = response.text.replace("```json", "").replace("```", "").strip()
                        quiz_json = json.loads(clean_json)
                        save_quiz_data(quiz_json, quiz_title)
                        st.success(f"🎉 Quiz '{quiz_title}' with YOUR EXACT questions has been published successfully!")
                    except Exception as e:
                        st.error(f"Error publishing quiz: {e}")
    elif pwd:
        st.error("Incorrect password!")

# 2. STUDENT AREA
else:
    active_quiz = load_quiz_data()
    
    if not active_quiz or not active_quiz.get("questions"):
        st.info("👋 No active exam right now. Please check back later or contact Mrs. Kheffa.")
    else:
        q_title = active_quiz.get("title", "English Assessment")
        questions = active_quiz.get("questions", [])
        
        st.subheader(f"📝 {q_title}")
        student_name = st.text_input("Student Full Name (اسم الطالب رباعي):", key="stu_name")
        
        if st.session_state.get('submitted', False):
            st.warning("⚠️ You have already submitted this exam.")
        else:
            with st.form("exam_form"):
                user_answers = {}
                for idx, q in enumerate(questions):
                    q_type = q.get('type', 'mcq')
                    st.markdown(f"**Question {idx + 1} (1 Mark)**")
                    
                    if q_type == "reading" and "passage" in q:
                        st.info(f"📖 **Read the passage:**\n\n{q['passage']}")
                    
                    if q_type in ["mcq", "reading"]:
                        st.write(q.get('question', ''))
                        user_answers[idx] = st.radio("Choose the correct answer:", options=q.get('options', []), key=f"stu_q_{idx}", index=None)
                    elif q_type == "fill_blank":
                        st.write(q.get('question', ''))
                        user_answers[idx] = st.selectbox("Select the missing word:", options=["-- Select --"] + q.get('options', []), key=f"stu_q_{idx}")
                    elif q_type == "matching":
                        st.write(f"🔹 Match: **{q.get('premise', '')}**")
                        user_answers[idx] = st.selectbox("Select correct match:", options=["-- Select Match --"] + q.get('options', []), key=f"stu_q_{idx}")
                    elif q_type == "reorder":
                        st.write(q.get('question', 'Rearrange the following words:'))
                        words_list = q.get('scrambled_words', [])
                        if words_list:
                            selected_words = st.multiselect("Word order:", options=words_list, key=f"stu_reorder_{idx}")
                            user_answers[idx] = " ".join(selected_words)
                        else:
                            user_answers[idx] = st.text_input("Type the sentence in correct order:", key=f"stu_text_reorder_{idx}")
                    st.write("---")
                    
                submit_btn = st.form_submit_button("Submit Exam & View Results 📊")
                
                if submit_btn:
                    if not student_name.strip():
                        st.error("Please enter your full name before submitting!")
                    else:
                        st.session_state['submitted'] = True
                        st.session_state['answers'] = user_answers
                        st.session_state['final_student_name'] = student_name
                        st.rerun()

        # Grading
        if st.session_state.get('submitted', False):
            st.write("---")
            st.subheader("📋 Results & Model Answers")
            score = 0
            total = len(questions)
            user_answers = st.session_state.get('answers', {})
            s_name = st.session_state.get('final_student_name', 'Student')
            breakdown_text = f"*Exam:* {q_title}\n*Teacher:* Mrs. Kheffa Eletreby\n*Student:* {s_name}\n"
            
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
            
            teacher_phone = "201090570624"
            encoded_msg = urllib.parse.quote(breakdown_text)
            whatsapp_url = f"https://wa.me/{teacher_phone}?text={encoded_msg}"
            
            st.markdown(f"""
                <div style="text-align: center; margin-top: 25px;">
                    <a href="{whatsapp_url}" target="_blank" style="background-color: #25D366; color: white; padding: 14px 28px; text-decoration: none; font-size: 17px; font-weight: bold; border-radius: 8px; display: inline-block; box-shadow: 0 4px 6px rgba(0,0,0,0.15);">
                        📲 Send Result to Mrs. Kheffa on WhatsApp
                    </a>
                </div>
            """, unsafe_allow_html=True)
