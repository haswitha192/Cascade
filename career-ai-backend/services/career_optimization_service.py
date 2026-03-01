from services.resume_skill_service import fetch_resume_skills
from services.job_service import fetch_all_jobs
from services.recommendation_service import calculate_similarity
from services.grok_service import generate_learning_roadmap


def generate_recommendations(resume_id):

    resume_skills = fetch_resume_skills(resume_id)
    jobs = fetch_all_jobs()

    recommendations = []

    for job in jobs:
        job_id = job[0]
        job_skills = job[1]

        similarity = calculate_similarity(resume_skills, job_skills)

        job_skill_list = [s.strip() for s in job_skills.split(",")]
        missing_skills = list(
            set(job_skill_list) - set(resume_skills)
        )

        roadmap = None
        if not missing_skills:
            roadmap = "You already meet all required skills for this role."
        else:
            roadmap = generate_learning_roadmap(job_id, missing_skills)

        recommendations.append({
            "job_id": job_id,
            "similarity_score": similarity,
            "missing_skills": missing_skills,
            "roadmap": roadmap
        })

    recommendations = sorted(
        recommendations,
        key=lambda x: x["similarity_score"],
        reverse=True
    )

    return recommendations