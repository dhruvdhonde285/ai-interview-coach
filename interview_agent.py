# interview_agent.py - Core AI agent logic

import google.generativeai as genai
import json
import re
from prompts import (
    QUESTION_GENERATION_PROMPT,
    ANSWER_EVALUATION_PROMPT,
    SESSION_SUMMARY_PROMPT
)

class InterviewAgent:
    def __init__(self, api_key):
        """Initialize the Interview Agent with Gemini API"""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.conversation_history = []
        
    def generate_questions(self, role, difficulty, count=1):
        """Generate interview questions based on role and difficulty"""
        prompt = QUESTION_GENERATION_PROMPT.format(
            role=role,
            difficulty=difficulty,
            count=count
        )
        
        try:
            response = self.model.generate_content(prompt)
            # Extract JSON from response
            json_text = self._extract_json(response.text)
            questions = json.loads(json_text)
            return questions
        except Exception as e:
            # Fallback questions if API fails
            return self._get_fallback_questions(role, difficulty, count)
    
    def evaluate_answer(self, question, answer, role, difficulty):
        """Evaluate candidate's answer and provide feedback"""
        prompt = ANSWER_EVALUATION_PROMPT.format(
            question=question,
            answer=answer,
            role=role,
            difficulty=difficulty
        )
        
        try:
            response = self.model.generate_content(prompt)
            json_text = self._extract_json(response.text)
            evaluation = json.loads(json_text)
            
            # Store in history
            self.conversation_history.append({
                "question": question,
                "answer": answer,
                "score": evaluation.get("score", 0),
                "feedback": evaluation.get("feedback", "")
            })
            
            return evaluation
        except Exception as e:
            # Fallback evaluation
            return self._get_fallback_evaluation(answer)
    
    def generate_session_summary(self, role, difficulty, questions_data):
        """Generate final session summary"""
        # Calculate averages
        attempted = len(questions_data)
        total_scores = [q.get("score", 0) for q in questions_data]
        avg_score = sum(total_scores) / len(total_scores) if total_scores else 0
        
        # Format question scores for prompt
        q_scores = "\n".join([
            f"Q{i+1}: {q['question'][:50]}... - Score: {q.get('score', 0)}/10"
            for i, q in enumerate(questions_data)
        ])
        
        prompt = SESSION_SUMMARY_PROMPT.format(
            role=role,
            difficulty=difficulty,
            attempted=attempted,
            total=len(questions_data),
            avg_score=round(avg_score, 1),
            question_scores=q_scores
        )
        
        try:
            response = self.model.generate_content(prompt)
            json_text = self._extract_json(response.text)
            summary = json.loads(json_text)
            return summary
        except:
            return self._get_fallback_summary(avg_score)
    
    def _extract_json(self, text):
        """Extract JSON from LLM response"""
        # Try to find JSON in markdown code blocks
        json_match = re.search(r'```json\n(.*?)\n```', text, re.DOTALL)
        if json_match:
            return json_match.group(1)
        
        # Try to find JSON array/object directly
        json_match = re.search(r'(\[.*\]|\{.*\})', text, re.DOTALL)
        if json_match:
            return json_match.group(1)
        
        return text
    
    def _get_fallback_questions(self, role, difficulty, count):
        """Fallback questions if API fails"""
        fallback_questions = {
            "Data Scientist": [
                {"question": "Explain the difference between supervised and unsupervised learning.", "type": "technical", "topics": ["Machine Learning"]},
                {"question": "What is the bias-variance tradeoff?", "type": "technical", "topics": ["Model Evaluation"]},
                {"question": "Explain how you would handle missing data in a dataset.", "type": "technical", "topics": ["Data Preprocessing"]}
            ],
            "Web Developer": [
                {"question": "Explain the difference between let, const, and var in JavaScript.", "type": "technical", "topics": ["JavaScript"]},
                {"question": "What is the DOM and how do you manipulate it?", "type": "technical", "topics": ["DOM"]},
                {"question": "Explain REST API and its principles.", "type": "technical", "topics": ["APIs"]}
            ],
            "Python Developer": [
                {"question": "What are decorators in Python and when would you use them?", "type": "technical", "topics": ["Python"]},
                {"question": "Explain the difference between deep and shallow copy.", "type": "technical", "topics": ["Python"]},
                {"question": "What is the Global Interpreter Lock (GIL)?", "type": "technical", "topics": ["Python"]}
            ]
        }
        
        default = fallback_questions.get(role, fallback_questions["Python Developer"])
        return default[:count]
    
    def _get_fallback_evaluation(self, answer):
        """Fallback evaluation if API fails"""
        answer_length = len(answer.split())
        if answer_length > 50:
            score = 7
            feedback = "Good attempt! Your answer shows understanding. Try to add more specific examples."
            improved = "Consider adding concrete examples and structuring your answer with clear points."
        elif answer_length > 20:
            score = 5
            feedback = "You're on the right track, but your answer could be more detailed."
            improved = "Expand your explanation with examples and structure your answer."
        else:
            score = 3
            feedback = "Your answer is too brief. Try to elaborate more on the concept."
            improved = "Start with a definition, then explain with examples, and conclude."
        
        return {
            "score": score,
            "correctness": score,
            "clarity": score,
            "completeness": score,
            "feedback": feedback,
            "improved_answer": improved,
            "key_missing_points": ["More details", "Examples", "Structure"]
        }
    
    def _get_fallback_summary(self, avg_score):
        """Fallback session summary"""
        if avg_score >= 7:
            feedback = "Great job! You're well-prepared. Keep practicing to maintain this level."
            next_steps = "Try advanced questions in your domain"
        elif avg_score >= 5:
            feedback = "Good effort! You have the basics, but need to dive deeper into concepts."
            next_steps = "Focus on understanding core concepts and practice with examples"
        else:
            feedback = "Keep practicing! Start with fundamentals and gradually build up."
            next_steps = "Review basic concepts and practice regularly"
        
        return {
            "final_score": avg_score,
            "strengths": ["Basic understanding", "Willingness to learn"],
            "areas_for_improvement": ["Depth of answers", "Technical vocabulary"],
            "recommended_topics": ["Core concepts", "Practice problems"],
            "overall_feedback": feedback,
            "next_steps": next_steps
        }