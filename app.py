# app.py - Main Streamlit Application

import streamlit as st
import os
from dotenv import load_dotenv
from interview_agent import InterviewAgent
import json
from datetime import datetime

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="AI Interview Coach",
    page_icon="🎯",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #1e3c72, #2a5298);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .score-card {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .feedback-good {
        background: #d4edda;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #28a745;
    }
    .feedback-improve {
        background: #fff3cd;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #ffc107;
    }
    .stButton button {
        background-color: #2a5298;
        color: white;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'agent' not in st.session_state:
    # Get API key from multiple sources
    api_key = os.getenv('GEMINI_API_KEY', '')
    
    if not api_key:
        try:
            api_key = st.secrets.get('GEMINI_API_KEY', '')
        except:
            pass
    
    if not api_key:
        st.error("⚠️ API key not configured. Please add your Gemini API key.")
        st.info("Get your free API key from: https://makersuite.google.com/app/apikey")
        st.stop()
    
    # Initialize the agent with the API key
    st.session_state.agent = InterviewAgent(api_key)

if 'questions' not in st.session_state:
    st.session_state.questions = []
if 'current_q_index' not in st.session_state:
    st.session_state.current_q_index = 0
if 'answers' not in st.session_state:
    st.session_state.answers = []
if 'session_started' not in st.session_state:
    st.session_state.session_started = False
if 'session_completed' not in st.session_state:
    st.session_state.session_completed = False
if 'role' not in st.session_state:
    st.session_state.role = None
if 'difficulty' not in st.session_state:
    st.session_state.difficulty = None

# Header
st.markdown('<div class="main-header"><h1>🎯 AI Interview Coach</h1><p>Practice interviews anytime, get instant feedback, and improve your skills</p></div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/interview.png", width=80)
    st.markdown("### About")
    st.markdown("""
    **AI Interview Coach** helps you:
    - Practice role-specific interview questions
    - Get instant, personalized feedback
    - Learn from improved answers
    - Track your progress over time
    """)
    
    st.markdown("---")
    st.markdown("### How it works")
    st.markdown("""
    1. Select your target role
    2. Choose difficulty level
    3. Answer AI-generated questions
    4. Receive instant feedback and scores
    5. Get a comprehensive session summary
    """)
    
    st.markdown("---")
    st.markdown("### Supported Roles")
    st.markdown("""
    - 🐍 Python Developer
    - 📊 Data Scientist
    - 🌐 Web Developer
    - 🤖 ML Engineer
    - ☁️ DevOps Engineer
    - 🎨 UI/UX Designer
    """)

# Main content
if not st.session_state.session_started:
    # Setup screen
    st.markdown("## 🚀 Start Your Practice Session")
    st.markdown("Configure your interview practice session below:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        role = st.selectbox(
            "Select your target role",
            ["Python Developer", "Data Scientist", "Web Developer", 
             "ML Engineer", "DevOps Engineer", "UI/UX Designer"],
            help="Choose the role you're preparing for"
        )
    
    with col2:
        difficulty = st.select_slider(
            "Select difficulty level",
            options=["Beginner", "Intermediate", "Advanced"],
            value="Intermediate",
            help="Higher difficulty includes complex and system design questions"
        )
    
    num_questions = st.slider(
        "Number of questions",
        min_value=3,
        max_value=10,
        value=5,
        help="How many questions do you want to practice?"
    )
    
    st.markdown("---")
    
    if st.button("🎯 Start Interview Practice", type="primary", use_container_width=True):
        with st.spinner("Generating interview questions..."):
            questions = st.session_state.agent.generate_questions(
                role, difficulty, num_questions
            )
            if questions:
                st.session_state.questions = questions
                st.session_state.role = role
                st.session_state.difficulty = difficulty
                st.session_state.session_started = True
                st.session_state.current_q_index = 0
                st.session_state.answers = []
                st.rerun()
            else:
                st.error("Failed to generate questions. Please try again.")

elif not st.session_state.session_completed:
    # Interview in progress
    current_q = st.session_state.questions[st.session_state.current_q_index]
    
    # Progress bar
    progress = (st.session_state.current_q_index) / len(st.session_state.questions)
    st.progress(progress)
    st.markdown(f"**Question {st.session_state.current_q_index + 1} of {len(st.session_state.questions)}**")
    
    # Display question
    st.markdown(f"""
    <div class="score-card">
        <h3>📝 Question {st.session_state.current_q_index + 1}</h3>
        <p style="font-size: 1.2rem;">{current_q.get('question', '')}</p>
        <p><small>📚 Topics: {', '.join(current_q.get('topics', []))} | 🏷️ Type: {current_q.get('type', 'technical')}</small></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Answer input
    answer = st.text_area(
        "Your answer:",
        height=200,
        placeholder="Type your answer here... Be as detailed as possible. Use examples and structure your answer clearly.",
        key=f"answer_{st.session_state.current_q_index}"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("⏭️ Skip Question", use_container_width=True):
            st.session_state.answers.append({
                "question": current_q.get('question'),
                "answer": "",
                "score": 0,
                "feedback": "Skipped",
                "improved_answer": "Try to attempt the question next time."
            })
            st.session_state.current_q_index += 1
            if st.session_state.current_q_index >= len(st.session_state.questions):
                st.session_state.session_completed = True
            st.rerun()
    
    with col2:
        if st.button("✅ Submit Answer", type="primary", use_container_width=True):
            if not answer.strip():
                st.warning("Please write your answer before submitting.")
            else:
                with st.spinner("Evaluating your answer..."):
                    evaluation = st.session_state.agent.evaluate_answer(
                        current_q.get('question'),
                        answer,
                        st.session_state.role,
                        st.session_state.difficulty
                    )
                    
                    st.session_state.answers.append({
                        "question": current_q.get('question'),
                        "answer": answer,
                        "score": evaluation.get('score', 0),
                        "feedback": evaluation.get('feedback', ''),
                        "improved_answer": evaluation.get('improved_answer', ''),
                        "key_missing_points": evaluation.get('key_missing_points', [])
                    })
                    
                    st.session_state.current_q_index += 1
                    if st.session_state.current_q_index >= len(st.session_state.questions):
                        st.session_state.session_completed = True
                    st.rerun()
    
    # Show previous answer feedback if available
    if st.session_state.answers and len(st.session_state.answers) > 0:
        # Show the most recent answer feedback
        prev = st.session_state.answers[-1]
        if prev.get('score', 0) > 0:
            st.markdown("---")
            st.markdown("### 📊 Previous Question Feedback")
            
            score_col, feedback_col = st.columns([1, 2])
            with score_col:
                st.markdown(f"""
                <div class="score-card" style="text-align: center;">
                    <h2 style="margin:0;">{prev.get('score', 0)}/10</h2>
                    <p>Your Score</p>
                </div>
                """, unsafe_allow_html=True)
            
            with feedback_col:
                if prev.get('score', 0) >= 7:
                    st.markdown(f'<div class="feedback-good"><strong>✅ Feedback:</strong><br>{prev.get("feedback", "")}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="feedback-improve"><strong>📈 Improvement Suggestions:</strong><br>{prev.get("feedback", "")}</div>', unsafe_allow_html=True)
            
            with st.expander("🔍 View Improved Answer"):
                st.markdown(prev.get('improved_answer', 'No improved answer available.'))
                
                if prev.get('key_missing_points'):
                    st.markdown("**Key points you missed:**")
                    for point in prev.get('key_missing_points', []):
                        st.markdown(f"- {point}")

else:
    # Session completed - Show summary
    st.balloons()
    st.markdown("## 🎉 Session Completed!")
    st.markdown(f"**Role:** {st.session_state.role} | **Difficulty:** {st.session_state.difficulty}")
    
    # Generate summary
    with st.spinner("Generating your session summary..."):
        summary = st.session_state.agent.generate_session_summary(
            st.session_state.role,
            st.session_state.difficulty,
            st.session_state.answers
        )
    
    # Display final score
    final_score = summary.get('final_score', 0)
    score_color = "green" if final_score >= 7 else "orange" if final_score >= 5 else "red"
    st.markdown(f"""
    <div class="score-card" style="text-align: center;">
        <h1 style="color: {score_color}; margin:0;">{final_score}/10</h1>
        <p>Overall Session Score</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Strengths and Improvements
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### ✅ Strengths")
        for strength in summary.get('strengths', []):
            st.markdown(f"- {strength}")
    with col2:
        st.markdown("### 📈 Areas to Improve")
        for area in summary.get('areas_for_improvement', []):
            st.markdown(f"- {area}")
    
    # Recommended topics
    st.markdown("### 📚 Recommended Topics to Study")
    for topic in summary.get('recommended_topics', []):
        st.markdown(f"- {topic}")
    
    # Overall feedback
    st.markdown("### 💡 Overall Feedback")
    st.info(summary.get('overall_feedback', 'Keep practicing!'))
    
    st.markdown("### 🎯 Next Steps")
    st.success(summary.get('next_steps', 'Practice more questions to improve your skills.'))
    
    # Detailed question breakdown
    with st.expander("📋 View Detailed Question Breakdown"):
        for i, ans in enumerate(st.session_state.answers):
            st.markdown(f"**Q{i+1}:** {ans['question'][:100]}...")
            st.markdown(f"Score: **{ans.get('score', 0)}/10**")
            st.markdown(f"Feedback: {ans.get('feedback', '')}")
            st.markdown("---")
    
    # Restart button
    if st.button("🔄 Start New Session", type="primary", use_container_width=True):
        for key in ['session_started', 'session_completed', 'questions', 'answers', 
                    'current_q_index', 'role', 'difficulty']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>AI Interview Coach | Powered by Gemini AI</p>", unsafe_allow_html=True)