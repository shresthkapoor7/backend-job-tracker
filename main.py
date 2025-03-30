from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai

app = FastAPI()

# CORS setup (for frontend integration)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/parse-job")
def parse_job(url: str = Query(...), api_key: str = Query(...)):
    try:
        # Step 1: Scrape the webpage
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text(separator='\n', strip=True)

        # Step 2: Gemini API configuration
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-pro")

        # Step 3: Strict prompt for JSON response
        prompt = f"""
        You are a job description parser.

        Based on the text I give you, extract the following information strictly in JSON format with no explanation, markdown, or extra text.

        Expected format:
        {{
          "company": "Company Name",
          "skills": ["Skill 1", "Skill 2", "..."],
          "deadline": "Application Deadline or 'Not specified'"
        }}

        Do not wrap the result in code blocks.

        Here is the text:
        {text}
        """

        gemini_response = model.generate_content(prompt)
        return gemini_response.text.strip()

    except Exception as e:
        return {"error": str(e)}