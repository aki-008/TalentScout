import streamlit as st 
import requests
import json
from datetime import datetime
import time
import os

st.set_page_config(
    page_icon="🌈",
    page_title="Hirebot - AI hiring assistant",
    layout="wide",
    initial_sidebar_state="collapsed"
)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Main app styling */
    .main {
        padding: 0rem 1rem;
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom header */
    .header-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    .header-title {
        color: white;
        font-size: 3rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .header-subtitle {
        color: rgba(255,255,255,0.9);
        font-size: 1.2rem;
        margin-top: 0.5rem;
        font-weight: 300;
    }
    
    /* Step indicators */
    .step-container {
        display: flex;
        justify-content: center;
        margin: 2rem 0;
        padding: 1rem;
        background: white;
        border-radius: 15px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.05);
    }
    
    .step {
        display: flex;
        align-items: center;
        margin: 0 1rem;
        padding: 0.5rem 1rem;
        border-radius: 25px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .step-active {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3);
    }
    
    .step-completed {
        background: linear-gradient(135deg, #56ab2f, #a8e6cf);
        color: white;
    }
    
    .step-pending {
        background: #f8f9fa;
        color: #6c757d;
    }
    
    /* Card styling */
    .card {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.08);
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        border-radius: 10px;
        border: 2px solid #e9ecef;
        padding: 0.75rem;
        font-size: 1rem;
        transition: border-color 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* File uploader styling */
    .stFileUploader > div {
        border: 2px dashed #667eea;
        border-radius: 15px;
        padding: 2rem;
        text-align: center;
        background: rgba(102, 126, 234, 0.05);
        transition: all 0.3s ease;
    }
    
    .stFileUploader > div:hover {
        background: rgba(102, 126, 234, 0.1);
    }
    
    /* Success/Error messages */
    .stSuccess {
        background: linear-gradient(135deg, #56ab2f, #a8e6cf);
        border-radius: 10px;
    }
    
    .stError {
        background: linear-gradient(135deg, #ff6b6b, #ffa8a8);
        border-radius: 10px;
    }
    
    /* Question cards */
    .question-card {
        background: linear-gradient(135deg, #f8f9fa, #ffffff);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
        box-shadow: 0 3px 10px rgba(0,0,0,0.05);
    }
    
    .question-title {
        font-weight: 600;
        color: #333;
        margin-bottom: 1rem;
        font-size: 1.1rem;
    }
    
    /* Evaluation results */
    .evaluation-container {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin: 2rem 0;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
    }
    
    .evaluation-title {
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 1rem;
        text-align: center;
    }
    
    .completion-message {
        background: rgba(255,255,255,0.1);
        padding: 1.5rem;
        border-radius: 10px;
        margin-top: 1.5rem;
        backdrop-filter: blur(10px);
    }
    
    /* Loading animation */
    .loading-container {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 2rem;
    }
    
    .loading-spinner {
        border: 4px solid #f3f3f3;
        border-top: 4px solid #667eea;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
</style>
""", unsafe_allow_html=True)

API_BASE_URL = os.getenv("HIREBOT_API_URL", "http://localhost:8000")

if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "user_name" not in st.session_state:
    st.session_state.user_name = ""
if "current_step" not in st.session_state:
    st.session_state.current_step = "start"
if "questions" not in st.session_state:
    st.session_state.questions = {}
if 'answers' not in st.session_state:
    st.session_state.answers = {}
if 'evaluation' not in st.session_state:
    st.session_state.evaluation = ""
if 'parsed_resume' not in st.session_state:
    st.session_state.parsed_resume = {}

def make_api_request(method, endpoint, **kwargs):
    try:
        url = f"{API_BASE_URL}{endpoint}"
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json() # forgot () here
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return None
    
def render_header():
    st.markdown("""
    <div class="header-container">
        <h1 class="header-title">🌈 Hirebot</h1>
        <p class="header-subtitle">AI-Powered Hiring Assistant</p>
    </div>
    """, unsafe_allow_html=True)

def render_step_indicator():
    steps = [
        ("start", "👋 Start"),
        ("resume_upload", "📜 Resume"),
        ("tech_questions", "⁉️ Questions"),
        ("evaluation", "📊 Evaluation")  # Changed from "evaluations"
    ]

    current_step = st.session_state.current_step

    step_html = '<div class="step-container">'  # Fixed typo (removed extra space)
    for step_key, step_label in steps:
        if step_key == current_step:
            step_class = "step step-active"
        else:
            # Check if current_step exists in steps
            current_step_index = next((i for i, (key, _) in enumerate(steps) if key == current_step), -1)
            current_key_index = steps.index((step_key, step_label))
            if current_step_index != -1 and current_key_index < current_step_index:
                step_class = "step step-completed"
            else:
                step_class = "step step-pending"

        step_html += f'<div class="{step_class}">{step_label}</div>'
    
    step_html += "</div>"
    st.markdown(step_html, unsafe_allow_html=True)

def start_session_page():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('### welcome to hirebot ! 🌈')
    st.markdown('let"s begin !' )

    user_name = st.text_input("Enter Your name",
                              placeholder= "Enter full name please !",
                              key= "user_name_input")
    
    if st.button("Start My Interview Session", key="start_session"):
        if user_name.strip():
            with st.spinner("Initializing your session...."):
                response = make_api_request(
                    "POST",
                    "/sessions/start", # spelling mistake was here
                    json={"user_name":user_name.strip()}
                )

                if response :
                    st.session_state.session_id = response["session_id"]
                    st.session_state.user_name = user_name.strip()
                    st.session_state.current_step = "resume_upload"

                    st.success("✨ Session started Sucessfully!")
                    st.markdown(f"**Greeting** {response['greeting']}")
                    time.sleep(1)
                    st.rerun()
        else:
            st.error("PLease enter your name to continue:")

    st.markdown("</div>", unsafe_allow_html=True)

def resume_upload_page():

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f"Hello {st.session_state.user_name}! ")
    st.markdown("Please upload resume in PDF format:")

    uploaded_file = st.file_uploader(
        "Choose your resume (PDF only )", 
        type= ["pdf"],
        help="Upload resume for evaluation"
    )

    if uploaded_file is not None:
        if st.button("Upload and process Resume", key="upload_resume"):
            with st.spinner("Processing..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                response = make_api_request(
                    "POST",
                    f'/sessions/{st.session_state.session_id}/upload-resume',
                    files=files
                )

                if response:
                    st.session_state.parsed_resume = response['parsed_resume'] #syntax error using ()
                    st.session_state.current_step = "tech_questions"
                    st.success(" Resume uploaded and parsed")

                    with st.expander("Parsed Resume"):
                        st.json(response["parsed_resume"])

                    time.sleep(1)
                    st.rerun()  # missing ()
    st.markdown("</div>", unsafe_allow_html=True)

def tech_questions_page():
    if not st.session_state.questions:
        with st.spinner("Generating personalized assessments...."):
            response = make_api_request(
                "GET",
                f'/sessions/{st.session_state.session_id}/tech-questions'
            )

            if response:
                st.session_state.questions = response["questions"]
    
    if st.session_state.questions:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("### Technical Questions ⁉️")
        st.markdown("Please answer the following questions.")

        answers = {}

        for i , (question_key, question_text) in enumerate(st.session_state.questions.items()):
            st.markdown(f"<div class='question-card'>", unsafe_allow_html=True)
            st.markdown(f"<div class='question-title'>Questions {i+1}:</div>", unsafe_allow_html=True)
            st.markdown(f"**{question_text}**")

            answer = st.text_area(
                f"Your Answer for Questions {i+1}",
                key = f"answer_{question_key}",
                height=100,
                placeholder=f"Type your answer here ..."

            )
            answers[question_key] = answer 
            st.markdown('</div>', unsafe_allow_html=True)

        if st.button("Submit all answers", key="Submit_answers"):
            if all(answer.strip() for answer in answers.values()):
                with st.spinner("Evaluating answers ..."):
                    response = make_api_request(
                        "POST",
                        f"/sessions/{st.session_state.session_id}/submit-answers",
                        json={
                            "session_id": st.session_state.session_id,
                            "answers":answers
                            }
                    )

                    if response:
                        st.session_state.answers = answers
                        st.session_state.evaluation = response['evaluation']
                        st.session_state.completion_message = response["completion_message"]
                        st.session_state.current_step = "evaluation"

                        st.success("Answers Submitted successfully")
                        time.sleep(1)
                        st.rerun()
            else:
                st.error("Please answer all the questions")
        
    st.markdown("</div>", unsafe_allow_html=True)   

def evaluation_page():
    st.markdown('<div class="evaluation-container">', unsafe_allow_html=True)
    st.markdown('<div class="evaluation-title">📊 Evaluation Results</div>', unsafe_allow_html=True)

    if st.session_state.evaluation:
        st.markdown("### Your Performance Analysis:")
        st.markdown(st.session_state.evaluation)

        if hasattr(st.session_state, "completion_message"):
            st.markdown('<div class="completion-message">', unsafe_allow_html=True)
            st.markdown("### Next Steps:")
            st.markdown(st.session_state.completion_message)
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Start New Session", key="New Session"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    with col2:
        if st.button("Get results", key="Get results"):
            result_data = {
                "user_name": st.session_state.user_name,
                "session_id": st.session_state.session_id,
                "evaluation": st.session_state.evaluation,
                "timestamp": datetime.now().isoformat()
            }

            st.download_button(
                label="Download report",
                data= json.dumps(result_data, indent=2),
                file_name= f"hirebot_evaluation_{st.session_state.user_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            
            )

def main():
    render_header()
    render_step_indicator()

    if st.session_state.current_step == "start":
        start_session_page()
    elif st.session_state.current_step == "resume_upload":
        resume_upload_page()
    elif st.session_state.current_step == "tech_questions":
        tech_questions_page()
    elif st.session_state.current_step == "evaluation":
        evaluation_page()

    with st.sidebar:
        st.markdown("### Session Info")
        if st.session_state.session_id:
            st.info(f"**Session ID:** {st.session_state.session_id[:8]}...")
            st.info(f"**User:** {st.session_state.user_name}")
            st.info(f"**Step:** {st.session_state.current_step}")
        else:
            st.warning("No active sessions")

        
        st.markdown("---")
        st.markdown("### About Hirebot")
        st.markdown("""
        🤖 **AI-Powered Hiring**

        Hirebot streamlines the hiring process using advanced AI to:
        - Parse and analyze resumes
        - Generate personalized technical questions
        - Evaluate candidate responses
        - Provide detailed feedback
        """)

if __name__ == "__main__":
    main()
