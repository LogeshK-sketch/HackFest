"""Resume text analysis and scoring module."""
import json, re
from PyPDF2 import PdfReader

SKILLS_LIST = [
    "Python", "Java", "C++", "C", "DSA", "SQL", "DBMS", "OS",
    "Computer Networks", "CN", "Machine Learning", "ML",
    "HTML", "CSS", "JavaScript", "React", "Flask", "Django",
    "Git", "Linux", "REST API", "OOP", "System Design",
    "Data Structures", "Algorithms", "Pandas", "NumPy"
]

PLACEMENT_CRITICAL = [
    "DSA", "SQL", "Python", "OOP", "OS", "DBMS",
    "Computer Networks", "System Design", "Git", "Data Structures"
]

SECTION_KEYWORDS = {
    "experience": ["experience", "internship", "worked", "employed", "work history"],
    "projects":   ["project", "built", "developed", "implemented", "created"],
    "education":  ["education", "university", "college", "degree", "b.tech", "b.e", "bachelor"],
    "contact":    ["email", "phone", "linkedin", "github", "@"]
}

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
        print(f"Error extracting text from PDF: {e}")
    return text

def detect_skills(text: str) -> tuple:
    """For each skill in SKILLS_LIST, use:
      re.search(r'\b' + re.escape(skill) + r'\b', text, re.IGNORECASE)
    Return (matched_skills_list, missing_skills_list)."""
    matched_skills = []
    missing_skills = []
    for skill in SKILLS_LIST:
        if re.search(r'\b' + re.escape(skill) + r'\b', text, re.IGNORECASE):
            matched_skills.append(skill)
        else:
            missing_skills.append(skill)
    return matched_skills, missing_skills

def detect_sections(text: str) -> dict:
    """For each section in SECTION_KEYWORDS, check if any
    keyword appears in text.lower(). Return dict of bool values."""
    sections = {}
    text_lower = text.lower()
    for section, keywords in SECTION_KEYWORDS.items():
        sections[section] = any(kw in text_lower for kw in keywords)
    return sections

def generate_suggestions(missing_skills: list, sections: dict, text: str) -> list:
    """Return up to 6 suggestions."""
    suggestions = []
    
    critical_missing = [s for s in PLACEMENT_CRITICAL if s in missing_skills]
    for skill in critical_missing[:3]:
        suggestions.append(f"Add {skill} projects or coursework to strengthen your profile.")
        if len(suggestions) >= 6: return suggestions
        
    if not sections.get('experience'):
        suggestions.append("Include an Experience or Internship section.")
        if len(suggestions) >= 6: return suggestions
        
    if not sections.get('projects'):
        suggestions.append("Add a Projects section with 2-3 technical projects.")
        if len(suggestions) >= 6: return suggestions
        
    text_lower = text.lower()
    if 'github' not in text_lower:
        suggestions.append("Add your GitHub profile URL (github.com/yourusername).")
        if len(suggestions) >= 6: return suggestions
        
    if 'linkedin' not in text_lower:
        suggestions.append("Include your LinkedIn profile link.")
        
    return suggestions[:6]

def analyze_resume(text: str) -> dict:
    """Calls detect_skills, detect_sections, generate_suggestions."""
    matched_skills, missing_skills = detect_skills(text)
    sections = detect_sections(text)
    suggestions = generate_suggestions(missing_skills, sections, text)
    
    base = round((len(matched_skills) / len(SKILLS_LIST)) * 60)
    bonus = 10 * sum(1 for v in sections.values() if v)
    score = min(base + bonus, 100)
    
    return {
      'matched_skills': matched_skills,
      'missing_skills': missing_skills,
      'score': int(score),
      'suggestions': suggestions,
      'sections': sections
    }
