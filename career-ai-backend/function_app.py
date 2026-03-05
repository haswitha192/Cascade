import azure.functions as func
import json
import logging
import os
import tempfile

from services.document_service import analyze_resume
from services.blob_service import upload_resume
from services.sql_service import insert_resume, insert_resume_skills
from services.skill_service import extract_skills
from services.career_optimization_service import generate_recommendations
from services.resume_skill_service import fetch_resume_skills
from services.score_service import compute_resume_score
from services.speech_service import transcribe_audio
from services.speech_analysis import calculate_wpm
from services.interview_ai import evaluate_answer, generate_interview_questions
from services.resume_skill_service import fetch_resume_skills


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}


def json_response(data: dict, status_code: int = 200) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps(data),
        status_code=status_code,
        mimetype="application/json",
        headers=CORS_HEADERS,
    )

app = func.FunctionApp()

MAX_FILE_SIZE_MB = 5


@app.function_name(name="processResume")
@app.route(route="processResume", methods=["POST"])
def process_resume(req: func.HttpRequest) -> func.HttpResponse:

    logging.info("Resume upload request received.")

    try:
        # -----------------------------
        # 1️⃣ Get File From FormData
        # -----------------------------
        file = req.files.get("file")

        if not file:
            return func.HttpResponse(
                json.dumps({"error": "No file provided"}),
                status_code=400,
                mimetype="application/json"
            )

        file_bytes = file.stream.read()

        # -----------------------------
        # 2️⃣ File Size Validation
        # -----------------------------
        file_size_mb = len(file_bytes) / (1024 * 1024)

        if file_size_mb > MAX_FILE_SIZE_MB:
            return func.HttpResponse(
                json.dumps({"error": "File exceeds 5MB limit"}),
                status_code=400,
                mimetype="application/json"
            )

        logging.info(f"File received: {file.filename}")
        logging.info(f"File size: {file_size_mb:.2f} MB")

        # -----------------------------
        # 3️⃣ Azure Document Intelligence
        # -----------------------------
        result = analyze_resume(file_bytes)

        extracted_text = result.get("extracted_text", "")
        ai_feedback = result.get("ai_feedback", "")

        logging.info(f"Extracted text length: {len(extracted_text)}")

        if not extracted_text:
            return func.HttpResponse(
                json.dumps({"error": "Resume extraction failed"}),
                status_code=500,
                mimetype="application/json"
            )

        # -----------------------------
        # 4️⃣ Upload to Blob (Correct Extension)
        # -----------------------------
        blob_url = upload_resume(file_bytes, file.filename)

        # -----------------------------
        # 5️⃣ Resume Scoring (Real algorithm)
        # -----------------------------
        resume_score = compute_resume_score(extracted_text)

        # -----------------------------
        # 6️⃣ Insert Into SQL
        # -----------------------------
        resume_id = insert_resume(
            user_id=1,
            blob_url=blob_url,
            extracted_text=extracted_text,
            resume_score=resume_score
        )

        # -----------------------------
        # 7️⃣ Skill Extraction
        # -----------------------------
        skills = extract_skills(extracted_text)
        insert_resume_skills(resume_id, skills)

        # -----------------------------
        # 8️⃣ Return JSON Response
        # -----------------------------
        return json_response({
            "success": True,
            "resume_id": resume_id,
            "resume_score": resume_score,
            "skills": skills,
            "ai_feedback": ai_feedback,
        })

    except Exception as e:
        logging.exception("Process Resume Failed")
        return json_response({"success": False, "error": str(e)}, 500)


# ─────────────────────────────────────────────
# 2. Recommend Jobs
# ─────────────────────────────────────────────
@app.function_name(name="recommendJobs")
@app.route(route="recommendJobs", methods=["GET", "OPTIONS"])
def recommend_jobs(req: func.HttpRequest) -> func.HttpResponse:

    # Handle CORS preflight
    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=204, headers=CORS_HEADERS)

    logging.info("recommendJobs request received.")

    resume_id_raw = req.params.get("resume_id")
    if not resume_id_raw:
        return json_response({"error": "resume_id query parameter is required."}, 400)

    try:
        resume_id = int(resume_id_raw)
    except ValueError:
        return json_response({"error": "resume_id must be an integer."}, 400)

    try:
        recommendations = generate_recommendations(resume_id)
        return json_response({"success": True, "recommendations": recommendations})

    except Exception as e:
        logging.exception("recommendJobs failed")
        return json_response({"success": False, "error": str(e)}, 500)


# ─────────────────────────────────────────────
# 3. Get Resume Skills (for Skills dashboard)
# ─────────────────────────────────────────────
@app.function_name(name="getResumeSkills")
@app.route(route="getResumeSkills", methods=["GET", "OPTIONS"])
def get_resume_skills(req: func.HttpRequest) -> func.HttpResponse:

    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=204, headers=CORS_HEADERS)

    logging.info("getResumeSkills request received.")

    resume_id_raw = req.params.get("resume_id")
    if not resume_id_raw:
        return json_response({"error": "resume_id query parameter is required."}, 400)

    try:
        resume_id = int(resume_id_raw)
    except ValueError:
        return json_response({"error": "resume_id must be an integer."}, 400)

    try:
        skills = fetch_resume_skills(resume_id)
        return json_response({"success": True, "skills": skills})

    except Exception as e:
        logging.exception("getResumeSkills failed")
        return json_response({"success": False, "error": str(e)}, 500)
    
# ─────────────────────────────────────────────
# 4. Start Interview
# ─────────────────────────────────────────────
@app.function_name(name="startInterview")
@app.route(route="startInterview", methods=["POST", "OPTIONS"])
def start_interview(req: func.HttpRequest) -> func.HttpResponse:

    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=204, headers=CORS_HEADERS)

    logging.info("startInterview request received.")

    fallback_questions = [
        "Tell me about yourself and your professional background.",
        "What are your strongest technical skills?",
        "Describe a difficult problem you solved at work.",
        "Why are you interested in this role?",
        "Where do you see yourself in five years?"
    ]

    try:
        try:
            body = req.get_json() or {}
        except Exception:
            body = {}
        resume_id_raw = body.get("resume_id") or req.params.get("resume_id")

        if not resume_id_raw:
            logging.info("No resume_id provided — returning fallback questions.")
            return json_response({"success": True, "questions": fallback_questions})

        resume_id = int(resume_id_raw)

        # ── Fetch resume text from SQL ──────────────────────────────
        from services.sql_service import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT extracted_text FROM Resumes WHERE resume_id = ?",
            resume_id
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if not row or not row[0]:
            logging.warning(f"No resume text found for resume_id={resume_id}")
            return json_response({"success": True, "questions": fallback_questions})

        resume_text = row[0]

        # ── Fetch extracted skills ──────────────────────────────────
        skills = fetch_resume_skills(resume_id)

        # ── Generate personalised questions with Groq LLM ───────────
        questions = generate_interview_questions(resume_text, skills)

        logging.info(f"Generated {len(questions)} personalised questions for resume_id={resume_id}")

        return json_response({"success": True, "questions": questions})

    except Exception as e:
        logging.exception("startInterview failed — returning fallback questions")
        return json_response({"success": True, "questions": fallback_questions})

# ─────────────────────────────────────────────
# 5. Submit Audio Answer
# ─────────────────────────────────────────────
@app.function_name(name="submitAudioAnswer")
@app.route(route="submitAudioAnswer", methods=["POST", "OPTIONS"])
def submit_audio_answer(req: func.HttpRequest) -> func.HttpResponse:

    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=204, headers=CORS_HEADERS)

    logging.info("submitAudioAnswer request received.")

    try:

        file = req.files.get("audio")
        question = req.form.get("question")

        if not file:
            return json_response({"error": "No audio file provided"}, 400)

        if not question:
            return json_response({"error": "Question missing"}, 400)

        # Save temporary audio file — browsers record WebM/Opus, not WAV
        webm_path = os.path.join(tempfile.gettempdir(), "interview_answer.webm")
        wav_path = os.path.join(tempfile.gettempdir(), "interview_answer.wav")

        with open(webm_path, "wb") as f:
            f.write(file.stream.read())

        # ─────────────────────────
        # Convert WebM to true PCM WAV
        # ─────────────────────────
        try:
            from pydub import AudioSegment
            import pydub.utils
            
            # Winget installs ffmpeg here for the Administrator account
            ffmpeg_path = r"C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0.1-full_build\bin\ffmpeg.exe"
            ffprobe_path = r"C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0.1-full_build\bin\ffprobe.exe"
            
            AudioSegment.converter = ffmpeg_path
            AudioSegment.ffmpeg = ffmpeg_path
            pydub.utils.get_prober_name = lambda: ffprobe_path
            
            audio_segment = AudioSegment.from_file(webm_path, format="webm")
            # Export as true PCM WAV
            audio_segment.export(wav_path, format="wav")
            logging.info("Successfully transcoded WebM to WAV using pydub/ffmpeg")
        except Exception as e:
            logging.error(f"Failed to transcode audio with pydub: {e}")
            # Fallback to the webm path if transcode fails (though Speech SDK will reject it)
            wav_path = webm_path

        # ─────────────────────────
        # Speech → Text
        # ─────────────────────────
        transcript = transcribe_audio(wav_path)

        logging.info(f"Transcript: {transcript}")

        # ─────────────────────────
        # Speaking Speed
        # ─────────────────────────
        duration_seconds = 10  # placeholder for now
        speaking_speed = calculate_wpm(transcript, duration_seconds)

        # ─────────────────────────
        # AI Interview Evaluation
        # ─────────────────────────
        evaluation = evaluate_answer(question, transcript)

        result = {
            "success": True,
            "transcript": transcript,
            "speaking_speed": speaking_speed,
            "technical_score": evaluation["technical_score"],
            "communication_score": evaluation["communication_score"],
            "confidence_score": evaluation["confidence_score"],
            "overall_score": evaluation["overall_score"],
            "feedback": evaluation["feedback"]
        }

        return json_response(result)

    except Exception as e:
        logging.exception("submitAudioAnswer failed")
        return json_response({"success": False, "error": str(e)}, 500)


# ─────────────────────────────────────────────
# 6. Analyze Video Frame
# ─────────────────────────────────────────────
@app.function_name(name="analyzeVideoFrame")
@app.route(route="analyzeVideoFrame", methods=["POST", "OPTIONS"])
def analyze_video_frame(req: func.HttpRequest) -> func.HttpResponse:

    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=204, headers=CORS_HEADERS)

    logging.info("analyzeVideoFrame request received.")

    try:

        file = req.files.get("frame")

        if not file:
            return json_response({"error": "No frame image provided"}, 400)

        image_bytes = file.stream.read()

        from services.video_analysis_service import analyze_face

        result = analyze_face(image_bytes)

        return json_response({
            "success": True,
            "confidence_score": result["confidence_score"],
            "eye_contact": result["eye_contact"],
            "emotion": result["emotion"]
        })

    except Exception as e:
        logging.exception("analyzeVideoFrame failed")
        return json_response({"success": False, "error": str(e)}, 500)