import os
import requests

FACE_ENDPOINT = os.environ.get("FACE_ENDPOINT")
FACE_KEY = os.environ.get("FACE_KEY")


def analyze_face(image_bytes):

    url = f"{FACE_ENDPOINT}/face/v1.0/detect"

    params = {
        "returnFaceAttributes": "emotion,headPose"
    }

    headers = {
        "Ocp-Apim-Subscription-Key": FACE_KEY,
        "Content-Type": "application/octet-stream"
    }

    response = requests.post(
        url,
        params=params,
        headers=headers,
        data=image_bytes
    )

    faces = response.json()

    if not faces:
        return {
            "confidence_score": 0,
            "eye_contact": False,
            "emotion": "no_face"
        }

    face = faces[0]

    emotion = face["faceAttributes"]["emotion"]
    head_pose = face["faceAttributes"]["headPose"]

    dominant_emotion = max(emotion, key=emotion.get)

    # Simple confidence heuristic based on available Azure emotions
    confidence_score = (
        emotion.get("neutral", 0) * 0.5 +
        emotion.get("happiness", 0) * 0.3 +
        (1.0 - emotion.get("fear", 0)) * 0.1 +
        (1.0 - emotion.get("sadness", 0)) * 0.1
    ) * 100

    eye_contact = abs(head_pose["yaw"]) < 15

    return {
        "confidence_score": round(confidence_score, 2),
        "eye_contact": eye_contact,
        "emotion": dominant_emotion
    }