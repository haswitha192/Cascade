import os
import requests

FACE_ENDPOINT = os.environ.get("FACE_ENDPOINT")
FACE_KEY = os.environ.get("FACE_KEY")


def analyze_face(image_bytes):

    base_url = FACE_ENDPOINT.rstrip('/') if FACE_ENDPOINT else ""
    url = f"{base_url}/face/v1.0/detect"

    params = {
        "returnFaceId": "true",
        "returnFaceAttributes": "headPose"
    }

    headers = {
        "Ocp-Apim-Subscription-Key": FACE_KEY,
        "Content-Type": "application/octet-stream"
    }

    import logging
    logging.info(f"Calling Face API at: {url}")

    try:
        response = requests.post(
            url,
            params=params,
            headers=headers,
            data=image_bytes,
            timeout=20
        )
        logging.info(f"Face API Response Status: {response.status_code}")
        if response.status_code != 200:
            logging.error(f"Face API Error Response: {response.text}")
    except Exception as e:
        logging.error(f"Face API Request failed: {e}")
        return {"confidence_score": 0, "eye_contact": False, "emotion": "connection_error"}

    try:
        faces = response.json()
    except ValueError:
        return {"confidence_score": 0, "eye_contact": False, "emotion": "api_error"}

    # If the API returned an error (dict with "error" key)
    if isinstance(faces, dict) and "error" in faces:
        print(f"Face API Error: {faces['error']}")
        return {"confidence_score": 0, "eye_contact": False, "emotion": "api_error"}

    # Ensure it's a list and has at least one face
    if not isinstance(faces, list) or len(faces) == 0:
        print(f"[DEBUG] Face API returned no faces or invalid list format. Response: {faces}, Status: {response.status_code}")
        return {
            "confidence_score": 0,
            "eye_contact": False,
            "emotion": "no_face"
        }

    face = faces[0]

    head_pose = face["faceAttributes"]["headPose"]

    # Azure retired the "emotion" attribute. We'll use a static "neutral" 
    # and base the confidence solely on the user making good eye contact (yaw and pitch close to 0).
    yaw, pitch = abs(head_pose["yaw"]), abs(head_pose["pitch"])
    
    # Good eye contact means looking straight at the camera (low yaw/pitch)
    eye_contact = yaw < 15 and pitch < 15
    
    # Simple confidence heuristic based on head pose
    if eye_contact:
        confidence_score = 95.0 - (yaw + pitch)
    else:
        confidence_score = max(50.0, 95.0 - (yaw * 1.5 + pitch * 1.5))

    return {
        "confidence_score": round(confidence_score, 2),
        "eye_contact": eye_contact,
        "emotion": "focused"
    }