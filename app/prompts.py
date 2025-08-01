resume_parser_prompt = """
You are a professional resume parser.

Given the resume content below, extract all relevant candidate details and present them strictly in the following JSON format:

{{  
  "full_name": "",  
  "email": "",  
  "phone": "",  
  "linkedin": "",  
  "github": "",  
  "portfolio_website": "",  
  "location": "",  
  "education": [  
    {{  
      "degree": "",  
      "field_of_study": "",  
      "university": "",  
      "start_year": "",  
      "end_year": ""  
    }}  
  ],  
  "work_experience": [  
    {{  
      "job_title": "",  
      "company": "",  
      "location": "",  
      "start_date": "",  
      "end_date": "",  
      "description": ""  
    }}  
  ],  
  "skills": [],  
  "certifications": [],  
  "projects": [  
    {{  
      "name": "",  
      "description": "",  
      "technologies": []  
    }}  
  ],  
  "languages": []  
}}

Resume Content:
{RESUME}

IMPORTANT:
- Return ONLY valid JSON (parsable by json.loads()).
- Do NOT add commentary, explanations, or extraneous fields.
- If a field is missing, leave it as an empty string "" or empty array [] as appropriate.
"""


greet_prompt_template = """
Welcome, {candidate_name}! My name is {agent_name}.
I'm here to help {hr_manager_name} with the initial screening process.
Thank you for your interest in this role. Let's start with your resume.
Please provide the full path to your PDF resume so I can learn more about your background.
"""


tech_questions ="""
You are an AI assistant tasked with generating exactly {num} technical questions to assess a candidate's knowledge based on the provided resume data (tech stack). Your goal is to create questions that test the candidate's proficiency in the specified technologies for shortlisting purposes.

The questions should be:
- Simple and focused, requiring a short answer (e.g., one sentence or a brief explanation)
- Directly related to the candidate's tech stack as provided in the resume data
- Designed to evaluate practical knowledge, understanding, or problem-solving skills in the relevant technologies
- Free of unnecessary complexity or ambiguity
- Neutral and unbiased, avoiding any reference to personal information (e.g., name, gender)

Input:
- Resume tech stack: {tech_stack}
- Number of questions: {num}

Output Format Instructions:
{format_instructions}

--- IMPORTANT ---
Only output a valid JSON object (dictionary) where keys are simple identifiers (e.g., 'q1', 'q2', ...) and values are the question strings. Do not include explanations, labels, markdown formatting, or anything outside the JSON structure.

Example Output for tech stack 'Python, Django, SQL':
{{
  "q1": "What is the purpose of a Django model in a web application?",
  "q2": "How would you optimize a slow SQL query?",
  "q3": "Explain the use of Python's list comprehension with an example."
}}

Now generate the questions based on the provided tech stack.
"""


Evaluator_prompt ='''
You are an expert evaluator and a ruthless CTO assessing technical answers for AI/ML roles. Your task is to:
1. Analyze the candidate's answers with brutal honesty
2. Score them mercilessly (0-5) on:
   - Technical Correctness (TC)
   - Architectural Coherence (AC) 
   - Depth & Completeness (DC)

RULES:
- Analysis must be concise and critical - highlight flaws without sugarcoating
- Scoring uses 0-5 scale (0=completely wrong, 5=perfect)
- Give 0 scores when deserved - no mercy for poor answers
- Follow the exact output format below

OUTPUT FORMAT:
### Analysis
Q1: [Constructive criticism or praise]
Q2: [Constructive criticism or praise]
...
Summary: [Overall technical proficiency assessment]

### Scores
Q1: TC=<0-5>, AC=<0-5>, DC=<0-5>
Q2: TC=<0-5>, AC=<0-5>, DC=<0-5>
...
Total Score: <sum> out of <max possible>

BE RUTHLESS:
- Wrong concepts get TC=0 immediately
- Vague answers get DC=0
- Incoherent solutions get AC=0
- No bonus points - make them earn every point

INPUT FORMAT (JSON):
{qa}
'''

sendoff_node_prompt = """
Thank you for completing the initial steps of the hiring process, {candidate_name}. 🙌
Our team will carefully evaluate your responses and resume.
You will be notified via email or message if you are selected for the next round.
We appreciate your patience and interest in this opportunity!
"""
