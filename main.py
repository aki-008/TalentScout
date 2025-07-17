from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import Literal, TypedDict, List, Optional, Dict
from typing_extensions import Annotated
from langgraph.graph import START, StateGraph
from langchain_core.vectorstores import InMemoryVectorStore
import json
import time
from dotenv import load_dotenv
import getpass
import os
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_tavily import TavilySearch
from langchain_core.output_parsers import JsonOutputParser
import logging
from langchain_groq import ChatGroq
from prompts import greet_prompt_template, resume_parser_prompt, tech_questions, Evaluator_prompt
from langchain_core.prompts import PromptTemplate
import bs4
from langchain import hub
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.documents import Document
from langchain.document_loaders import DirectoryLoader, TextLoader
from langchain_community.document_loaders import PyPDFLoader, PyMuPDFLoader


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.FileHandler("TS.log"), logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

load_dotenv()


if "GROQ_API_KEY" not in os.environ or not os.getenv("GROQ_API_KEY"):
    os.environ["GROQ_API_KEY"] = getpass.getpass("Enter your Groq API key: ")

# --- LLM Initialization ---
try:
    llm = ChatGroq(
        model="llama3-8b-8192",
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
    greet_user: Optional[str]
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
        user_name = input("Please enter your name: ")
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
        input_variables=["input","candidate_name", "agent_name", "hr_manager_name"],
    )
    
    chain = prompt | llm

    greet = chain.invoke({"input":"START","candidate_name": "John Doe", "agent_name":"janus", "hr_manager_name": "radhika"})
    print(greet.content)
    logger.info("Greeting generated.")
    

    return {"greet_user": greet.content}

def resume_loader(path_to_resume):

    loader = DirectoryLoader(
                path_to_resume,
                glob="**/*.pdf",
                loader_cls=PyMuPDFLoader,
                show_progress=True,  # Optional: Displays a progress bar
                use_multithreading=True  # Optional: Enables multithreading for faster loading
            )

    langchian_loader = loader.load() 
    resume_data =langchian_loader[0].page_content
    return resume_data

def Parse_resume(state: Hirebot) -> dict:
    logger.info('Node: Make Question started')

    data = resume_loader(resume_path)
    parser = JsonOutputParser()
    parser.get_format_instructions()
    prompt = PromptTemplate(
        template=(resume_parser_prompt),
        input_variables=["RESUME"],
        partial_variables={"format_instructions": parser.get_format_instructions()},

    )

    chain = prompt | llm |parser
    parsed_resume = chain.invoke({"RESUME": data})
    return {"resume_parsed": parsed_resume}

def Tech_question(state: Hirebot) -> dict:
    """Generates clarifying questions based on the initial query using an LLM."""
    # logger.info("Node: make_question execution started.")
    questions = {}
    num = 3 # Number of questions to generate
    parser = JsonOutputParser()
    # Corrected Example Output to be valid JSON
    prompt = PromptTemplate(
        template=(tech_questions),
        input_variables=["num", "resume_data"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    chain = prompt | llm | parser

    questions = chain.invoke({"num": num, "tech_stack": resume_data})
    return {"tech_questions": questions}

def answers(state: Hirebot) -> dict:
    answers = {}
    for i in questions:
        answers[questions[i]] = input(f"Question {i}: {questions[i]}")
    print(answers)
    print(type(answers))
    return {"answers": answers}

def Get_reults(state: Hirebot) -> dict:
    """Generates clarifying questions based on the initial query using an LLM."""

    prompt = PromptTemplate(
        template=(Evaluator_prompt),
        input_variables=["qa"],
    )

    chain = prompt | llm 

    results = chain.invoke({"qa": answers})
    return {"results": results}

def print_final_state(state: Hirebot) -> None:
    """Prints the final state of the graph."""
    logger.info("Node: print_final_state execution started.")
    print("\n--- Final State ---")
    # Print the actual greeting message received from the user
    if state.get("greet_user"):
        print(state["greet_user"])
    # Pretty print the full dictionary state for debugging
    print("\n--- Full State Object ---")
    print(json.dumps(state, indent=2))
    print("--- End of State ---")
    logger.info("Final state printed.")
    return None

# --- Graph Definition ---
graph_builder = StateGraph(Hirebot)

# Add nodes
graph_builder.add_node("get_name", get_name)
graph_builder.add_node("greet", greet_user)
graph_builder.add_node("parse_resume", Parse_resume)
graph_builder.add_node("tech_questions", Tech_question)
graph_builder.add_node("answers", answers)
graph_builder.add_node("results", Get_reults)
graph_builder.add_node("print_state", print_final_state)

# Set the entry point
graph_builder.set_entry_point("get_name")

# Add edges to define the flow
graph_builder.add_edge("get_name", "greet")
graph_builder.add_edge("greet", "print_state")

# Set the finish point
graph_builder.set_finish_point("print_state")

# Compile the graph
hirebot_graph = graph_builder.compile()
logger.info("Hirebot graph compiled successfully.")

# --- Graph Execution ---
if __name__ == "__main__":
    print("🚀 Starting Hirebot Agent...")
    initial_state: Hirebot = {
        "user_name": None,
        "greet_user": None,
        "resume_parsed": None,
    }
    # Invoke the graph. The initial state is empty.
    hirebot_graph.invoke(initial_state)
    print("✅ Hirebot session finished.")