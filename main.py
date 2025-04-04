from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import json
import re

app = FastAPI()

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/parse-job")
def parse_job(url: str = Query(...), api_key: str = Query(...)):
    try:
        # Step 1: Scrape the page
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text(separator='\n', strip=True)

        # Step 2: Gemini config
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-pro-exp-03-25")

        # Step 3: Prompt
        prompt = f"""
        You are a job description parser.

        Based on the text I give you, extract the following information strictly in JSON format with no explanation, markdown, or extra text.

        Expected format:
        {{
          "company": "Company Name",
          "role": "Job Title",
          "skills": ["Skill 1", "Skill 2", "..."],
          "deadline": "Application Deadline or 'Not specified'"
        }}

        Do not wrap the result in code blocks.

        Here is the text:
        {text}
        """

        gemini_response = model.generate_content(prompt)
        raw_text = gemini_response.text.strip()

        # Step 4: Clean code block wrapping
        if raw_text.startswith("```json"):
            cleaned_text = re.sub(r"^```json\s*|\s*```$", "", raw_text, flags=re.DOTALL).strip()
        elif raw_text.startswith("```"):
            cleaned_text = re.sub(r"^```\s*|\s*```$", "", raw_text, flags=re.DOTALL).strip()
        else:
            cleaned_text = raw_text

        # Step 5: Try parsing into JSON
        try:
            parsed = json.loads(cleaned_text)
            return parsed
        except json.JSONDecodeError:
            return {
                "raw": cleaned_text,
                "note": "Could not parse JSON cleanly. Here's the raw response."
            }

    except Exception as e:
        return {"error": str(e)}