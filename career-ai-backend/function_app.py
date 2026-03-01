import azure.functions as func
from services.document_service import analyze_resume
from services.blob_service import upload_resume
from services.sql_service import insert_resume, insert_resume_skills
from services.skill_service import extract_skills
from services.career_optimization_service import generate_recommendations
import json
import logging

app = func.FunctionApp()

MAX_FILE_SIZE_MB = 5


# -------------------------
# PROCESS RESUME
# -------------------------
@app.function_name(name="processResume")
@app.route(route="processResume", methods=["POST"])
def process_resume(req: func.HttpRequest) -> func.HttpResponse:

    logging.info("Resume upload request received.")

    try:
        file_bytes = req.get_body()

        result = analyze_resume(file_bytes)

        extracted_text = result["extracted_text"]
        ai_feedback = result["ai_feedback"]

        blob_url = upload_resume(file_bytes)

        resume_id = insert_resume(1, blob_url, 0.0)

        skills = extract_skills(extracted_text)
        insert_resume_skills(resume_id, skills)

        return func.HttpResponse(
            json.dumps({
                "resume_id": resume_id,
                "skills": skills,
                "ai_feedback": ai_feedback
            }),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logging.error(str(e))
        return func.HttpResponse("Internal server error", status_code=500)


# -------------------------
# RECOMMEND JOBS
# -------------------------
@app.function_name(name="recommendJobs")
@app.route(route="recommendJobs", methods=["GET"])
def recommend_jobs(req: func.HttpRequest) -> func.HttpResponse:

    resume_id = req.params.get("resume_id")

    if not resume_id:
        return func.HttpResponse(
            json.dumps({"error": "resume_id is required"}),
            status_code=400,
            mimetype="application/json"
        )

    recommendations = generate_recommendations(int(resume_id))

    return func.HttpResponse(
        json.dumps({
            "resume_id": resume_id,
            "recommendations": recommendations
        }),
        status_code=200,
        mimetype="application/json"
    )