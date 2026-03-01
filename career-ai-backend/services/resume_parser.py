def parse_resume(text: str) -> dict:
    skills_keywords = ["python", "java", "sql", "azure"]
    found = []

    text_lower = text.lower()

    for skill in skills_keywords:
        if skill in text_lower:
            found.append(skill)

    return {
        "name": text.split("\n")[0],
        "skills": found,
        "raw_text": text
    }