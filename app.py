import streamlit as st
import json
import os
import re
import urllib.parse
from PIL import Image
import PyPDF2
from google import genai

# Page Configuration
st.set_page_config(
    page_title="Mrs. Kheffa Eletreby | English Assessments",
    page_icon="📝",
    layout="centered"
)

# Custom Teacher Header
st.markdown("""
    <div style="background: linear-gradient(135deg, #1E3A8A, #3B82F6); padding: 22px; border-radius: 12px; color: white; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center;">
        <h2 style="margin: 0; font-size: 26px;">🎓 English Assessment Platform</h2>
        <h3 style="margin: 6px 0; font-size: 19px; color: #E0E7FF;">Mrs. Kheffa Eletreby</h3>
        <p style="margin: 0; font-size: 15px; color: #DBEAFE;">Online English Teacher | 📱 WhatsApp: <b>01090570624</b></p>
    </div>
""", unsafe_allow_html=True)

QUIZ_FILE = "active_quiz.json"
TEACHER_PASSWORD = "admin"  # كلمة سر لوحة المعلمة

def save_quiz_data(data, title):
    payload = {
        "title": title,
        "questions": data
    }
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

def normalize_reorder(text):
    if not text:
        return ""
    cleaned = re.sub(r'[^\w\s]', '', text.lower())
    return " ".join(cleaned.split())

# Sidebar Navigation
st.sidebar.title("Navigation")
app_mode = st.sidebar.radio("Go to:", ["Student Area (الامتحان)", "Teacher Dashboard (لوحة المعلمة)"])

# ==========================================
# 1. TEACHER DASHBOARD
# ==========================================
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
                    You MUST strictly extract and use ONLY the exact questions provided in the user input / file / image.

                    Your task:
                    1. Read the provided text/image carefully.
                    2. Convert EVERY question from the teacher's input into the appropriate interactive format.
                    3. Determine the 100% correct model answer for each question.

                    Supported question formats:
                    - "mcq": For multiple choice questions. Keep original choices.
                    - "fill_blank": For sentences with blanks (e.g. using a word bank). Include the word bank options in "options".
                    - "reorder": For scrambled words that need rearranging.
                    - "matching": For Column A & Column B matching.
                    - "reading": For reading comprehension passages followed by their questions.

                    Return ONLY a valid JSON array of objects. No markdown formatting, no explanations.
                    Example JSON structure:
                    [
                      {"type": "mcq", "question": "Exact question text", "options": ["Option 1", "Option 2", "Option 3", "Option 4"], "answer": "Exact correct option"},
                      {"type": "fill_blank", "question": "The public garden is very popular ..... teenagers.", "options": ["with", "for", "at"], "answer": "with"},
                      {"type": "reorder", "question": "sports / play / you / Do / ?", "answer": "Do you play sports?"},
                      {"type": "matching", "premise": "Item from Column A", "options": ["Choice 1", "Choice 2"], "answer": "Choice 1"},
                      {"type": "reading", "passage": "Full passage text...", "question": "Question about passage", "options": ["A", "B", "C"], "answer": "A"}
                    ]
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

# ==========================================
# 2. STUDENT AREA
# ==========================================
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
                        st.write(q['question'])
                        user_answers[idx] = st.radio(
                            "Choose the correct answer:",
                            options=q.get('options', []),
                            key=f"stu_q_{idx}",
                            index=None
                        )
                    elif q_type == "fill_blank":
                        st.write(q['question'])
                        user_answers[idx] = st.selectbox(
                            "Select the missing word:",
                            options=["-- Select --"] + q.get('options', []),
                            key=f"stu_q_{idx}"
                        )
                    elif q_type == "matching":
                        st.write(f"Match: **{q.get('premise', '')}**")
                        user_answers[idx] = st.selectbox(
                            "Matches with:",
                            options=["-- Select Match --"] + q.get('options', []),
                            key=f"stu_q_{idx}"
                        )
                    elif q_type == "reorder":
                        st.write(q['question'])
                        user_answers[idx] = st.text_input(
                            "Type the correct sentence order:",
                            key=f"stu_q_{idx}"
                        )
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

        # Results & Model Answers
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
                if q_type == "reorder":
                    if normalize_reorder(ans) == normalize_reorder(correct):
                        is_correct = True
                else:
                    if ans == correct and ans not in ["-- Select --", "-- Select Match --", None]:
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
