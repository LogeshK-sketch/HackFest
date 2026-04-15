# pip install: google-genai tenacity
# Required imports:
import os
import json
import logging
from PyPDF2 import PdfReader
from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from google.genai.errors import APIError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_text_from_pdf(filepath: str) -> str:
    """Open PDF with PdfReader, iterate all pages,
    concatenate page.extract_text(), return full string."""
    text = ""
    try:
        reader = PdfReader(filepath)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
    return text

# The tenacity decorator retries up to 3 times, with exponential backoff (e.g. 2s, 4s, 8s)
# if we hit a 429 quota exception specifically.
@retry(
    stop=stop_after_attempt(3), 
    wait=wait_exponential(multiplier=2, min=2, max=15),
    retry=retry_if_exception_type(APIError),
    reraise=True
)
def extract_gemini_json_with_retry(client, text):
    """Makes the API call using the new SDK."""
    prompt = f"""
    You are an expert ATS (Applicant Tracking System) and resume evaluator.
    Analyze the resume text below and return ONLY a valid JSON object —
    no markdown, no explanation, no extra text.

    Evaluate the resume against modern industry standards and return:
    - skills_found: technical and soft skills explicitly mentioned
    - skills_missing: relevant industry skills absent from the resume
      (infer from the role level and domain detected)
    - projects_detected: any projects, case studies, or portfolio items
    - experience_level: classify as "Junior", "Mid", or "Senior"
    - suggestions: 3–5 specific, actionable improvements to boost ATS ranking
    - score: integer ATS compatibility score from 0 to 100

    Resume Text:
    {text}
    """
    
    # Send the request with application/json mapping
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2
        )
    )
    return response.text

def analyze_resume_with_gemini(text: str) -> dict:
    """
    Analyzes resume text using the Gemini API to extract ATS-optimized
    insights, skills, and overall compatibility scores based on industry standards.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Missing GEMINI_API_KEY environment variable")
        
    client = genai.Client(api_key=api_key)
    
    fallback_response = {
        "skills_found": [],
        "skills_missing": [],
        "projects_detected": [],
        "experience_level": "",
        "suggestions": [],
        "score": 0
    }

    try:
        response_text = extract_gemini_json_with_retry(client, text)
        
        # Parse output safely
        parsed_json = json.loads(response_text.strip())
        
        for k, v in fallback_response.items():
            if k not in parsed_json:
                parsed_json[k] = v
                
        return parsed_json
        
    except Exception as e:
        logger.error(f"Gemini API extraction failed: {e}")
        return fallback_response

# Example Flask route integration:
#
# @app.route('/analyze', methods=['POST'])
# def analyze():
#     file = request.files['resume']
#     text = extract_text_from_pdf(file)          # existing function
#     result = analyze_resume_with_gemini(text)   # new Gemini function
#     return jsonify(result)
