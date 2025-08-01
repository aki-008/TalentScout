import os
import uuid
import asyncio
from datetime import datetime
from typing import TypedDict, Optional, Dict, List
from pathlib import Path
import logging

from fastapi import FastAPI, HTTPException, UploadFile, File, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from prompts import greet_prompt_template, resume_parser_prompt, tech_questions, Evaluator_prompt
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_community.document_loaders import PyMuPDFLoader
from langgraph.graph import StateGraph, END

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.FileHandler("hirebot_api.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logger.warning("dotenv package not found. Skipping .env file load.")

# Initialize FastAPI app
app = FastAPI(
    title="Hirebot API",
    description="AI-powered hiring assistant API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize LLM
try:
    if not os.getenv("GROQ_API_KEY"):
        raise ValueError("GROQ_API_KEY environment variable is required")
    
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.2,
    )
    logger.info("LLM loaded successfully")
except Exception as e:
    logger.error(f"Failed to load LLM: {e}")
    raise

# --- Pydantic Models ---
class SessionStartRequest(BaseModel):
    user_name: str

class SessionStartResponse(BaseModel):
    session_id: str
    greeting: str
    message: str

class ResumeUploadResponse(BaseModel):
    session_id: str
    message: str
    parsed_resume: Dict

class TechQuestionsResponse(BaseModel):
    session_id: str
    questions: Dict[str, str]

class AnswerSubmissionRequest(BaseModel):
    session_id: str
    answers: Dict[str, str]

class EvaluationResponse(BaseModel):
    session_id: str
    evaluation: str
    completion_message: str

class SessionStatus(BaseModel):
    session_id: str
    status: str
    current_step: str
    user_name: Optional[str] = None

# --- State Definition ---
class Hirebot(TypedDict):
    """Defines the state for the graph."""
    session_id: str
    user_name: Optional[str]
    resume_path: Optional[str]
    resume_parsed: Optional[Dict]
    tech_questions: Optional[Dict[str, str]]
    answers: Optional[Dict[str, str]]
    results: Optional[str]
    current_step: str
    created_at: str

# In-memory session storage (use Redis/database in production)
sessions: Dict[str, Hirebot] = {}

# Directory for uploaded files
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# --- Helper Functions ---
def resume_loader(path_to_resume: str) -> str:
    """Helper function to load and extract text from a PDF resume."""
    loader = PyMuPDFLoader(path_to_resume)
    documents = loader.load()
    logger.info(f"Successfully loaded {path_to_resume}")
    return documents[0].page_content

def generate_greeting(candidate_name: str) -> str:
    """Generate greeting for the user."""
    prompt = PromptTemplate(
        template=greet_prompt_template,
        input_variables=["candidate_name", "agent_name", "hr_manager_name"],
    )
    return prompt.format(
        candidate_name=candidate_name, 
        agent_name="Janus", 
        hr_manager_name="Radhika"
    )

async def parse_resume_async(resume_path: str) -> Dict:
    """Parse resume asynchronously."""
    try:
        data = resume_loader(resume_path)
        parser = JsonOutputParser()
        prompt = PromptTemplate(
            template=resume_parser_prompt,
            input_variables=["RESUME"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )
        
        chain = prompt | llm | parser
        parsed_resume = await asyncio.to_thread(chain.invoke, {"RESUME": data})
        logger.info("Resume parsed successfully.")
        return parsed_resume
    except Exception as e:
        logger.error(f"Error parsing resume: {e}")
        raise HTTPException(status_code=500, detail=f"Error parsing resume: {str(e)}")

async def generate_tech_questions_async(resume_data: Dict) -> Dict[str, str]:
    """Generate technical questions asynchronously."""
    try:
        num = 3
        parser = JsonOutputParser()
        prompt = PromptTemplate(
            template=tech_questions,
            input_variables=["num", "tech_stack"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )
        
        chain = prompt | llm | parser
        questions = await asyncio.to_thread(chain.invoke, {"num": num, "tech_stack": resume_data})
        logger.info("Tech questions generated successfully.")
        return questions
    except Exception as e:
        logger.error(f"Error generating tech questions: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating questions: {str(e)}")

async def evaluate_answers_async(answers: Dict[str, str]) -> str:
    """Evaluate answers asynchronously."""
    try:
        prompt = PromptTemplate(
            template=Evaluator_prompt,
            input_variables=["qa"],
        )
        
        chain = prompt | llm
        results_message = await asyncio.to_thread(chain.invoke, {"qa": answers})
        logger.info("Answers evaluated successfully.")
        return results_message.content
    except Exception as e:
        logger.error(f"Error evaluating answers: {e}")
        raise HTTPException(status_code=500, detail=f"Error evaluating answers: {str(e)}")

# --- API Endpoints ---

@app.get("/")
async def root():
    return {"message": "Welcome to Hirebot API", "status": "active"}

@app.post("/sessions/start", response_model=SessionStartResponse)
async def start_session(request: SessionStartRequest):
    """Start a new hiring session."""
    try:
        session_id = str(uuid.uuid4())
        greeting = generate_greeting(request.user_name)
        
        sessions[session_id] = {
            "session_id": session_id,
            "user_name": request.user_name,
            "resume_path": None,
            "resume_parsed": None,
            "tech_questions": None,
            "answers": None,
            "results": None,
            "current_step": "resume_upload",
            "created_at": datetime.now().isoformat()
        }
        
        logger.info(f"Session started for user: {request.user_name}, session_id: {session_id}")
        
        return SessionStartResponse(
            session_id=session_id,
            greeting=greeting,
            message="Session started successfully. Please upload your resume next."
        )
    except Exception as e:
        logger.error(f"Error starting session: {e}")
        raise HTTPException(status_code=500, detail=f"Error starting session: {str(e)}")

@app.post("/sessions/{session_id}/upload-resume", response_model=ResumeUploadResponse)
async def upload_resume(session_id: str, file: UploadFile = File(...)):
    """Upload and parse resume for a session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    try:
        # Save uploaded file
        file_path = UPLOAD_DIR / f"{session_id}_{file.filename}"
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Parse resume
        parsed_resume = await parse_resume_async(str(file_path))
        
        # Update session
        sessions[session_id]["resume_path"] = str(file_path)
        sessions[session_id]["resume_parsed"] = parsed_resume
        sessions[session_id]["current_step"] = "tech_questions"
        
        logger.info(f"Resume uploaded and parsed for session: {session_id}")
        
        return ResumeUploadResponse(
            session_id=session_id,
            message="Resume uploaded and parsed successfully. Ready for technical questions.",
            parsed_resume=parsed_resume
        )
    except Exception as e:
        logger.error(f"Error uploading resume: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")

@app.get("/sessions/{session_id}/tech-questions", response_model=TechQuestionsResponse)
async def get_tech_questions(session_id: str):
    """Generate and return technical questions for a session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    if not session["resume_parsed"]:
        raise HTTPException(status_code=400, detail="Resume must be uploaded first")
    
    try:
        # Generate questions if not already generated
        if not session["tech_questions"]:
            questions = await generate_tech_questions_async(session["resume_parsed"])
            sessions[session_id]["tech_questions"] = questions
            sessions[session_id]["current_step"] = "answering_questions"
        
        return TechQuestionsResponse(
            session_id=session_id,
            questions=sessions[session_id]["tech_questions"]
        )
    except Exception as e:
        logger.error(f"Error generating tech questions: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating questions: {str(e)}")

@app.post("/sessions/{session_id}/submit-answers", response_model=EvaluationResponse)
async def submit_answers(session_id: str, request: AnswerSubmissionRequest):
    """Submit answers and get evaluation."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    if not session["tech_questions"]:
        raise HTTPException(status_code=400, detail="Technical questions not generated yet")
    
    try:
        # source_dict = {'a': 'value1', 'b': 'value2', 'c': 'value3'}
        request.answers = {value: None for value in session['tech_questions'].values()} # Assign None or any desired default value

        sessions[session_id]["answers"] = request.answers
        sessions[session_id]["current_step"] = "evaluation"
        
        # Evaluate answers
        evaluation = await evaluate_answers_async(request.answers)
        sessions[session_id]["results"] = evaluation
        sessions[session_id]["current_step"] = "completed"
        
        user_name = session["user_name"]
        completion_message = f"""
Thank you for completing the initial steps of the hiring process, {user_name}. 🙌
Our team will carefully evaluate your responses and resume.
You will be notified via email or message if you are selected for the next round.
We appreciate your patience and interest in this opportunity!
        """
        
        logger.info(f"Session completed for: {session_id}")
        
        return EvaluationResponse(
            session_id=session_id,
            evaluation=evaluation,
            completion_message=completion_message.strip()
        )
    except Exception as e:
        logger.error(f"Error evaluating answers: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing answers: {str(e)}")

@app.get("/sessions/{session_id}/status", response_model=SessionStatus)
async def get_session_status(session_id: str):
    """Get the current status of a session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    return SessionStatus(
        session_id=session_id,
        status="active" if session["current_step"] != "completed" else "completed",
        current_step=session["current_step"],
        user_name=session["user_name"]
    )

@app.get("/sessions", response_model=List[SessionStatus])
async def list_sessions():
    """List all sessions (for admin purposes)."""
    return [
        SessionStatus(
            session_id=session_id,
            status="active" if session["current_step"] != "completed" else "completed",
            current_step=session["current_step"],
            user_name=session["user_name"]
        )
        for session_id, session in sessions.items()
    ]

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and its associated files."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        session = sessions[session_id]
        
        # Delete uploaded file if exists
        if session["resume_path"] and os.path.exists(session["resume_path"]):
            os.remove(session["resume_path"])
        
        # Remove session from memory
        del sessions[session_id]
        
        logger.info(f"Session deleted: {session_id}")
        return {"message": "Session deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting session: {str(e)}")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_sessions": len(sessions)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
