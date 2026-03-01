def calculate_similarity(resume_skills, job_skills):
    resume_set = set(skill.lower() for skill in resume_skills)
    job_set = set(skill.strip().lower() for skill in job_skills.split(","))

    if not resume_set or not job_set:
        return 0.0

    intersection = resume_set.intersection(job_set)
    union = resume_set.union(job_set)

    return round(len(intersection) / len(union), 2)


