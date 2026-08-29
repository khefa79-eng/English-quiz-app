import streamlit as st
import json
import string
import re
import urllib.parse
from PIL import Image
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

def clean_text_for_grading(text):
    if not text:
        return ""
    text = text.translate(str.maketrans('', '', string.punctuation + '؟،؛«»ـ'))
    text = text.lower()
    return " ".join(text.split())

def extract_json_safely(raw_text):
    match = re.search(r'\[.*\]', raw_text, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    cleaned = raw_text.replace("```json", "").replace("```", "").strip()
    return json.loads(cleaned)

# Teacher Control Panel
with st.expander("⚙️ Teacher Control Panel (إعداد وتوليد الاختبار)", expanded=('quiz_data' not in st.session_state)):
    pwd = st.text_input("Enter Teacher Password:", type="password", key="admin_pwd")
    
    if pwd == "admin":
        st.success("لوحة التحكم جاهزة! أدخلي البيانات واضغطي توليد.")
        quiz_title = st.text_input("Quiz Title / Grade:", "Prep 1 - Assessment", key="exam_title_input")
        api_key = st.text_input("Gemini API Key:", type="password", key="api_key_input")
        
        uploaded_file = st.file_uploader("Upload PDF or Image:", type=["pdf", "png", "jpg", "jpeg"])
        raw_text = st.text_area("Or paste questions text here:", height=150)
        
        if st.button("🚀 Generate & Publish Exam"):
            if not api_key:
                st.error("Please enter your Gemini API Key.")
            elif uploaded_file is None and not raw_text.strip():
                st.error("Please provide exam content (upload file or paste text).")
            else:
                with st.spinner("Processing your exact questions..."):
                    client = genai.Client(api_key=api_key)
                    prompt = """
                    Strictly extract and convert the provided English exam questions into a JSON array.
                    DO NOT add any questions outside the provided material.
                    
                    Return ONLY a raw JSON array like:
                    [
                      {
                        "type": "mcq",
                        "question": "1- Eating while looking at something on my ..... is a bad habit.",
                        "options": ["oven", "table", "screen", "school"],
                        "answer": "screen"
                      },
                      {
                        "type": "fill_blank",
                        "question": "The public garden is very popular ..... teenagers.",
                        "options": ["with", "for", "at"],
                        "answer": "with"
                      },
                      {
                        "type": "matching",
                        "premise": "Librarian",
                        "options": ["A person who helps in a library", "A person who flies planes"],
                        "answer": "A person who helps in a library"
                      },
                      {
                        "type": "reorder",
                        "question": "Rearrange the words:",
                        "scrambled_words": ["play", "sports", "you", "Do"],
                        "answer": "Do you play sports"
                      }
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
                        
                    # Multi-model retry to prevent 503 errors
                    models_to_try = ["gemini-2.5-flash", "gemini-3.6-flash", "gemini-1.5-flash"]
                    response_text = None
                    last_error = None
                    
                    for m in models_to_try:
                        try:
                            res = client.models.generate_content(model=m, contents=contents)
                            if res and res.text:
                                response_text = res.text
                                break
                        except Exception as e:
                            last_error = e
                            continue
                            
                    if response_text:
                        try:
                            parsed = extract_json_safely(response_text)
                            if parsed and len(parsed) > 0:
                                st.session_state['quiz_data'] = parsed
                                st.session_state['current_title'] = quiz_title
                                st.session_state['exam_submitted'] = False
                                st.success(f"🎉 تم استخراج {len(parsed)} سؤال بنجاح! انزلي لأسفل للبدء.")
                                st.rerun()
                            else:
                                st.error("لم يتم العثور على أسئلة داخل الملف. يرجى تجربة لصق نص الأسئلة مباشرة.")
                        except Exception as parse_err:
                            st.error(f"Error parsing response: {parse_err}")
                    else:
                        st.error(f"حدث ضغط مؤقت في السيرفر: {last_error}")
    elif pwd:
        st.error("Incorrect password!")

# Student Interactive View
if 'quiz_data' in st.session_state and len(st.session_state['quiz_data']) > 0:
    questions = st.session_state['quiz_data']
    q_title = st.session_state.get('current_title', 'English Assessment')
    
    st.write("---")
    st.subheader(f"📝 {q_title}")
    
    student_name = st.text_input("Student Full Name (اسم الطالب رباعي):", key="student_full_name")
    
    if not st.session_state.get('exam_submitted', False):
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
                if not student_name.strip():
                    st.error("Please enter your full name first!")
                else:
                    st.session_state['exam_submitted'] = True
                    st.session_state['submitted_answers'] = user_answers
                    st.rerun()

    # Results Section
    if st.session_state.get('exam_submitted', False):
        st.subheader("📋 Results & Model Answers")
        score = 0
        total = len(questions)
        user_answers = st.session_state.get('submitted_answers', {})
        s_name = student_name or "Student"
        
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
        whatsapp_url = f"https://wa.me/{teacher_phone}?text={urllib.parse.quote(breakdown_text)}"
        
        st.markdown(f"""
            <div style="text-align: center; margin-top: 25px;">
                <a href="{whatsapp_url}" target="_blank" style="background-color: #25D366; color: white; padding: 14px 28px; text-decoration: none; font-size: 17px; font-weight: bold; border-radius: 8px; display: inline-block;">
                    📲 Send Result to Mrs. Kheffa on WhatsApp
                </a>
            </div>
        """, unsafe_allow_html=True)
