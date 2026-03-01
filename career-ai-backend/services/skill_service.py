COMMON_SKILLS = [
    "Python", "Java", "C++", "SQL",
    "Machine Learning", "HTML", "CSS",
    "JavaScript", "MongoDB", "Azure"
]

def extract_skills(text: str):
    found_skills = []

    for skill in COMMON_SKILLS:
        if skill.lower() in text.lower():
            found_skills.append(skill)

    return found_skills