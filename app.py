import streamlit as st
import json
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
    <div style="background: linear-gradient(135deg, #1E3A8A, #3B82F6); padding: 22px; border-radius: 12px; color: white; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <h2 style="margin: 0; font-size: 26px;">🎓 English Assessment Platform</h2>
        <h3 style="margin: 6px 0; font-size: 19px; color: #E0E7FF;">Mrs. Kheffa Eletreby</h3>
        <p style="margin: 0; font-size: 15px; color: #DBEAFE;">Online English Teacher | 📱 WhatsApp: <b>01090570624</b></p>
    </div>
""", unsafe_allow_html=True)

# Quiz Title & API Key Setup
col_t1, col_t2 = st.columns([2, 1])
with col_t1:
    quiz_title = st.text_input("Quiz Title / Grade:", "Connect / Connect Plus Assessment")
with col_t2:
    api_key = st.text_input("Gemini API Key:", type="password")

# Material Upload
st.subheader("1. Upload Questions / Exam Material")
uploaded_file = st.file_uploader("Upload PDF or Image (Exam / Worksheet):", type=["pdf", "png", "jpg", "jpeg"])
raw_text = st.text_area("Or paste questions text here:")

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

# Generate Quiz Button
if st.button("🚀 Generate Interactive Quiz"):
    if not api_key:
        st.error("Please enter your Gemini API key first.")
    elif not extracted_content and image_to_send is None:
        st.error("Please upload a file or paste exam questions first.")
    else:
        with st.spinner("AI is analyzing material and generating all question types..."):
            client = genai.Client(api_key=api_key)
            prompt = """
            You are an expert English language test creator for Egyptian curricula (Connect / Connect Plus / Prep).
            Extract or generate the exam questions from the material. You MUST cover diverse question types found in the input:
            1. "mcq" (Multiple Choice)
            2. "fill_blank" (Fill in the blanks using a given word-box/options)
            3. "reorder" (Rearrange words to make correct sentences)
            4. "matching" (Match Column A with Column B)
            5. "reading" (Passage followed by MCQs)

            Return ONLY a valid JSON array of objects. Do not add markdown code blocks or text outside JSON.
            Structure:
            [
              {
                "type": "mcq",
                "question": "Question text here?",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "answer": "Option A"
              },
              {
                "type": "fill_blank",
                "question": "Sentence with [blank] inside?",
                "options": ["word1", "word2", "word3"],
                "answer": "word1"
              },
              {
                "type": "reorder",
                "question": "Arrange: / words / separated / by / slash /",
                "answer": "Words separated by slash."
              },
              {
                "type": "matching",
                "premise": "Column A Item",
                "options": ["Match 1", "Match 2", "Match 3"],
                "answer": "Match 1"
              },
              {
                "type": "reading",
                "passage": "Passage text...",
                "question": "Question about passage?",
                "options": ["A", "B", "C"],
                "answer": "A"
              }
            ]
            """

            contents = [prompt]
            if image_to_send:
                contents.append(image_to_send)
            if extracted_content:
                contents.append(extracted_content)

            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=contents
                )
                clean_json = response.text.replace("```json", "").replace("```", "").strip()
                st.session_state['quiz_data'] = json.loads(clean_json)
                st.session_state['submitted'] = False
                st.success("Exam generated successfully! Student can now take the test.")
            except Exception as e:
                st.error(f"Error parsing exam data: {e}")

# Helper for Re-order normalization
def normalize_reorder(text):
    if not text:
        return ""
    cleaned = re.sub(r'[^\w\s]', '', text.lower())
    return " ".join(cleaned.split())

# Quiz Display & Taking Section
if 'quiz_data' in st.session_state and st.session_state['quiz_data']:
    st.write("---")
    st.subheader(f"📝 {quiz_title}")
    
    # Student Info
    student_name = st.text_input("Student Full Name (اسم الطالب رباعي):", key="student_name_input")
    
    if st.session_state.get('submitted', False):
        st.warning("⚠️ This exam has already been submitted and cannot be retaken in this session.")
    else:
        with st.form("student_exam_form"):
            user_answers = {}
            for idx, q in enumerate(st.session_state['quiz_data']):
                q_type = q.get('type', 'mcq')
                st.markdown(f"**Question {idx + 1} (1 Mark)**")
                
                if q_type == "reading" and "passage" in q:
                    st.info(f"📖 **Read the passage:**\n\n{q['passage']}")
                
                if q_type in ["mcq", "reading"]:
                    st.write(q['question'])
                    user_answers[idx] = st.radio(
                        "Choose the correct answer:",
                        options=q.get('options', []),
                        key=f"q_{idx}",
                        index=None
                    )
                elif q_type == "fill_blank":
                    st.write(q['question'])
                    user_answers[idx] = st.selectbox(
                        "Select the missing word:",
                        options=["-- Select --"] + q.get('options', []),
                        key=f"q_{idx}"
                    )
                elif q_type == "matching":
                    st.write(f"Match: **{q.get('premise', '')}**")
                    user_answers[idx] = st.selectbox(
                        "Matches with:",
                        options=["-- Select Match --"] + q.get('options', []),
                        key=f"q_{idx}"
                    )
                elif q_type == "reorder":
                    st.write(q['question'])
                    user_answers[idx] = st.text_input(
                        "Type the correct sentence order:",
                        key=f"q_{idx}"
                    )
                st.write("---")
                
            submit_exam = st.form_submit_button("Submit Exam & Calculate Score 📊")
            
            if submit_exam:
                if not student_name.strip():
                    st.error("Please enter the student's full name before submitting.")
                else:
                    st.session_state['submitted'] = True
                    st.session_state['answers'] = user_answers
                    st.session_state['final_student_name'] = student_name
                    st.rerun()

# Results and WhatsApp Sharing
if st.session_state.get('submitted', False) and 'quiz_data' in st.session_state:
    st.write("---")
    st.subheader("📋 Detailed Result & Model Answers")
    
    score = 0
    total = len(st.session_state['quiz_data'])
    user_answers = st.session_state.get('answers', {})
    s_name = st.session_state.get('final_student_name', 'Student')
    
    breakdown_text = f"*Exam:* {quiz_title}\n*Teacher:* Mrs. Kheffa Eletreby\n*Student:* {s_name}\n"
    
    for idx, q in enumerate(st.session_state['quiz_data']):
        q_type = q.get('type', 'mcq')
        ans = user_answers.get(idx, "")
        correct = q.get('answer', '')
        
        # Grading logic
        is_correct = False
        if q_type == "reorder":
            if normalize_reorder(ans) == normalize_reorder(correct):
                is_correct = True
        else:
            if ans == correct and ans not in ["-- Select --", "-- Select Match --", None]:
                is_correct = True
                
        if is_correct:
            score += 1
            st.success(f"**Q{idx + 1}: Correct ✅** | Your answer: {ans}")
            breakdown_text += f"Q{idx+1}: Correct ✅\n"
        else:
            st.error(f"**Q{idx + 1}: Incorrect ❌** | Your answer: {ans or 'No Answer'} | **Model Answer:** {correct}")
            breakdown_text += f"Q{idx+1}: Incorrect ❌ (Ans: {ans or 'None'} | Correct: {correct})\n"
            
    percentage = round((score / total) * 100, 1)
    st.info(f"### 🏆 Final Score: {score} / {total} ({percentage}%)")
    
    breakdown_text += f"\n*Final Score:* {score}/{total} ({percentage}%)"
    
    # WhatsApp Direct Send Link
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