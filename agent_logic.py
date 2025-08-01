import os
import getpass
import logging
from typing import TypedDict, Optional, Dict
from prompts import greet_prompt_template, resume_parser_prompt, tech_questions, Evaluator_prompt
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_community.document_loaders import PyMuPDFLoader
from langgraph.graph import StateGraph, END

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.FileHandler("hirebot.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logger.warning("dotenv package not found. Skipping .env file load.")


if "GROQ_API_KEY" not in os.environ or not os.getenv("GROQ_API_KEY"):
    os.environ["GROQ_API_KEY"] = getpass.getpass("Enter your Groq API key: ")


try:
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.2,
    )
    logger.info("LLM loaded successfully")
except Exception as e:
    logger.error(f"Failed to load LLM: {e}")
    raise

# --- State Definition ---
class Hirebot(TypedDict):
    """Defines the state for the graph."""
    user_name: Optional[str]
    resume_path: Optional[str]
    resume_parsed: Optional[str]
    tech_questions: Optional[Dict[str, str]]
    answers: Optional[Dict[str, str]]
    results: Optional[str]

# --- Node Functions ---
def get_name(state: Hirebot) -> dict:
    """Gets user's name from input and updates the state."""
    logger.info('Node: get_name execution started')
    user_name = ''
    while not user_name:
        user_name = input("Hi there! To get started, please enter your full name: ")
        if not user_name:
            print("Name cannot be empty. Please try again.")
    logger.info(f'Node: Name captured: {user_name}')
    return {"user_name": user_name}

def greet_user(state: Hirebot) -> dict:
    """Generates a greeting for the user and updates the state."""
    logger.info('Node: greet_user execution started')
    candidate_name = state["user_name"]
    
    prompt = PromptTemplate(
        template=greet_prompt_template,
        input_variables=["candidate_name", "agent_name", "hr_manager_name"],
    )
    
    greeting = prompt.format(candidate_name=candidate_name, agent_name="Janus", hr_manager_name="Radhika")
    print(greeting)
    
    while True:
        path = input("Enter the path of you resume (PDF file): ")
        if os.path.exists(path) and path.lower().endswith(".pdf"):
            logger.info(f" Resume path recieved and validated: {path}")
            return {"resume_path": path}
        else:
            print("Invalid Path or not a PDF file. Please check the file path and try again.")

def resume_loader(path_to_resume):
    """Helper function to load and extract text from a PDF resume."""
    loader = PyMuPDFLoader(path_to_resume)
    documents = loader.load()
    logger.info(f"Sucessfully loaded {path_to_resume}")
    return documents[0].page_content


def Parse_resume(state: Hirebot) -> dict:
    logger.info('Node: Make Question started')
    resume_path = state["resume_path"]
    data = resume_loader(resume_path)
    parser = JsonOutputParser()
    prompt = PromptTemplate(
        template=(resume_parser_prompt),
        input_variables=["RESUME"],
        partial_variables={"format_instructions": parser.get_format_instructions()},

    )

    chain = prompt | llm | parser
    logger.info("Invoking resume parsing chain...")
    parsed_resume = chain.invoke({"RESUME": data})
    logger.info("Resume parsed successfully.")
    print("\n✅ Thanks! I've reviewed your resume. Now for a few technical questions.")
    return {"resume_parsed": parsed_resume}

def Tech_question(state: Hirebot) -> dict:
    """Generates clarifying questions based on the initial query using an LLM."""
    # logger.info("Node: make_question execution started.")
    resume_data = state["resume_parsed"]
    questions = {}
    num = 3 # Number of questions to generate
    parser = JsonOutputParser()
    # Corrected Example Output to be valid JSON
    prompt = PromptTemplate(
        template=(tech_questions),
        input_variables=["num", "tech_stack"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    chain = prompt | llm | parser
    logger.info("Invoking tech question generation chain...")
    questions = chain.invoke({"num": num, "tech_stack": resume_data})
    return {"tech_questions": questions}

def answers(state: Hirebot) -> dict:

    questions = state["tech_questions"]
    if questions is not None:
        answers = {}
        for key, question_text in questions.items():
            answer = input(f"❓ {question_text}\n> ")
            answers[question_text] = answer
        print(answers)
        return {"answers": answers}
    else:
        return {"answers": None}

def Get_results(state: Hirebot) -> dict:
    """Generates clarifying questions based on the initial query using an LLM."""
    answers = state["answers"]
    prompt = PromptTemplate(
        template=(Evaluator_prompt),
        input_variables=["qa"],
    )

    chain = prompt | llm 

    results_message = chain.invoke({"qa": answers})
    return {"results": results_message.content}

def sendoff_node(state: Hirebot) -> None:
    candidate_name = state["user_name"]
    evaluation = state["results"]

    print("\n" + "="*50)
    print("Evaluation Complete")
    print("="*50)
    print(f"\nHere is a summary of your technical screening:\n")
    print(evaluation)
    
    message = f"""
    Thank you for completing the initial steps of the hiring process, {candidate_name}. 🙌
    Our team will carefully evaluate your responses and resume.
    You will be notified via email or message if you are selected for the next round.
    We appreciate your patience and interest in this opportunity!
    """

    print(message)

graph_builder = StateGraph(Hirebot)

# Add nodes
graph_builder.add_node("get_name", get_name)
graph_builder.add_node("greet", greet_user)
graph_builder.add_node("parse_resume", Parse_resume)
graph_builder.add_node("tech_questions", Tech_question)
graph_builder.add_node("answers", answers)
graph_builder.add_node("results", Get_results)
graph_builder.add_node("sendoff", sendoff_node)

# Set the entry point
graph_builder.set_entry_point("get_name")

# Add edges to define the flow
graph_builder.add_edge("get_name", "greet")
graph_builder.add_edge("greet", "parse_resume")
graph_builder.add_edge("parse_resume", "tech_questions")
graph_builder.add_edge("tech_questions", "answers")
graph_builder.add_edge("answers", "results")
graph_builder.add_edge("results", "sendoff")
graph_builder.add_edge("sendoff", END)

# Compile the graph
hirebot_graph = graph_builder.compile()
logger.info("Hirebot graph compiled successfully.")

# --- Graph Execution ---
if __name__ == "__main__":
    print("🚀 Starting Hirebot Agent...")
    initial_state = {}
    # Invoke the graph. The initial state is empty.
    hirebot_graph.invoke(initial_state)
    print("✅ Hirebot session finished.")